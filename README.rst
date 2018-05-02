Asyncy platform engine
#######################
The engine powering Asyncy and executing stories.

The engine queries Asyncy's API to get the stories' syntax tree and process it


Installing
-----------
See https://github.com/asyncy/stack-compose to install in production.


    python setup.py install


Running a story
----------------
You can run a story from cli with::

    asyncy-engine run hello.story

This will request a story to the API, from /apps/1/stories/hello.story and
run it.


Configuration options
----------------------
The engine loads its configuration options from the environment. Defaults are
provided::

    export api_url=api-private:8080
    export logger_name=asyncy
    export loggger_level=warning

Testing
-------
To run the engine in a testing environment:

1. Install the engine in a virtualenv
2. Run ``asyncy-server start`` to start the engine
3. Run ``asyncy-engine run story_name`` to run the story

Generating gRPC python code from the proto files
------------------------------------------

To generate the python code from the proto files, run the following:
``python -m grpc_tools.protoc -Iprotos --python_out=. --grpc_python_out=. protos/asyncy/rpc/http_proxy.proto``
