import vimeo
import json
from urllib.parse import urlencode

with open('secrets.json', 'r') as f:
    api_key_json = json.load(f)
    
client = vimeo.VimeoClient(
    token=api_key_json["token"],
    key=api_key_json["client_id"],
    secret=api_key_json["secret"]
)

request_args = {
    'per_page': 2,
    'filter': 'nolive',
    'query_fields': 'type',
    'query': 'live',
    # 'fields': 'uri,name,link,created_time,modified_time,privacy.view',
    'sort': 'modified_time',
    'direction': 'desc'
}

resp = client.get(f"/me/videos/?{urlencode(request_args)}")
resp_json = json.loads(json.dumps(resp.json()))
with open('log.txt','w') as f:
    f.write(json.dumps(resp_json, indent=4))
# print(datetime.fromisoformat(resp.json()['data']['modified_time']))
d = dict(resp.json())