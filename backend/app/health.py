import asyncio, ipaddress, socket, time, os
from urllib.parse import urlparse
import httpx

async def probe(url):
    parsed=urlparse(url)
    if parsed.scheme not in ('http','https') or not parsed.hostname or parsed.username or parsed.password: raise ValueError('Use an HTTP(S) URL without credentials.')
    addresses=await asyncio.get_running_loop().run_in_executor(None,lambda: socket.getaddrinfo(parsed.hostname,parsed.port or (443 if parsed.scheme=='https' else 80)))
    allowed=set(os.getenv('HEALTH_ALLOWED_HOSTS','').split(','))
    if parsed.hostname not in allowed and any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses): raise ValueError('Private targets must be explicitly allowlisted in HEALTH_ALLOWED_HOSTS.')
    start=time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=10,follow_redirects=False) as client:
            async with client.stream('GET',url) as response:
                status='healthy' if 200<=response.status_code<400 else 'down'
                return {'status':status,'latency':round((time.monotonic()-start)*1000),'http_status':response.status_code}
    except httpx.HTTPError: return {'status':'down','latency':round((time.monotonic()-start)*1000),'error':'Connection or TLS verification failed'}
