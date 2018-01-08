Evenflow
#########

I needed a name and I was listening to Pearl Jam :)


Installing
-----------

You can install evenflow from pip::

    pip install evenflow


After that, you might want to configure it. Evenflow loads variables from
the environment, so all you need to do is to export the options::

    export database=postgresql://postgres:postgres@localhost:5432/database
    export mongo=mongodb://localhost:27017/
    export broker=amqp://:@localhost:5672/
    export github.pem_path=github.pem
    export github.app_identifier=123456789

Starting the server::

    celery worker -A evenflow.CeleryTasks


Processing stories::

    from evenflow.CeleryTasks import run

    run.delay('app_id', 'story_name', story_id=None)
