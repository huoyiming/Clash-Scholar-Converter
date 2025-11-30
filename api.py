from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import aiohttp
import yaml

app = FastAPI()

# 分流列表
list_url = "https://res.eming.fun/SCC/sci.list"
# 分流节点
proxy = {
    'name': 'xxx-university',
    'type': 'http',
    'server': 'xxx',
    'port': 14514,
}

headers = {
    "User-Agent": 'clash'
}

# Set your base URL here if needed
base_url = ''

@app.get("/api")
async def convert(request: Request):
    url = base_url + request.scope['query_string'].decode()[4:]
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(list_url) as response:
                list_file = await response.text()
                sci_list = [i for i in list_file.splitlines() if i.strip() and not i.startswith("#")]
            async with session.get(url) as response:
                raw_sub = yaml.safe_load(await response.text())
                raw_headers = response.headers
    except Exception as e:
        return {"error": str(e)}
    if 'proxies' not in raw_sub:
        return {"error": "No proxies found in the subscription."}
    raw_sub['proxies'].append(proxy)
    if 'proxy-groups' not in raw_sub:
        return {"error": "No proxy-groups found in the subscription."}
    scholar_proxies = raw_sub['proxy-groups'][0]['proxies'].copy()
    scholar_proxies.insert(0, proxy['name'])
    raw_sub['proxy-groups'].insert(1,{
        'name': 'Scholar',
        'type': 'select',
        'proxies': scholar_proxies,
    })
    if 'rules' not in raw_sub:
        return {"error": "No rules found in the subscription."}
    sci_rules = [f'{i},Scholar' for i in sci_list]
    raw_sub['rules'][:0] = sci_rules
    new_header = {i: raw_headers[i] for i in raw_headers if i.lower() in ['profile-update-interval', 'subscription-userinfo', 'content-disposition', 'profile-web-page-url']}
    return PlainTextResponse(yaml.safe_dump(raw_sub), headers=new_header)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=14514)