from datetime import datetime, timezone, timedelta
from .db import Session, Record

def seed():
    with Session() as db:
        if db.query(Record).first(): return
        now = datetime.now(timezone.utc)
        projects = [
          ('mediaverse','MediaVerse','Your movies. Everywhere.','Vercel','healthy','#a89bff','Next.js','media-verse.in'),
          ('aayvu-web','Aayvu Web','Research, beautifully connected.','Vercel','healthy','#75d8ff','React','aayvu.siv19.dev'),
          ('splitllm-api','SplitLLM API','Shared intelligence, simplified.','GitHub Actions','healthy','#ffbb7b','Python','api.splitllm.in'),
          ('journeyalert','JourneyAlert','Never miss your destination.','Docker Compose','down','#ff8298','Node.js','journey.siv19.dev'),
          ('collegecal','CollegeCal','A little order for campus life.','Vercel','degraded','#f5d87d','React','cal.siv19.dev'),
          ('aayvu-worker','Aayvu Worker','Background research processing.','Docker Compose','healthy','#74dac2','Python','worker.siv19.dev')]
        def add(kind,id,**data): db.add(Record(id=id,kind=kind,data={'id':id,**data}))
        for i,(id,name,description,provider,status,color,stack,url) in enumerate(projects):
            repo = 'aayvu/aayvu' if id.startswith('aayvu') else f'sample/{id}'
            add('project',id,name=name,description=description,provider=provider,status=status,color=color,stack=stack,url='https://'+url,branch='main',repositories=[repo],environment='production',environments=['development','preview','staging','production'],public=False,auto_rollback=False,security_policy={'block_critical':True,'block_secrets':True},provider_config={})
            if not db.get(Record,repo):
                db.flush()
                if not db.get(Record,repo): add('repository',repo,name=repo,state='managed',stack=stack,archived=False,fork=False,branch='main',installation_id=None)
            for j in range(3):
                did=f'deploy-{i}-{j}'
                status_d='failed' if i in [3,4] and j==0 else 'healthy'
                add('deployment',did,project=id,project_name=name,environment='production',commit=['fa41921','2ab883c','d941cc8'][j],branch='main',provider=provider,status=status_d,source='push',actor='Sivaganesh',started_at=(now-timedelta(minutes=12+i*23+j*120)).isoformat(),duration=112+i*13,previous_deployment=f'deploy-{i}-{j+1}' if j<2 else None,logs=['Sample workspace: historical deployment record.','Build completed.','Security scan completed.','Verification '+('failed: timeout' if status_d=='failed' else 'passed.')],steps={'build':'passed','security':'passed','deploy':'passed','verification':'failed' if status_d=='failed' else 'passed'})
            for j,check in enumerate(['Website','API']):
                add('health_check',f'check-{i}-{j}',project=id,name=check,url='https://'+url+('/api/health' if j else ''),status=status,latency=89+i*19+j*12,required=True,interval=60,public=False,history=[{'status':status if k>26 else 'healthy','latency':80+(k*17+i*29)%100,'time':(now-timedelta(minutes=(29-k)*60)).isoformat()} for k in range(30)])
        for i,(project,severity,package,scanner) in enumerate([('journeyalert','critical','express','trivy'),('aayvu-web','high','next','osv-scanner'),('mediaverse','high','axios','trivy'),('collegecal','medium','vite','osv-scanner'),('splitllm-api','medium','requests','trivy'),('aayvu-worker','low','urllib3','osv-scanner'),('mediaverse','medium','cookie','trivy'),('journeyalert','high','jsonwebtoken','semgrep')]):
            add('finding',f'finding-{i}',project=project,severity=severity,package=package,scanner=scanner,category='sast' if scanner=='semgrep' else 'dependency',file='package-lock.json' if package!='requests' else 'requirements.txt',rule=f'SAMPLE-{1000+i}',installed_version='1.0.0',fixed_version='1.0.1',status='open',first_seen=now.isoformat(),last_seen=now.isoformat(),deployment=f'deploy-{i%6}-0',description='Sample finding for exploring the security workflow. Connect scanners for real results.')
        for id,name,cpu,ram,disk,status in [('omv','OMV Server',12,34,61,'online'),('rog','ASUS ROG',0,0,0,'offline')]:
            add('host',id,name=name,cpu=cpu,ram=ram,disk=disk,status=status,version='1.0.0',last_seen=now.isoformat(),capabilities=['docker','health','deploy','metrics'])
        for i,name in enumerate(['Jellyfin','Vaultwarden','Immich','PostgreSQL','Redis']): add('service',f'svc-{i}',name=name,host='omv',status='healthy',image=f'{name.lower()}:stable',port=[8096,8080,2283,5432,6379][i])
        for i,(title,kind) in enumerate([('MediaVerse deployed successfully','deployment'),('JourneyAlert health check failed','health'),('Aayvu Web: high vulnerability detected','security'),('GitHub repositories synchronized','repository'),('Jellyfin restarted','infrastructure')]): add('activity',f'event-{i}',title=title,type=kind,actor='Sivaganesh',time=(now-timedelta(minutes=12+i*18)).isoformat())
        add('settings','settings',workspace='Sivaganesh',ignore_archived=True,ignore_forks=True,ignore_patterns='assignment-*\nlab-*\ntest-*\narchive-*',notification_email='',telegram_chat_id='',notify_success=False,log_retention_days=7)
        db.commit()
