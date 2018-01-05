Evenflow
#########

I needed a name and I was listening to Pearl Jam :)


Installing::

    pip install evenflow

Starting the server::

    celery worker -A evenflow.CeleryTasks


Processing stories::

    from evenflow.CeleryTasks import run

    run.delay('app_id', 'story_name', story_id=None)
