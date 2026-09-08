import os, json, secrets, hashlib, hmac, fnmatch
from datetime import datetime, timezone
from uuid import uuid4
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel, Field
from cryptography.fernet import Fernet
import httpx
from .db import Session, Record, Secret
from .seed import seed
from .providers import PROVIDERS, ProviderError, discover, installation_token, request as provider_request
from .security import normalize, gate
from .health import probe

DEMO=os.getenv('DEMO_MODE','true').lower()=='true'
SESSION_KEY=os.getenv('SESSION_SECRET') or (secrets.token_urlsafe(48) if DEMO else '')
if not SESSION_KEY: raise RuntimeError('SESSION_SECRET is required outside demo mode')
@asynccontextmanager
async def lifespan(app):
    if DEMO: seed()
    yield
app=FastAPI(title='CI/CD Control Plane',lifespan=lifespan)
app.add_middleware(SessionMiddleware,secret_key=SESSION_KEY,https_only=not DEMO,same_site='lax')
def now(): return datetime.now(timezone.utc).isoformat()
def records(kind):
    with Session() as db: return [r.data for r in db.query(Record).filter_by(kind=kind).order_by(Record.created_at.desc()).all()]
def get(id,kind=None):
    with Session() as db:
        r=db.get(Record,id)
        if not r or (kind and r.kind!=kind): raise HTTPException(404,'Not found')
        return r.data

def put(kind,data):
    with Session() as db:
        r=db.get(Record,data['id'])
        if r: r.data=data
        else: db.add(Record(id=data['id'],kind=kind,data=data))
        db.commit()
    return data

def audit(title,type='configuration',actor='system'):
    put('activity',{'id':uuid4().hex,'title':title,'type':type,'actor':actor,'time':now()})
async def user(req:Request):
    if DEMO: return {'login':'Sivaganesh','role':'owner','demo':True}
    value=req.session.get('user')
    if not value: raise HTTPException(401,'Sign in with GitHub')
    return value
async def writer(req:Request,u=Depends(user)):
    if u['role'] not in ('owner','admin','developer'): raise HTTPException(403,'Read-only role')
    if req.method not in ('GET','HEAD'):
        origin=req.headers.get('origin')
        expected=os.getenv('APP_URL','http://127.0.0.1:5173').rstrip('/')
        if origin and origin!=expected: raise HTTPException(403,'Origin rejected')
    return u
async def admin(u=Depends(writer)):
    if u['role'] not in ('owner','admin'): raise HTTPException(403,'Administrator required')
    return u
class ProjectInput(BaseModel):
    name:str=Field(min_length=1,max_length=80)
    description:str=''
    repositories:list[str]=[]
    provider:str='Vercel'
    branch:str='main'
    url:str=''
    environment:str='production'
class DeployInput(BaseModel):
    action:str='deploy'
    environment:str='production'
    target:str|None=None
class SecretInput(BaseModel):
    name:str=Field(pattern=r'^[A-Z][A-Z0-9_]{0,99}$')
    value:str=Field(min_length=1,max_length=65536)
    environment:str='production'

@app.get('/api/session')
async def session(req:Request):
    return {'user':await user(req) if DEMO or req.session.get('user') else None,'demo':DEMO,'github_configured':bool(os.getenv('GITHUB_CLIENT_ID'))}
@app.get('/api/auth/github')
async def login(req:Request):
    if not os.getenv('GITHUB_CLIENT_ID'): raise HTTPException(503,'Configure GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET on the backend.')
    state=secrets.token_urlsafe(32); req.session['oauth_state']=state
    return RedirectResponse('https://github.com/login/oauth/authorize?client_id='+os.environ['GITHUB_CLIENT_ID']+'&state='+state+'&scope=read:user')
@app.get('/api/auth/callback')
async def callback(req:Request,code:str,state:str):
    saved=req.session.pop('oauth_state',None)
    if not saved or not secrets.compare_digest(saved,state): raise HTTPException(400,'Invalid OAuth state')
    async with httpx.AsyncClient(timeout=20) as client:
        result=await client.post('https://github.com/login/oauth/access_token',json={'client_id':os.environ['GITHUB_CLIENT_ID'],'client_secret':os.environ['GITHUB_CLIENT_SECRET'],'code':code},headers={'Accept':'application/json'})
        token=result.json().get('access_token')
        if not token: raise HTTPException(401,'OAuth exchange failed')
        result=await client.get('https://api.github.com/user',headers={'Authorization':f'Bearer {token}'})
        profile=result.json()
    roles=json.loads(os.getenv('GITHUB_ALLOWED_USERS','{}'))
    role=roles.get(profile.get('login'))
    if role not in ('owner','admin','developer','viewer'): raise HTTPException(403,'This account is not authorized for this private workspace.')
    req.session.clear(); req.session['user']={'login':profile['login'],'role':role,'avatar':profile.get('avatar_url')}
    audit('Signed in with GitHub','authentication',profile['login'])
    return RedirectResponse(os.getenv('APP_URL','http://127.0.0.1:5173'))
@app.post('/api/auth/logout')
async def logout(req:Request,u=Depends(writer)):
    req.session.clear(); return {'ok':True}
@app.get('/api/dashboard')
async def dashboard(u=Depends(user)):
    return {kind:records(kind) for kind in ['project','repository','deployment','finding','health_check','host','service','activity','incident'] } | {'demo':DEMO,'user':u}
@app.post('/api/projects')
async def create_project(body:ProjectInput,u=Depends(writer)):
    if body.provider not in PROVIDERS: raise HTTPException(400,'Unknown provider')
    if body.environment not in ('development','preview','staging','production'): raise HTTPException(400,'Invalid environment')
    for repo in body.repositories:
        if get(repo,'repository')['state']!='managed': raise HTTPException(400,'Manage repositories before creating a project')
    data=put('project',{'id':uuid4().hex,**body.model_dump(),'status':'unknown','color':'#8fffc2','stack':'Unknown','environments':['development','preview','staging','production'],'public':False,'auto_rollback':False,'provider_config':{},'security_policy':{'block_critical':True,'block_secrets':True}})
    audit(f'{body.name} project created','project',u['login']); return data
@app.patch('/api/projects/{id}')
async def update_project(id:str,body:dict,u=Depends(admin)):
    p=get(id,'project'); allowed={'name','description','branch','url','public','public_name','public_description','auto_rollback','provider_config','security_policy'}
    p.update({k:v for k,v in body.items() if k in allowed}); put('project',p); audit(f'{p["name"]} settings updated',actor=u['login']); return p
@app.post('/api/repositories/discover')
async def discover_repos(u=Depends(admin)):
    if DEMO:
        data=[{'id':'sample/new-project','name':'sample/new-project','state':'unreviewed','stack':'TypeScript','branch':'main','archived':False,'fork':False},{'id':'sample/lab-experiment','name':'sample/lab-experiment','state':'unreviewed','stack':'Python','branch':'main','archived':False,'fork':False}]
    else:
        try: data=await discover()
        except ProviderError as e: raise HTTPException(503,str(e))
    current={r['id']:r for r in records('repository')}; settings=records('settings'); cfg=settings[0] if settings else {}
    for repo in data:
        if repo['id'] in current: repo['state']=current[repo['id']]['state']
        elif (cfg.get('ignore_archived',True) and repo['archived']) or (cfg.get('ignore_forks',True) and repo['fork']) or any(fnmatch.fnmatch(repo['name'].split('/')[-1],p.strip()) for p in cfg.get('ignore_patterns','').splitlines() if p.strip()): repo['state']='ignored'
        put('repository',repo)
    audit(f'Discovered {len(data)} repositories','repository',u['login']); return records('repository')
@app.patch('/api/repositories/state')
async def repo_state(body:dict,u=Depends(writer)):
    if body.get('state') not in ('managed','ignored','unreviewed'): raise HTTPException(400,'Invalid state')
    r=get(body['id'],'repository'); r['state']=body['state']; put('repository',r); audit(f'{r["name"]} marked {r["state"]}','repository',u['login']); return r
@app.post('/api/repositories/inspect')
async def inspect_repo(body:dict,u=Depends(user)):
    r=get(body['id'],'repository')
    if DEMO: return {'stack':[r['stack']],'recommendations':['HTTP availability check','Lint → tests → security → build → deploy'],'provider':'Vercel' if r['stack'] in ('React','Next.js','TypeScript') else 'GitHub Actions'}
    try:
        token=await installation_token(r.get('installation_id'))
        files=await provider_request('GET',f'https://api.github.com/repos/{r["name"]}/contents',token)
        names=[f['name'] for f in files]; stack=[]
        for pattern,label in [('package.json','Node.js'),('next.config.*','Next.js'),('vite.config.*','Vite'),('requirements.txt','Python'),('pyproject.toml','Python'),('Dockerfile','Docker'),('*compose*yml','Docker Compose'),('vercel.json','Vercel')]:
            if any(fnmatch.fnmatch(n,pattern) for n in names): stack.append(label)
        return {'stack':stack,'recommendations':['Add an HTTP health check','Use the supplied security workflow template'],'provider':'Vercel' if 'Vercel' in stack or 'Next.js' in stack else 'GitHub Actions'}
    except ProviderError as e: raise HTTPException(503,str(e))
@app.post('/api/projects/{id}/deployments')
async def deployment(id:str,body:DeployInput,u=Depends(writer)):
    p=get(id,'project'); provider=PROVIDERS[p['provider']]
    if body.action not in provider.capabilities: raise HTTPException(400,'This provider does not support this action')
    if body.environment not in p['environments']: raise HTTPException(400,'Unknown environment')
    findings=[f for f in records('finding') if f['project']==id]
    if body.action not in ('stop','cancel') and gate(findings,p['security_policy']): raise HTTPException(409,'Security gate blocked this action: resolve or acknowledge blocking findings first.')
    history=[d for d in records('deployment') if d['project']==id and d['environment']==body.environment]
    target=get(body.target,'deployment') if body.target else None
    if body.action=='rollback' and not target: raise HTTPException(400,'Choose a rollback target')
    if target and (target['project']!=id or target['environment']!=body.environment or target['status']!='healthy'): raise HTTPException(400,'Rollback target must be a healthy deployment in the same project/environment')
    d={'id':uuid4().hex,'project':id,'project_name':p['name'],'environment':body.environment,'provider':p['provider'],'branch':p['branch'],'commit':target['commit'] if target else p['branch'],'source':body.action,'actor':u['login'],'status':'queued','started_at':now(),'duration':0,'previous_deployment':history[0]['id'] if history else None,'rollback_target':body.target,'target_external_id':target.get('external_id') if target else (history[0].get('external_id') if history else None),'steps':{'build':'pending','security':'passed','deploy':'pending','verification':'pending'},'logs':[]}
    if DEMO: d['logs']=['Sample mode: action recorded. No external deployment was triggered.']; d['status']='queued'
    else:
        try: d.update(await provider.execute(body.action,p,d))
        except ProviderError as e: raise HTTPException(503,str(e))
    put('deployment',d)
    if d.get('agent_task'):
        put('agent_task',{'id':uuid4().hex,**d['agent_task'],'deployment':d['id'],'status':'queued'})
    audit(f'{p["name"]}: {body.action} queued','deployment',u['login']); return d
@app.get('/api/projects/{id}/builds')
async def builds(id:str,u=Depends(user)):
    p=get(id,'project')
    if DEMO: return {'workflow_runs':[d for d in records('deployment') if d['project']==id]}
    try: return await PROVIDERS['GitHub Actions'].builds(p)
    except ProviderError as e: raise HTTPException(503,str(e))
@app.post('/api/deployments/{id}/verify')
async def verify(id:str,u=Depends(writer)):
    d=get(id,'deployment'); checks=[c for c in records('health_check') if c['project']==d['project'] and c.get('required')]
    if d['status'] not in ('verifying','failed'): raise HTTPException(409,'Provider must complete deployment before verification')
    if not checks: raise HTTPException(409,'At least one required health check is needed')
    results=[await run_check(c['id'],u) for c in checks]
    d['status']='healthy' if all(r['status']=='healthy' for r in results) else 'failed'; d['steps']['verification']='passed' if d['status']=='healthy' else 'failed'; d['ended_at']=now(); put('deployment',d); audit(f'{d["project_name"]}: verification {d["status"]}','health',u['login']); return d
@app.patch('/api/findings/{id}')
async def finding_state(id:str,body:dict,u=Depends(writer)):
    if body.get('status') not in ('open','acknowledged','ignored','fixed','false_positive'): raise HTTPException(400,'Invalid finding status')
    f=get(id,'finding'); f['status']=body['status']; put('finding',f); audit(f'{f["rule"]}: {f["status"]}','security',u['login']); return f
@app.post('/api/security/import')
async def import_scan(body:dict,u=Depends(writer)):
    p=get(body['project'],'project'); d=get(body['deployment'],'deployment')
    if d['project']!=p['id']: raise HTTPException(400,'Deployment does not belong to project')
    if body['scanner']=='syft':
        payload=body['payload']
        if payload.get('bomFormat')!='CycloneDX': raise HTTPException(400,'CycloneDX format required')
        return put('sbom',{'id':d['id']+'-sbom','project':p['id'],'deployment':d['id'],'commit':d['commit'],'time':now(),'payload':payload})
    try: data=normalize(body['scanner'],body['payload'],p['id'],d['id'])
    except ValueError as e: raise HTTPException(400,str(e))
    for f in data: f.update(first_seen=now(),last_seen=now()); put('finding',f)
    audit(f'{p["name"]}: imported {len(data)} findings','security',u['login']); return {'count':len(data)}
@app.get('/api/deployments/{id}/sbom')
async def sbom(id:str,u=Depends(user)): return get(id+'-sbom','sbom')['payload']
@app.post('/api/health/checks')
async def create_check(body:dict,u=Depends(writer)):
    get(body['project'],'project')
    if not str(body.get('url','')).startswith(('https://','http://')): raise HTTPException(400,'HTTP(S) URL required')
    return put('health_check',{'id':uuid4().hex,'project':body['project'],'name':str(body.get('name','HTTP'))[:100],'url':body['url'],'status':'unknown','latency':0,'history':[],'required':True,'interval':60,'public':False})
@app.post('/api/health/checks/{id}/run')
async def run_check(id:str,u=Depends(writer)):
    c=get(id,'health_check')
    if DEMO: result={'status':c['status'],'latency':c['latency'],'sample':True}
    else:
        try: result=await probe(c['url'])
        except (ValueError,OSError) as e: raise HTTPException(400,str(e))
    old=c['status']; c.update(result); c['history']=(c['history']+[dict(result,time=now())])[-43200:]; c['last_checked']=now(); put('health_check',c)
    p=get(c['project'],'project'); checks=[v for v in records('health_check') if v['project']==p['id']]; p['status']='healthy' if all(v['status']=='healthy' for v in checks) else 'down' if all(v['status']=='down' for v in checks) else 'degraded'; put('project',p)
    if old!=c['status']:
        audit(f'{p["name"]}: {c["name"]} is {c["status"]}','health')
        if c['status']=='down': put('incident',{'id':uuid4().hex,'project':p['id'],'check':id,'started_at':now(),'ended_at':None,'title':f'{c["name"]} unavailable'})
        elif c['status']=='healthy':
            for i in records('incident'):
                if i['check']==id and not i['ended_at']: i['ended_at']=now(); put('incident',i)
    return c
@app.get('/api/public/status')
async def public_status():
    return {'updated_at':now(),'projects':[{'name':p.get('public_name') or p['name'],'description':p.get('public_description',''),'status':p['status'],'incidents':[{'started_at':i['started_at'],'ended_at':i['ended_at']} for i in records('incident') if i['project']==p['id']]} for p in records('project') if p.get('public')]}
@app.get('/api/settings')
async def settings(u=Depends(admin)):
    data=records('settings'); return (data[0] if data else {'id':'settings','workspace':'My workspace'}) | {'integrations':{'GitHub App':bool(os.getenv('GITHUB_APP_ID')),'GitHub OAuth':bool(os.getenv('GITHUB_CLIENT_ID')),'Vercel':bool(os.getenv('VERCEL_TOKEN')),'Email':bool(os.getenv('SMTP_HOST')),'Telegram':bool(os.getenv('TELEGRAM_BOT_TOKEN'))},'demo':DEMO}
@app.patch('/api/settings')
async def save_settings(body:dict,u=Depends(admin)):
    allowed={'workspace','ignore_archived','ignore_forks','ignore_patterns','notification_email','telegram_chat_id','notify_success','log_retention_days'}
    data=records('settings'); cfg=data[0] if data else {'id':'settings'}; cfg.update({k:v for k,v in body.items() if k in allowed}); put('settings',cfg); audit('Workspace settings updated',actor=u['login']); return cfg
@app.get('/api/projects/{id}/secrets')
async def list_secrets(id:str,u=Depends(admin)):
    with Session() as db: return [{'id':s.id,'name':s.name,'environment':s.environment} for s in db.query(Secret).filter_by(project=id).all()]
@app.post('/api/projects/{id}/secrets')
async def save_secret(id:str,body:SecretInput,u=Depends(admin)):
    get(id,'project'); key=os.getenv('MASTER_ENCRYPTION_KEY')
    if not key: raise HTTPException(503,'Set MASTER_ENCRYPTION_KEY on the server to enable encrypted secret storage.')
    sid=f'{id}:{body.environment}:{body.name}'
    with Session() as db:
        s=db.get(Secret,sid); ciphertext=Fernet(key.encode()).encrypt(body.value.encode()).decode()
        if s: s.ciphertext=ciphertext
        else: db.add(Secret(id=sid,project=id,environment=body.environment,name=body.name,ciphertext=ciphertext))
        db.commit()
    audit(f'{body.name} secret stored for {id}',actor=u['login']); return {'name':body.name,'environment':body.environment}
@app.delete('/api/projects/{id}/secrets/{name}')
async def delete_secret(id:str,name:str,environment:str='production',u=Depends(admin)):
    with Session() as db:
        s=db.get(Secret,f'{id}:{environment}:{name}')
        if not s: raise HTTPException(404,'Secret not found')
        db.delete(s); db.commit()
    audit(f'{name} secret deleted for {id}',actor=u['login']); return {'ok':True}
@app.post('/api/services/{id}/{action}')
async def service_action(id:str,action:str,u=Depends(admin)):
    if action not in ('restart','stop'): raise HTTPException(400,'Unsupported action')
    s=get(id,'service')
    if DEMO: s['status']='stopped' if action=='stop' else 'healthy'; put('service',s)
    else: put('agent_task',{'id':uuid4().hex,'agent_id':s['host'],'service':s['name'],'action':action,'status':'queued'})
    audit(f'{s["name"]}: {action} requested','infrastructure',u['login']); return s
@app.post('/api/webhooks/github')
async def webhook(req:Request):
    key=os.getenv('GITHUB_WEBHOOK_SECRET')
    if not key: raise HTTPException(503,'Webhook not configured')
    body=await req.body()
    expected='sha256='+hmac.new(key.encode(),body,hashlib.sha256).hexdigest()
    if not hmac.compare_digest(req.headers.get('x-hub-signature-256',''),expected): raise HTTPException(401,'Invalid signature')
    delivery=req.headers.get('x-github-delivery','')
    if not delivery: raise HTTPException(400,'Delivery ID required')
    with Session() as db:
        if db.get(Record,'hook-'+delivery): return {'duplicate':True}
    payload=json.loads(body); event=req.headers.get('x-github-event'); put('webhook',{'id':'hook-'+delivery,'event':event,'time':now()})
    if event=='workflow_run':
        run=payload['workflow_run']; repo=payload['repository']['full_name']
        for p in records('project'):
            if repo not in p['repositories']: continue
            existing=next((d for d in records('deployment') if d['project']==p['id'] and (d.get('external_id')==str(run['id']) or (d['status']=='queued' and d['branch']==run['head_branch']))),None)
            d=existing or {'id':uuid4().hex,'project':p['id'],'project_name':p['name'],'environment':'production','provider':'GitHub Actions','source':'push','actor':run['actor']['login'],'started_at':run['created_at'],'duration':0,'logs':[],'steps':{}}
            d.update(external_id=str(run['id']),commit=run['head_sha'],branch=run['head_branch'],status='verifying' if run.get('conclusion')=='success' else 'failed' if run.get('conclusion') in ('failure','timed_out') else 'cancelled' if run.get('conclusion')=='cancelled' else 'building')
            put('deployment',d)
    audit(f'GitHub {event} received','repository'); return {'ok':True}

@app.post('/api/agents/register')
async def register_agent(body:dict,u=Depends(admin)):
    name=str(body.get('name','')).strip()
    if not name or len(name)>80: raise HTTPException(400,'Host name required, maximum 80 characters')
    token=secrets.token_urlsafe(40);id=uuid4().hex
    put('agent',{'id':id,'name':name,'token_hash':hashlib.sha256(token.encode()).hexdigest(),'capabilities':['docker','metrics','deploy'],'version':'1.0.0'})
    put('host',{'id':id,'name':name,'status':'offline','cpu':0,'ram':0,'disk':0,'version':'1.0.0','last_seen':now(),'capabilities':['docker','metrics','deploy']})
    audit(f'{name}: agent registered','infrastructure',u['login']);return {'id':id,'token':token,'message':'Store this token on the host. It is shown only once.'}
async def agent_identity(req:Request):
    id=req.headers.get('x-agent-id','');authorization=req.headers.get('authorization','')
    if not authorization.startswith('Bearer '): raise HTTPException(401,'Agent token required')
    try: a=get(id,'agent')
    except HTTPException: raise HTTPException(401,'Unknown agent')
    if not secrets.compare_digest(a['token_hash'],hashlib.sha256(authorization[7:].encode()).hexdigest()): raise HTTPException(401,'Invalid agent token')
    return a
@app.post('/api/agent/heartbeat')
async def heartbeat(body:dict,a=Depends(agent_identity)):
    h=get(a['id'],'host');h.update(status='online',last_seen=now(),version=str(body.get('version','unknown'))[:50])
    for metric in ['cpu','ram','disk']:
        try: h[metric]=max(0,min(100,float(body.get(metric,0))))
        except (TypeError,ValueError): raise HTTPException(400,'Invalid metric')
    put('host',h)
    for service in body.get('services',[])[:100]:
        name=str(service.get('name',''))[:100]
        put('service',{'id':a['id']+':'+name,'host':a['id'],'name':name,'status':service.get('status','unknown'),'image':str(service.get('image',''))[:200],'port':service.get('port','')})
    return {'ok':True}
@app.get('/api/agent/tasks')
async def agent_tasks(a=Depends(agent_identity)):
    tasks=[]
    with Session() as db:
        rows=db.query(Record).filter_by(kind='agent_task').with_for_update().all()
        for r in rows:
            d=r.data
            claimed=d.get('claimed_at')
            lease_expired=d.get('status')=='running' and claimed and (datetime.now(timezone.utc)-datetime.fromisoformat(claimed)).total_seconds()>600
            if d.get('agent_id')==a['id'] and (d.get('status')=='queued' or lease_expired):
                d=dict(d,status='running',claimed_at=now());r.data=d;tasks.append(d)
                if len(tasks)>=5: break
        db.commit()
    return tasks
@app.post('/api/agent/tasks/{id}/result')
async def task_result(id:str,body:dict,a=Depends(agent_identity)):
    t=get(id,'agent_task')
    if t['agent_id']!=a['id'] or t['status']!='running': raise HTTPException(409,'Task is not assigned to this agent or already completed')
    t['status']='completed' if body.get('success') is True else 'failed';t['ended_at']=now()
    # Arbitrary process output may contain secrets: only store bounded status messages.
    t['message']='Agent operation completed' if body.get('success') else 'Agent operation failed; inspect logs on host'
    put('agent_task',t)
    if t.get('deployment'):
        d=get(t['deployment'],'deployment');d['status']='verifying' if body.get('success') else 'failed';d['steps']['deploy']='passed' if body.get('success') else 'failed';d['logs']+= [t['message']];put('deployment',d)
    audit(f'{a["name"]}: {t["action"]} {t["status"]}','infrastructure',a['name']);return {'ok':True}
@app.get('/api/deployments/{id}/logs')
async def deployment_logs(id:str,u=Depends(user)):
    d=get(id,'deployment');return {'lines':d.get('logs',[])}
@app.get('/api/events')
async def events(req:Request,u=Depends(user)):
    import asyncio
    from fastapi.responses import StreamingResponse
    async def stream():
        previous=None
        while not await req.is_disconnected():
            latest=records('activity')[:1]; marker=latest[0]['id'] if latest else ''
            if marker!=previous: yield 'data: '+json.dumps({'type':'refresh','id':marker})+'\n\n';previous=marker
            else: yield ': keepalive\n\n'
            await asyncio.sleep(5)
    return StreamingResponse(stream(),media_type='text/event-stream',headers={'Cache-Control':'no-cache','X-Accel-Buffering':'no'})
