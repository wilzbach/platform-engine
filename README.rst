Asyncy platform engine
#######################
The engine powering Asyncy and executing stories.


Installing
-----------
See https://github.com/asyncy/stack-compose to install in production.


For testing, you will need RabbitMQ and MongoDB. Then you can install with::


    python setup.py install


Running a story
----------------
You can run a story from cli with::

    asyncy run hello.story 1

This will request a story to the API, from /apps/1/stories/hello.story and
run it.


Configuration options
----------------------
The engine loads its configuration options from the envrionment. Some defaults
are provided::

    export mongo=mongodb://mongodb:27017/
    export broker=amqp://rabbitmq:rabbitmq@rabbitmq:5672//
    export api_url=api-private:8080
    export logger_name=asyncy
    export loggger_level=warning
