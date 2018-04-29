Asyncy platform engine
#######################
The engine powering Asyncy and executing stories.

The engine queries Asyncy's API to get the stories' syntax tree and process it


Installing
-----------
See https://github.com/asyncy/stack-compose to install in production.


For testing, you will need MongoDB. Then you can install with::


    python setup.py install


Running a story
----------------
You can run a story from cli with::

    asyncy run hello.story 1

This will request a story to the API, from /apps/1/stories/hello.story and
run it.


Configuration options
----------------------
The engine loads its configuration options from the environment. Defaults are
provided::

    export mongo=mongodb://mongodb:27017/
    export api_url=api-private:8080
    export logger_name=asyncy
    export loggger_level=warning

Testing
-------
To run the engine in a testing environment:

1. Install the engine in a virtualenv
2. Set testing environment variables:
    - ``export mongo=mongodb://localhost:27017/``
    - ``export api_url=localhost``
3. Start a mock http server that answers to GET requests against http://localhost/apps/app_id/stories/story_name with a mock, but valid JSON story document
4. Run ``asyncy server`` to start the engine
5. Run ``asyncy-cli run story_name app_id`` to run the story

Generating gRPC python code from the proto files
------------------------------------------

To generate the python code from the proto files, run the following:
``python -m grpc_tools.protoc -Iprotos --python_out=. --grpc_python_out=. protos/asyncy/rpc/http_proxy.proto``