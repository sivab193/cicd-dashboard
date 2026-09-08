"""Provider adapters. Unsupported operations fail explicitly; no shell execution."""
import os, time, pathlib
from abc import ABC, abstractmethod
import httpx, jwt

class ProviderError(Exception): pass
class DeploymentProvider(ABC):
    capabilities: set[str] = set()
    @abstractmethod
    async def execute(self, action: str, project: dict, deployment: dict) -> dict: ...
    @abstractmethod
    async def status(self, project: dict, external_id: str) -> dict: ...

async def request(method, url, token, **kwargs):
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.request(method,url,headers={'Authorization':f'Bearer {token}','Accept':'application/json'},**kwargs)
        if response.is_error: raise ProviderError(f'Provider rejected request ({response.status_code})')
        return response.json() if response.content else {}

def app_jwt():
    key_path=os.getenv('GITHUB_APP_PRIVATE_KEY_PATH')
    if not key_path or not os.getenv('GITHUB_APP_ID'): raise ProviderError('Configure GitHub App ID and private key path on the server.')
    return jwt.encode({'iat':int(time.time())-60,'exp':int(time.time())+540,'iss':os.environ['GITHUB_APP_ID']},pathlib.Path(key_path).read_text(),algorithm='RS256')
async def installation_token(id):
    if not id: raise ProviderError('Repository has no GitHub App installation.')
    return (await request('POST',f'https://api.github.com/app/installations/{int(id)}/access_tokens',app_jwt()))['token']
async def discover():
    repos=[]
    page=1
    while True:
        installs=await request('GET',f'https://api.github.com/app/installations?per_page=100&page={page}',app_jwt())
        for installation in installs:
            token=await installation_token(installation['id']); p=1
            while True:
                data=await request('GET',f'https://api.github.com/installation/repositories?per_page=100&page={p}',token)
                for repo in data['repositories']:
                    repos.append({'id':repo['full_name'],'name':repo['full_name'],'state':'unreviewed','archived':repo['archived'],'fork':repo['fork'],'branch':repo['default_branch'],'installation_id':installation['id'],'updated_at':repo['updated_at'],'stack':repo.get('language') or 'Unknown','url':repo['html_url']})
                if len(data['repositories'])<100: break
                p+=1
        if len(installs)<100: break
        page+=1
    return repos

class GitHubActions(DeploymentProvider):
    capabilities={'deploy','redeploy','cancel'}
    async def execute(self,action,project,deployment):
        cfg=project.get('provider_config',{}); token=await installation_token(cfg.get('installation_id'))
        repo=project['repositories'][0]; root=f'https://api.github.com/repos/{repo}/actions'
        if action=='deploy':
            if not cfg.get('workflow'): raise ProviderError('Set a dispatchable workflow filename in project settings.')
            await request('POST',f'{root}/workflows/{cfg["workflow"]}/dispatches',token,json={'ref':deployment['branch']})
            return {'status':'queued','external_id':None,'message':'Workflow dispatched; webhook will report progress.'}
        run=cfg.get('run_id') or deployment.get('external_id')
        if not run: raise ProviderError('A workflow run ID is required.')
        await request('POST',f'{root}/runs/{int(run)}/'+('rerun' if action=='redeploy' else 'cancel'),token)
        return {'external_id':str(run),'status':'cancelled' if action=='cancel' else 'queued'}
    async def status(self,project,external_id):
        token=await installation_token(project['provider_config'].get('installation_id'))
        return await request('GET',f'https://api.github.com/repos/{project["repositories"][0]}/actions/runs/{int(external_id)}',token)
    async def builds(self,project):
        token=await installation_token(project['provider_config'].get('installation_id'))
        return await request('GET',f'https://api.github.com/repos/{project["repositories"][0]}/actions/runs?per_page=30',token)

class Vercel(DeploymentProvider):
    capabilities={'deploy','redeploy','rollback'}
    def token(self):
        token=os.getenv('VERCEL_TOKEN')
        if not token: raise ProviderError('Configure VERCEL_TOKEN on the server.')
        return token
    async def execute(self,action,project,deployment):
        cfg=project.get('provider_config',{}); token=self.token()
        if not cfg.get('project_id'): raise ProviderError('Set the Vercel project ID in project settings.')
        params={'teamId':cfg['team_id']} if cfg.get('team_id') else {}
        body={'name':project['name'].lower().replace(' ','-'),'project':cfg['project_id'],'target':'production' if deployment['environment']=='production' else 'preview'}
        if action in {'redeploy','rollback'}:
            if not deployment.get('target_external_id'): raise ProviderError('The target deployment has no Vercel deployment ID.')
            body['deploymentId']=deployment['target_external_id']
        else:
            if not cfg.get('repo_id'): raise ProviderError('Set the numeric GitHub repository ID for Vercel deployments.')
            body['gitSource']={'type':'github','repoId':cfg['repo_id'],'ref':deployment['branch']}
        data=await request('POST','https://api.vercel.com/v13/deployments',token,json=body,params=params)
        return {'external_id':data['id'],'status':'building','url':data.get('url')}
    async def status(self,project,external_id): return await request('GET',f'https://api.vercel.com/v13/deployments/{external_id}',self.token())

class DockerCompose(DeploymentProvider):
    capabilities={'deploy','redeploy','rollback','restart','stop'}
    async def execute(self,action,project,deployment):
        cfg=project.get('provider_config',{})
        if not cfg.get('agent_id') or not cfg.get('service'): raise ProviderError('Configure an agent and allowlisted Compose service.')
        return {'status':'queued','agent_task':{'agent_id':cfg['agent_id'],'service':cfg['service'],'action':action,'image':deployment.get('image')}}
    async def status(self,project,external_id): return {'status':'queued'}
PROVIDERS={'GitHub Actions':GitHubActions(),'Vercel':Vercel(),'Docker Compose':DockerCompose()}
