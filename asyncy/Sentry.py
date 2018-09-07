# -*- coding: utf-8 -*-


class Sentry:

    @staticmethod
    def clear_and_set_context(sentry_client, app_id: str, version: int):
        sentry_client.context.clear()
        sentry_client.user_context({
            'app_uuid': app_id,
            'app_version': version
        })
