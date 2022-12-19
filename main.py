import vimeo
import json
from urllib.parse import urlencode

with open('secrets.json', 'r') as f:
    api_key_json = json.load(f)
    
client = vimeo.VimeoClient(
    token=api_key_json["vimeo_token"],
    key=api_key_json["vimeo_client_id"],
    secret=api_key_json["vimeo_secret"]
)

request_args = {
    'per_page': 10,
    # 'filter': 'nolive',
    'query_fields': 'description',
    'query': 'test',
    'fields': 'uri, link, name, type, duration, modified_time, created_time, privacy.view',
    'sort': 'date',
    'direction': 'desc'
}

resp = client.get(f"/me/videos/?{urlencode(request_args)}")
resp_json = json.loads(json.dumps(resp.json()))
with open('log.txt','w') as f:
    f.write(json.dumps(resp_json, indent=4))
print(f"Found videos: { len(resp_json['data']) }")
# print(datetime.fromisoformat(resp.json()['data']['modified_time']))
d = dict(resp.json())