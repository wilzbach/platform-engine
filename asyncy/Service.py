# -*- coding: utf-8 -*-
import time
from concurrent import futures

import click
import grpc

from asyncy import Version
from asyncy.CeleryTasks import process_story
from asyncy.Config import Config
from asyncy.Logger import Logger
from asyncy.rpc import http_proxy_pb2
from .rpc.http_proxy_pb2_grpc import HttpProxyServicer, add_HttpProxyServicer_to_server

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

config = Config()
logger = Logger(config)
logger.start()


class Service(HttpProxyServicer):

    def RunStory(self, request, context):
        logger.log("rpc-request-run-story", request.story_name, request.app_id)
        process_story.delay(request.app_id, request.story_name, block=None, start=None,
                            context=None, environment=None)
        return http_proxy_pb2.Response(status=202, status_line="Accepted")

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
