Asyncy platform engine
#######################
The engine powering Asyncy and executing stories.

The engine queries Asyncy's API to get the stories' syntax tree and process it


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
The engine loads its configuration options from the environment. Defaults are
provided::

    export mongo=mongodb://mongodb:27017/
    export broker=amqp://rabbitmq:rabbitmq@rabbitmq:5672//
    export api_url=api-private:8080
    export logger_name=asyncy
    export loggger_level=warning

Testing
-------
To run the engine in a testing environment:

1. Install the engine in a virtualenv
2. Set testing environment variables:
    - ``export mongo=mongodb://localhost:27017/``
    - ``export broker=amqp://:@localhost:5672/``
    - ``export api_url=localhost``
2. Start celery with ``celery worker -A asyncy.CeleryTasks -E ``
3. Start a mock http server that answers to GET requests against http://localhost/apps/:app_id/stories/:story_name with a mock, but valid JSON story document
4. Run ``asyncy run story_name app_id`` to run the story
