Asyncy
#########
The engine powering Asyncy


Installing
-----------

You can install asyncy from pip::

    pip install asyncy


After that, you might want to configure it. Asyncy loads variables from
the environment, so all you need to do is to export the options::

    export database=postgresql://postgres:postgres@localhost:5432/database
    export mongo=mongodb://localhost:27017/
    export broker=amqp://:@localhost:5672/
    export github.pem_path=github.pem
    export github.app_identifier=123456789

Starting the server::

    celery worker -A asyncy.CeleryTasks


Processing stories::

    from asyncy.CeleryTasks import run

    run.delay('app_id', 'story_name', story_id=None)
