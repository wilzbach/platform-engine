# -*- coding: utf-8 -*-
import asyncio


class DeploymentLock:

    lock = asyncio.Lock()
    apps = {}

    async def try_acquire(self, app_id):
        """
        Non blocking acquire. If a deployment can continue, this
        method will return True. If a deployment for an app is already locked,
        then this will return False.
        """
        async with self.lock:
            if self.apps.get(app_id):
                return False

            self.apps[app_id] = True

        return True

    async def release(self, app_id):
        async with self.lock:
            self.apps.pop(app_id)
