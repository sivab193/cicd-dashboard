"""Normalize only the five V1 scanner formats. Scanner execution stays in CI."""
from uuid import uuid4

def normalize(scanner, payload, project, deployment):
    findings=[]
    def add(severity,package='',file='',rule='',installed='',fixed='',category='dependency',description=''):
        findings.append(dict(id=uuid4().hex,project=project,deployment=deployment,scanner=scanner,severity=severity.lower(),package=package,file=file,rule=rule,installed_version=installed,fixed_version=fixed,category=category,status='open',description=description))
    if scanner=='trivy':
        for result in payload.get('Results',[]):
            for v in result.get('Vulnerabilities') or []: add(v.get('Severity','unknown'),v.get('PkgName',''),result.get('Target',''),v.get('VulnerabilityID',''),v.get('InstalledVersion',''),v.get('FixedVersion',''),description=v.get('Title',''))
            for v in result.get('Misconfigurations') or []: add(v.get('Severity','unknown'),file=result.get('Target',''),rule=v.get('ID',''),category='iac',description=v.get('Title',''))
    elif scanner=='semgrep':
        for v in payload.get('results',[]):
            extra=v.get('extra',{}); sev=extra.get('metadata',{}).get('severity') or {'ERROR':'high','WARNING':'medium','INFO':'low'}.get(extra.get('severity'),'medium')
            add(sev,file=v.get('path',''),rule=v.get('check_id',''),category='sast',description=extra.get('message',''))
    elif scanner=='gitleaks':
        for v in payload: add('critical',file=v.get('File',''),rule=v.get('RuleID',''),category='secret',description='Secret detected; value redacted.')
    elif scanner=='osv-scanner':
        for result in payload.get('results',[]):
            for package in result.get('packages',[]):
                for v in package.get('vulnerabilities',[]):
                    sev=v.get('database_specific',{}).get('severity','unknown')
                    add(sev,package.get('package',{}).get('name',''),result.get('source',{}).get('path',''),v.get('id',''),package.get('package',{}).get('version',''),description=v.get('summary',''))
    else: raise ValueError('Unsupported scanner')
    return findings

def gate(findings, policy):
    return [f for f in findings if f['status']=='open' and ((f['category']=='secret' and policy.get('block_secrets',True)) or (f['severity']=='critical' and policy.get('block_critical',True)))]
