import vimeo
import json
import datetime
from datetime import datetime as dt, timedelta as td
from zoneinfo import ZoneInfo
import requests

from urllib.parse import urlencode

timezone = ZoneInfo('Europe/Zurich')

with open('secrets.json', 'r') as f:
    secrets = json.load(f)
    
vimeo_api = vimeo.VimeoClient(
    token=secrets["vimeo_token"],
    key=secrets["vimeo_client_id"],
    secret=secrets["vimeo_secret"])

pushover_api_url = "https://api.pushover.net/1/messages.json"

# Find all videos that contain the service keyword
title_new_video = 'Gottesdienst'
request_args = {
    'per_page': 10,
    'filter': 'nolive',
    'query_fields': 'title',
    'query': title_new_video,
    'fields': 'uri, link, name, created_time, privacy.view',
    'sort': 'modified_time',
    'direction': 'desc'
}
resp = vimeo_api.get(f"/me/videos/?{urlencode(request_args)}")
resp_json = json.loads(json.dumps(resp.json()))
print(resp_json)

found_new_video = False
for video in resp_json['data']:
    creation_date = dt.fromisoformat(video['created_time']).date()
    if creation_date >= (dt.now(tz=timezone) - td(weeks=4)).date():
        if video['name'] == title_new_video:
            found_new_video = True
            video_id = video['uri'].split('/')[2]
            resp = vimeo_api.patch(f'/videos/{video_id}', data={
                'name': f"{title_new_video} {creation_date.strftime('%d.%m.%Y')}"})
            msg = f"New video online:\n{title_new_video} {creation_date.strftime('%d.%m.%Y')}\n{video['link']}"
            requests.post(pushover_api_url, {'token': secrets['pushover_token'], 'user': secrets['pushover_user_key'], 'message': msg})
            print(msg)

        if creation_date < (dt.now(tz=timezone) - td(weeks=1)).date():
            if video['privacy']['view'] != 'nobody':
                resp = vimeo_api.patch(f'/videos/{video_id}', data={'privacy': {'view': 'nobody'}})
    else:
        continue