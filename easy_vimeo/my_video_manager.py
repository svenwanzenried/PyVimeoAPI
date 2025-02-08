import datetime
import re
import urllib.parse
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, List, Optional
import numpy

import pandas
import requests
import vimeo


class VideoType(Enum):
    """Provides the strings used in the 'filter' parameter in Vimeo API"""
    APP_ONLY: str = 'app_only'
    EMBEDDABLE: str = 'embeddable'
    FEATURED: str = 'featured'
    LIVE: str = 'live'
    NOPLACEHOLDER: str = 'no_placeholder'
    NOLIVE: str = 'nolive'
    PLAYABLE: str = 'playable'
    SCREEN_RECORDED: str = 'screen_recorded'


class SortDirection(Enum):
    """Provides the strings used for 'direction' parameter in Vimeo API"""
    ASCENDING: str = 'asc'
    DESCENDING: str = 'desc'


class QueryField(Enum):
    """Provides the strings used for 'query_fields' parameter in Vimeo API"""
    CHAPTERS: str = 'chapters'
    DESCRIPTION: str = 'description'
    TAGS: str = 'tags'
    TITLE: str = 'title'


class SortCiteria(Enum):
    """Provides the strings used for 'sort' parameter in Vimeo API"""
    ALPHABETICAL: str = 'alphabetical'
    DATE_CREATION: str = 'date'  # TODO Check if this is really the creation date
    DATE_MODIFY: str = 'modified_time'
    DATE_LAST_USER_ACTION: str = 'last_user_action_event_date'
    DEFAULT: str = 'default'
    DURATION: str = 'duration'
    NUMBER_OF_LIKES: str = 'likes'
    NUMBER_OF_PLAYS: str = 'plays'


@dataclass
class RequestArgs():
    """Provides abstraction for the parameters passed to the
        '/users/{user_id}/videos' query in Vimeo API"""
    type: Optional[VideoType] = None
    sort_criteria: Optional[SortCiteria] = None
    sort_direction: Optional[SortDirection] = None
    query_fields: Optional[List[QueryField]] = None
    query: Optional[str] = None
    fields: Optional[List[str]] = None
    _video_per_page: int = 1  # This the user should not specify as it is specific to the processing method

    def _encoded(self) -> str:
        all_args = {
            'per_page': self._video_per_page,
            'filter': self.type.value if self.type else None,
            'query_fields': ','.join([f.value for f in self.query_fields]) if self.query_fields else None,
            'query': self.query,
            'fields': ', '.join(self.fields) if self.fields else None,
            'sort': self.sort_criteria.value if self.sort_criteria else None,
            'direction': self.sort_direction.value if self.sort_direction else None
        }
        return urllib.parse.urlencode({k: v for (k, v) in all_args.items() if v is not None})


class Manager():
    """Provides a high level abstraction to manage a users videos on Vimeo"""

    vimeo_client_id: str
    vimeo_toke: str
    vimeo_secret: str

    def __init__(self, client_id: str, token: str, secret: str) -> None:
        # Initialize API with credentials
        self.api = Manager._get_valid_client(client_id, token, secret)

    def get_videos(self,
                   query_fields: Optional[List[QueryField]] = None,
                   query: Optional[str] = None,
                   start_date: Optional[datetime.datetime] = None,
                   end_date: Optional[datetime.datetime] = None) -> pandas.DataFrame:
        """
        Fetches basic information about all user videos on Vimeo
        Can be limited by query string or by date (However date filter can only
        be applied after web request. Therefore some delay should be expected)
        For filtering, the date of the last added video file is used,
        as this seems to be the 'default' order Vimeo uses.
        This value can be accessed by column 'newest_file_date' inside return dataframe
        """

        # Setup correct times
        if start_date is None:
            # Begin of epoch, but there is a bug in the system when requesting timezones for dates before 03.01.1970
            start_date = datetime.datetime(year=1970, month=1, day=3).astimezone()
        else:
            start_date = start_date.astimezone()
        if end_date is None:
            # 1 day in the future
            end_date = datetime.datetime.now().astimezone() + datetime.timedelta(hours=24)
        else:
            end_date = end_date.astimezone()

        # Setup arguments
        fields = [
            'uri',
            'name',
            'description',
            'type',
            'link',
            'duration',
            'created_time',
            'modified_time',
            'release_time',
            'files.created_time',
            # 'tags.name',
            'privacy.view',
            'stats.plays',
            'last_user_action_event_date',
            'status',
            'transcode.status',
        ]
        args = RequestArgs(
            _video_per_page=100,
            # sort_direction=SortDirection.DESCENDING,
            sort_criteria=SortCiteria.DEFAULT,
            fields=fields,
            query_fields=query_fields,
            query=query)

        all_videos = self._get_all_results(f"/me/videos/?{args._encoded()}")

        # Drop all videos, that to not match date boundaries (if given)
        all_videos = all_videos.drop(all_videos.newest_file_date[all_videos.newest_file_date < start_date].index)
        all_videos = all_videos.drop(all_videos.newest_file_date[all_videos.newest_file_date > end_date].index)

        return all_videos

    @classmethod
    def _get_valid_client(self, client_id, token, secret) -> vimeo.VimeoClient:
        client = vimeo.VimeoClient(token=token, key=client_id, secret=secret)
        request_args = RequestArgs(_video_per_page=1)
        resp: requests.Response = client.get(f"/me/videos/?{request_args._encoded()}")
        if resp.status_code != 200:
            raise Exception("Login to Vimeo not possible! Did you pass correct credentials?")
        return client

    def _get_all_results(self, url: str) -> pandas.DataFrame:
        all_videos = pandas.DataFrame()

        resp = self.api.get(url)
        resp_json = resp.json()
        while True:
            for video in resp_json['data']:
                v = pandas.DataFrame(pandas.json_normalize(video), index=[0])
                all_videos = pandas.concat([all_videos, v], ignore_index=True)

            # Check for next page
            next = resp_json['paging']['next']
            if next is None:
                break
            else:
                resp = self.api.get(next)
                resp_json = resp.json()

        # # Add column with tags exctracted that fit dd.mm.yyyy
        # all_videos['date_tag'] = all_videos.apply(
        #     lambda tags: re.search('\d{2}\.\d{2}\.\d{4}', str(tags['tags'])).group() if tags['tags'] else None, axis=1)

        # Get newest date of all containing files per video
        all_videos['newest_file_date'] = all_videos.files.apply(lambda video: self._get_newest_file_date(video))
        all_videos.newest_file_date = all_videos.newest_file_date.fillna(all_videos.created_time)
        all_videos = all_videos.drop('files', axis=1)

        # Parse the date strings to datetime format
        # all_videos['created_time'] = pandas.to_datetime(all_videos['created_time'])
        # all_videos['modified_time'] = pandas.to_datetime(all_videos['modified_time'])
        # all_videos['release_time'] = pandas.to_datetime(all_videos['release_time'])
        # all_videos['last_user_action_event_date'] = pandas.to_datetime(all_videos['last_user_action_event_date'])
        # all_videos['newest_file_date'] = [(str(s) if not pandas.isnull(s) else pandas.NaT) for s in all_videos['newest_file_date']]

        return all_videos

    def _get_newest_file_date(self, data: List[dict]) -> datetime.datetime:
        if not data:
            return None
        times = [datetime.datetime.fromisoformat(d['created_time']) for d in data]
        return max(times)
