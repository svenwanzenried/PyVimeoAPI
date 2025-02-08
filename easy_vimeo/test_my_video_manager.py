from datetime import datetime
import pandas
from .my_video_manager import Manager
import pytest
import json


class TestManager:

    def test_valid_credentials(self):
        with open('secrets.json', 'r') as f:
            secrets = json.load(f)
        assert 'vimeo_client_id' in secrets
        assert 'vimeo_token' in secrets
        assert 'vimeo_secret' in secrets
        Manager._get_valid_client(secrets['vimeo_client_id'], secrets['vimeo_token'], secrets['vimeo_secret'])

    def test_manager_invalid_credentials(self):
        with pytest.raises(Exception):
            m = Manager('', '', '')

    def test_manager_valid_credentials(self):
        with open('secrets.json', 'r') as f:
            secrets = json.load(f)
        m = Manager(secrets['vimeo_client_id'], secrets['vimeo_token'], secrets['vimeo_secret'])

    def test_manager_get_all(self):
        with open('secrets.json', 'r') as f:
            secrets = json.load(f)
        m = Manager(secrets['vimeo_client_id'], secrets['vimeo_token'], secrets['vimeo_secret'])
        start_date = datetime(year=2023, month=1, day=1)
        df = m.get_videos(start_date=start_date)
        df.to_csv('test_manager_get_all.csv')
        assert isinstance(df, pandas.DataFrame)
        assert len(df) > 10 # Because test account has way more that 100 videos
        
