# -*- coding: utf-8 -*-
import asyncio
import json
import pathlib
import shutil
from collections import deque
from unittest.mock import ANY, call

import pytest
from pytest import fixture, mark

from storyruntime.App import App, AppData
from storyruntime.AppConfig import Forward
from storyruntime.Containers import Containers
from storyruntime.Exceptions import StoryscriptError
from storyruntime.Kubernetes import Kubernetes
from storyruntime.Types import StreamingService
from storyruntime.constants.ServiceConstants import ServiceConstants
from storyruntime.entities.Release import Release
from storyruntime.enums.AppEnvironment import AppEnvironment
from storyruntime.processing import Stories
from storyruntime.processing.Services import Command, Service, Services
from storyruntime.utils.ConstDict import ConstDict
from storyruntime.utils.HttpUtils import HttpUtils

from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPResponse


@fixture
def exc(patch):
    def func(*args):
        raise Exception()

    return func


@fixture
def app(config, logger, magic):
    return App(
        app_data=AppData(
            release=Release(
                app_uuid="app_uuid",
                app_name="app_name",
                app_dns="app_dns",
                owner_uuid="owner_uuid",
                owner_email="example@example.com",
                environment={},
                stories=magic(),
                version=magic(),
                always_pull_images=False,
                maintenance=False,
                deleted=False,
                state="QUEUED",
                app_environment=AppEnvironment.PRODUCTION,
            ),
            config=config,
            logger=logger,
            services={},
            app_config=magic(),
        )
    )


def test_add_subscription(patch, app, magic):
    streaming_service = magic()
    payload = {"payload": True}
    app.add_subscription("sub_id", streaming_service, "event_name", payload)
    sub = app.get_subscription("sub_id")
    assert sub.streaming_service == streaming_service
    assert sub.id == "sub_id"
    assert sub.payload == payload
    assert sub.event == "event_name"
    app.remove_subscription("sub_id")
    assert app.get_subscription("sub_id") is None


@mark.asyncio
@mark.parametrize("response_code", [200, 500])
async def test_unsubscribe_all(patch, app, async_mock, magic, response_code):
    streaming_service = StreamingService(
        "alpine", "echo", "alpine-1", "alpine.com"
    )

    payload = {"sub_body": {"payload": True}}
    app.add_subscription("sub_id", streaming_service, "event_name", payload)

    app.add_subscription(
        "sub_id_with_no_unsub", streaming_service, "foo", payload
    )

    app.services = {
        "alpine": {
            ServiceConstants.config: {
                "actions": {
                    "echo": {
                        "events": {
                            "event_name": {
                                "http": {
                                    "unsubscribe": {
                                        "port": 28,
                                        "path": "/unsub",
                                    }
                                }
                            },
                            "foo": {"http": {}},
                        }
                    }
                }
            }
        }
    }

    res = magic()
    res.code = response_code
    patch.object(
        HttpUtils, "fetch_with_retry", new=async_mock(return_value=res)
    )

    patch.init(AsyncHTTPClient)

    client = AsyncHTTPClient()

    await app.unsubscribe_all()

    url = "http://alpine.com:28/unsub"
    expected_kwargs = {
        "method": "POST",
        "body": json.dumps(payload["sub_body"]),
        "headers": {"Content-Type": "application/json; charset=utf-8"},
    }

    HttpUtils.fetch_with_retry.mock.assert_called_with(
        3, app.logger, url, client, expected_kwargs
    )

    if response_code != 200:
        app.logger.error.assert_called_once()


@mark.parametrize("env", [{"env": True}, None, {"a": {"nested": "1"}}])
@mark.parametrize("always_pull_images", [False, True])
def test_app_init(magic, config, logger, env, always_pull_images):
    services = magic()
    stories = magic()
    expected_secrets = {}
    if env:
        for k, v in env.items():
            if not isinstance(v, dict):
                expected_secrets[k.lower()] = v

    version = 100
    app_config = magic()
    config.APP_DOMAIN = "asyncyapp.com"

    app = App(
        app_data=AppData(
            release=Release(
                app_uuid="app_id",
                app_name="app_name",
                app_dns="app_dns",
                version=version,
                stories=stories,
                always_pull_images=always_pull_images,
                environment=env,
                owner_uuid="owner_1",
                owner_email="example@example.com",
                maintenance=False,
                deleted=False,
                state="QUEUED",
                app_environment=AppEnvironment.PRODUCTION,
            ),
            app_config=app_config,
            services=services,
            config=config,
            logger=logger,
        )
    )

    if env is None:
        env = {}

    assert app.app_id == "app_id"
    assert app.app_dns == "app_dns"
    assert app.config == config
    assert app.logger == logger
    assert app.owner_uuid == "owner_1"
    assert app.owner_email == "example@example.com"
    assert app.stories == stories["stories"]
    assert app.services == services
    assert app.always_pull_images == always_pull_images
    assert app.environment == env
    assert app.app_context["hostname"] == f"{app.app_dns}.asyncyapp.com"
    assert app.app_context["version"] == version
    assert app.app_context["secrets"] == expected_secrets
    assert app.entrypoint == stories["entrypoint"]
    assert app.app_config == app_config

    if always_pull_images is True:
        assert app.image_pull_policy() == "Always"
    else:
        assert app.image_pull_policy() == "IfNotPresent"


@mark.asyncio
async def test_app_bootstrap(patch, app, async_mock):
    patch.object(app, "run_stories", new=async_mock())
    patch.object(app, "start_services", new=async_mock())
    stories = {"entrypoint": ["foo"], "stories": {"foo": {}}}
    app.stories = stories
    app.story_global_contexts = {"foo": {}}
    await app.bootstrap()

    assert app.run_stories.mock.call_count == 1
    assert app.start_services.mock.call_count == 1

    for story in app.story_global_contexts:
        assert isinstance(app.story_global_contexts[story], ConstDict)


def test_app_get_tmp_dir(app):
    assert app.get_tmp_dir() == "/tmp/story.app_uuid"


def test_app_create_tmp_dir(patch, app):
    patch.object(pathlib, "Path")
    patch.object(app, "get_tmp_dir")

    # create_tmp_dir is called twice to ensure the dir is created just once.
    app.create_tmp_dir()
    app.create_tmp_dir()

    app.get_tmp_dir.assert_called_once()

    pathlib.Path.assert_called_with(app.get_tmp_dir())
    pathlib.Path().mkdir.assert_called_with(
        parents=True, mode=0o700, exist_ok=True
    )


def test_app_create_tmp_dir_exc(patch, magic, app):
    def exc(*args, **kwargs):
        raise BaseException()

    path = magic()
    path.mkdir.side_effect = exc

    patch.object(pathlib, "Path", return_value=path)
    patch.object(app, "get_tmp_dir")

    with pytest.raises(BaseException):
        app.create_tmp_dir()

    app.logger.error.assert_called()


def test_app_cleanup_tmp_dir(patch, app):
    path = f"/tmp/story.{app.app_id}"
    patch.object(app, "get_tmp_dir", return_value=path)
    patch.object(shutil, "rmtree")

    app.cleanup_tmp_dir()

    app.get_tmp_dir.assert_called()
    shutil.rmtree.assert_called_with(path, ignore_errors=True)


def test_app_cleanup_tmp_dir_exc(patch, app):
    path = f"/tmp/story.{app.app_id}"

    def exc(*args, **kwargs):
        raise BaseException()

    patch.object(app, "get_tmp_dir", return_value=path)
    patch.object(shutil, "rmtree", side_effect=exc)
    with pytest.raises(BaseException):
        app.cleanup_tmp_dir()

    app.logger.error.assert_called()


@mark.asyncio
async def test_start_services_completed(patch, app, async_mock):
    app.stories = {}
    patch.object(asyncio, "wait", new=async_mock(return_value=([], [])))
    await app.start_services()


@mark.asyncio
async def test_start_services_completed_exc(patch, app, async_mock, magic):
    app.stories = {
        "a": {"tree": {"1": {"method": "execute"}}, "entrypoint": "1"}
    }

    patch.object(Services, "is_internal", return_value=False)
    chain = deque()
    chain.append(Service(name="foo"))
    chain.append(Command(name="foo"))
    patch.object(Services, "resolve_chain", return_value=chain)
    task = magic()
    task.exception.return_value = Exception()
    patch.object(asyncio, "wait", new=async_mock(return_value=([task], [])))
    with pytest.raises(Exception):
        await app.start_services()


@mark.parametrize("internal", [True, False])
@mark.asyncio
async def test_start_services(patch, app, async_mock, magic, internal):
    app.stories = {
        "a.story": {
            "tree": {
                "1": {"method": "execute", "next": "2"},
                "2": {"method": "execute", "next": "3"},
                "3": {"method": "not_execute"},
            },
            "entrypoint": "1",
        }
    }
    chain = deque()
    chain.append(Service(name="cold_service"))
    chain.append(Command(name="cold_command"))

    start_container_result = magic()

    patch.object(Services, "resolve_chain", return_value=chain)
    patch.object(Services, "is_internal", return_value=internal)
    patch.object(
        Services, "start_container", return_value=start_container_result
    )
    patch.object(asyncio, "wait", new=async_mock(return_value=([], [])))

    await app.start_services()

    tasks = [start_container_result]

    if not internal:
        asyncio.wait.mock.assert_called_with(tasks)

        assert Services.start_container.call_count == 1
        Services.start_container.assert_has_calls(
            calls=[call(ANY, {"method": "execute", "next": "2"})]
        )

    else:
        assert Services.start_container.call_count == 0


@mark.asyncio
async def test_start_services_multiple(patch, app, async_mock, magic):
    app.stories = {
        "a.story": {
            "tree": {
                "1": {"method": "execute", "src": "1"},
                "2": {"method": "execute", "src": "2"},
                "3": {"method": "not_execute"},
                "4": {"method": "execute", "src": "4"},
                "5": {"method": "execute", "src": "5"},
            },
            "entrypoint": "1",
        }
    }
    # checks that only three services get spawned (no duplicate of
    # cold_service)
    chains = [
        deque([Service(name="cold_service"), Command(name="cold_command")]),
        deque([Service(name="cold_service"), Command(name="cold_command")]),
        deque([Service(name="warm_service"), Command(name="cold_command")]),
        deque([Service(name="hot_service"), Command(name="cold_command")]),
    ]

    start_container_result = magic()

    patch.object(Services, "resolve_chain", side_effect=chains)
    patch.object(Services, "is_internal", return_value=False)
    patch.object(
        Services, "start_container", return_value=start_container_result
    )
    patch.object(asyncio, "wait", new=async_mock(return_value=([], [])))

    await app.start_services()

    tasks = [
        start_container_result,
        start_container_result,
        start_container_result,
    ]

    asyncio.wait.mock.assert_called_with(tasks)

    assert Services.start_container.call_count == 3
    Services.start_container.assert_has_calls(
        calls=[
            call(ANY, {"method": "execute", "src": "1"}),
            call(ANY, {"method": "execute", "src": "4"}),
            call(ANY, {"method": "execute", "src": "5"}),
        ]
    )


@mark.asyncio
async def test_expose_services(patch, app, async_mock):
    a = Forward(service="foo", service_forward_name="foo", http_path="foo")
    b = Forward(service="foo", service_forward_name="foo", http_path="foo")
    patch.object(app.app_config, "get_expose_config", return_value=[a, b])
    patch.object(App, "_expose_service", new=async_mock())

    await app.expose_services()

    assert app._expose_service.mock.call_count == 2


@mark.parametrize("no_config", [True, False])
@mark.parametrize("no_http_path", [True, False])
@mark.asyncio
async def test_expose_service(patch, app, async_mock, no_config, no_http_path):
    if no_http_path and no_config:
        # THey're mutually exclusive.
        return

    app.services = {
        "foo": {
            "configuration": {
                "expose": {
                    "my_expose_name": {
                        "http": {"path": "/expose_path", "port": 1993}
                    }
                }
            }
        }
    }

    if no_config:
        app.services["foo"]["configuration"]["expose"]["my_expose_name"] = None

    if no_http_path:
        app.services["foo"]["configuration"]["expose"]["my_expose_name"][
            "http"
        ]["path"] = None

    patch.object(Containers, "expose_service", new=async_mock())

    e = Forward(
        service="foo",
        service_forward_name="my_expose_name",
        http_path="/expose_external_path",
    )

    if no_config or no_http_path:
        with pytest.raises(StoryscriptError):
            await app._expose_service(e)
    else:
        await app._expose_service(e)
        Containers.expose_service.mock.assert_called_with(app, e)


@mark.asyncio
async def test_app_run_stories(patch, app, async_mock):
    stories = {"foo": {}, "bar": {}}
    app.entrypoint = ["foo", "bar"]
    app.stories = stories
    patch.object(Stories, "run", new=async_mock())
    await app.run_stories()
    assert Stories.run.mock.call_count == 2


@mark.asyncio
async def test_app_destroy_no_stories(patch, async_mock, app):
    app.stories = None
    patch.object(Kubernetes, "clean_namespace", new=async_mock())
    patch.object(app, "clear_subscriptions_synapse", new=async_mock())
    patch.object(app, "cleanup_tmp_dir")
    assert await app.destroy() is None


@mark.asyncio
async def test_app_run_stories_exc(patch, app, async_mock, exc):
    app.stories = {"foo": {}, "bar": {}}
    app.entrypoint = ["foo", "bar"]
    patch.object(app, "logger")

    patch.object(Stories, "run", new=async_mock(side_effect=exc))

    with pytest.raises(Exception):
        await app.run_stories()


@mark.asyncio
@mark.parametrize("status_code", [200, 500])
async def test_clear_subscriptions_synapse(
    patch, app, async_mock, status_code
):
    app.app_id = "my_cool_app"
    app.config.ASYNCY_SYNAPSE_HOST = "syn"
    app.config.ASYNCY_SYNAPSE_PORT = 9000

    expected_url = (
        f"http://{app.config.ASYNCY_SYNAPSE_HOST}:"
        f"{app.config.ASYNCY_SYNAPSE_PORT}/clear_all"
    )

    expected_kwargs = {
        "method": "POST",
        "body": json.dumps({"app_id": app.app_id}),
        "headers": {"Content-Type": "application/json; charset=utf-8"},
    }
    res = HTTPResponse(HTTPRequest(url=expected_url), status_code)
    patch.object(
        HttpUtils, "fetch_with_retry", new=async_mock(return_value=res)
    )

    ret = await app.clear_subscriptions_synapse()
    HttpUtils.fetch_with_retry.mock.assert_called_with(
        3, app.logger, expected_url, AsyncHTTPClient(), expected_kwargs
    )

    if status_code == 200:
        assert ret is True
    else:
        assert ret is False


@mark.asyncio
async def test_app_destroy(patch, app, async_mock):
    app.stories = {"foo": {}, "bar": {}}
    app.entrypoint = ["foo", "bar"]
    patch.object(app, "unsubscribe_all", new=async_mock())
    patch.object(app, "clear_subscriptions_synapse", new=async_mock())
    patch.object(app, "cleanup_tmp_dir")
    await app.destroy()

    app.unsubscribe_all.mock.assert_called()
    app.clear_subscriptions_synapse.mock.assert_called()
    app.cleanup_tmp_dir.assert_called()
