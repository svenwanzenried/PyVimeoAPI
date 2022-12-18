import vimeo
import json
import datetime
from datetime import datetime as dt, timedelta as td
from zoneinfo import ZoneInfo

from urllib.parse import urlencode

timezone = ZoneInfo('Europe/Zurich')

with open('secrets.json', 'r') as f:
    api_key_json = json.load(f)
    
client = vimeo.VimeoClient(
    token=api_key_json["token"],
    key=api_key_json["client_id"],
    secret=api_key_json["secret"]
)

# Find all Videos that are unlisted
request_args = {
    'per_page': 100,
    'filter': 'nolive',
    # 'query_fields': 'type',
    # 'query': 'live',
    'fields': 'uri,created_time,privacy.view',
    'sort': 'modified_time',
    'direction': 'desc'
}
resp = client.get(f"/me/videos/?{urlencode(request_args)}")
resp_json = json.loads(json.dumps(resp.json()))

next_page = resp_json['paging']['next']
video_ids = []
while True:
    video_ids += [
        video['uri'].split('/')[2]
        for video
        in resp_json['data']
        if (
            video['privacy']['view'] != 'nobody'
            and dt.fromisoformat(video['created_time']) < (dt.now(tz=timezone) - td(days=7)))]
    
    next = resp_json['paging']['next']
    if next is None:
        break
    else:
        resp = client.get(next)
        resp_json = json.loads(json.dumps(resp.json()))
    
print(f'Found video IDS that are not private: {video_ids}')

# Set found video to private
request_args = {
    
}
for id in video_ids:
    resp = client.patch(f'/videos/{id}', data={
        'privacy':{
            'view': 'nobody'
        }
    })
    print(resp)
    # print(str(resp.json()))

