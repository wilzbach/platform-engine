import sentry_sdk

from ..ReportingAgent import ReportingAgent, ReportingEvent
from ...Exceptions import StoryscriptError
from ...Logger import Logger


class SentryAgent(ReportingAgent):
    _sentry_client = None

    def __init__(self, dsn: str, release: str, logger: Logger):
        """
        Initialises Sentry without breadcrumbs, logging hook, and
        hook libraries as Sentry relies on a thread local for it's context,
        which is not feasible in an asyncio context.
        """
        self._release = release
        self._logger = logger

        sentry_sdk.init(
            dsn=dsn,
            release=release,
            max_breadcrumbs=0,
            integrations=[],
            default_integrations=False
        )

    async def capture(self, re: ReportingEvent):
        exc_info = re.exc_info

        if isinstance(exc_info, StoryscriptError):
            return

        with sentry_sdk.configure_scope() as scope:
            user_context = {
                'app_uuid': re.app_uuid,
                'app_version': re.app_version,
                'platform_release': self._release,
                'app_name': re.app_name,
                'story_name': re.story_name,
                'story_line': re.story_line
            }

            if re.owner_email is not None:
                user_context['email'] = re.owner_email

            scope.user = user_context

            try:
                sentry_sdk.capture_exception(error=exc_info)
            finally:
                scope.clear()
