import json
import time

from expiringdict import ExpiringDict

from tornado.httpclient import AsyncHTTPClient

from ..ReportingAgent import ReportingAgent, ReportingEvent
from ...Logger import Logger
from ...utils.HttpUtils import HttpUtils


class CleverTapAgent(ReportingAgent):
    throttle_cache = ExpiringDict(max_len=10000, max_age_seconds=30)

    def __init__(self, account_id: str, account_pass: str,
                 release: str, logger: Logger):
        self._account_id = account_id
        self._account_pass = account_pass
        self._release = release
        self._logger = logger
        self._http_client = AsyncHTTPClient()

    @staticmethod
    def get_throttle_key(re: ReportingEvent) -> str:
        return f'app_{re.app_uuid}_evt_{re.event_name}'

    def should_throttle(self, re: ReportingEvent) -> bool:
        key = self.get_throttle_key(re)
        should_throttle = self.throttle_cache.get(key) is not None

        if not should_throttle:
            self.throttle_cache[key] = True

        return should_throttle

    async def capture(self, re: ReportingEvent):
        if re.event_name is None or re.owner_uuid is None:
            return

        # Prevent the same event for the same app
        # from being raised several times.
        if self.should_throttle(re):
            return

        evt_data = {
            'Platform release': self._release,
            'App name': re.app_name,
            'Version': re.app_version,
            'Story name': re.story_name,
            'Story line': re.story_line
        }

        await HttpUtils.fetch_with_retry(
            tries=3, logger=self._logger,
            url='https://api.clevertap.com/1/upload',
            http_client=self._http_client,
            kwargs={
                'method': 'POST',
                'body': json.dumps({'d': [{
                    'ts': int(time.time()),
                    'identity': re.owner_uuid,
                    'evtName': re.event_name,
                    'evtData': evt_data,
                    'type': 'event'
                }]}),
                'headers': {
                    'X-CleverTap-Account-Id': self._account_id,
                    'X-CleverTap-Passcode': self._account_pass,
                    'Content-Type': 'application/json; charset=utf-8'
                }
            })
