import json
import time
from datetime import datetime
from threading import Event, Thread
from urllib.parse import urlencode

import vimeo

with open('api-key.json', 'r') as f:
    api_key_json = json.load(f)
client = vimeo.VimeoClient(
    token=api_key_json["token"],
    key=api_key_json["client_id"],
    secret=api_key_json["secret"]
)

polling_args = {
    'per_page': 1,
    'filter': 'nolive',
    'fields': 'uri,name,link,created_time,modified_time,privacy',
    'sort': 'modified_time',
    'direction': 'desc'
}

def polling(stop_event):
    while stop_event.is_set() is False:
        resp = client.get(f"/me/videos/?{urlencode(polling_args)}")
        # with open('log.txt','w') as f:
        #     f.write(str(resp.json()))
        # print(datetime.fromisoformat(resp.json()['data']['modified_time']))
        d = dict(resp.json())
        print(d['data'][0]['modified_time'])
        time.sleep(1)
        
        
        
stop_event = Event()
t1 = Thread(target=polling, args=(stop_event,))

t1.start()

print('Press any Key to quit')
input()

stop_event.set()
t1.join()
    

# resp = client.get("/me/videos")
# print(resp)


