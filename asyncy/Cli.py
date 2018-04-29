# -*- coding: utf-8 -*-
import click
import grpc

from asyncy.rpc import http_proxy_pb2
from asyncy.rpc import http_proxy_pb2_grpc
from .Config import Config
from .Logger import Logger

config = Config()
logger = Logger(config)
logger.start()


class Cli:

    @click.group()
    def main():
        pass

    @staticmethod
    @main.command()
    @click.argument('story')
    @click.argument('app_id')
    @click.option('--port', help='The port on which the engine is running', default='32781')
    @click.option('--host', help='The host on which the engine is running', default='localhost')
    @click.option('--block', help='Processes the block after this line')
    @click.option('--start', help='Force story to start from this line')
    @click.option('--context', help='Context data to start the story with')
    @click.option('--environment', help='Specify story environment')
    def run(app_id, story, block, start, context, environment, port, host):
        """
        Runs the given story immediately via an RPC call to the engine.
        :param app_id: The app ID
        :param story: The story name
        :param block: The block ID (string)
        :param start: Start processing this story from this line (string)
        :param context: Provide this context to the story (JSON string)
        :param environment: Provide this environment to the story (JSON string)
        :param port: The port on which the engine is running on
        :param host: The host on which the engine is running on
        """

        channel = grpc.insecure_channel(host + ':' + port)
        stub = http_proxy_pb2_grpc.HttpProxyStub(channel)
        req = http_proxy_pb2.Request(story_name=story, app_id=app_id, block=block,
                                     start=start, context=context, environment=environment)
        res = stub.RunStory(req)
        print(res.status_line)
