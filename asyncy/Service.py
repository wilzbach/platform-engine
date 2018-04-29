# -*- coding: utf-8 -*-
import time
from concurrent import futures

import click
import grpc
import ujson

from asyncy import Version
from asyncy.Config import Config
from asyncy.Logger import Logger
from asyncy.processing import Story
from asyncy.rpc import http_proxy_pb2
from .rpc.http_proxy_pb2_grpc import HttpProxyServicer, add_HttpProxyServicer_to_server

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

config = Config()
logger = Logger(config)
logger.start()


class Service(HttpProxyServicer):

    def RunStory(self, request, context):
        logger.log("rpc-request-run-story", request.story_name, request.app_id)

        environment = {}
        context = {}

        if request.json_environment is not None and request.json_environment is not "":
            environment = ujson.loads(request.json_environment)

        if request.json_context is not None and request.json_context is not "":
            context = ujson.loads(request.json_context)

        Story.run(config, logger, app_id=request.app_id, story_name=request.story_name,
                  environment=environment, context=context,
                  block=request.block, start=request.start)

        return http_proxy_pb2.Response(status=200, status_line="OK")

    @click.group()
    def main():
        pass

    @staticmethod
    @main.command()
    @click.option('--port', help='Set the port on which the RPC server binds to', default='32781')
    def server(port):
        logger.log("service-init", Version.version)
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        add_HttpProxyServicer_to_server(Service(), server)
        server.add_insecure_port('[::]:' + port)

        server.start()
        logger.log("rpc-init", port)

        try:
            while True:
                time.sleep(_ONE_DAY_IN_SECONDS)
        except KeyboardInterrupt:
            server.stop(0)
