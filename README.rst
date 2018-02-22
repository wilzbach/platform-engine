Asyncy platform engine
#######################
The engine powering Asyncy and executing stories.


Installing
-----------
As this is a platform, you would not normally instally it on your machine or
server, except for development of if you wish to run Asyncy on premises.
To install the engine you will need:

- PostgreSQL
- MongoDB
- Celery
- A Github application

1. Create a database in postgres and export its url::

    export database=postgresql://postgres:postgres@localhost:5432/database

2. From mongo, do the following::

    use asyncy
    db.createCollection('lines')
    db.createCollection('stories')
    db.createCollection('narrations')

2. Create a Github Application that has read permission on repositories
   contents. Generate a pem key, then export the application name, the path to
   the pem file and the application id::

    export github.app_name=myapp
    export github.pem_path=github.pem
    export github.app_identifier=123456789

3. Install asyncy from pip::

    pip install asyncy

4. Execute the install command::

    asyncy install

5. Start celery::

    celery worker -A asyncy.CeleryTasks

6. The engine is installed! If you want to run a story, keep reading.


Running a story
----------------
Asyncy loads stories from Github repositories, so if you want to run stories,
you need to configure a repository


1. Create a repository and push a story::

    # hello.story
    alpine echo "hello world"


2. Create an asyncy.yml file, which can be empty
3. Install the application previously created in the repo
4. Populate postgres with an user, an application, a repository and a story::

    insert into users (name, email, github_handle, installation_id) values ('user', 'user@asyncy.com', 'handle', 12345);
    insert into applications (name, user_id) values ('app', 1);
    insert into repositories (name, organization, owner_id) values ('repository_name', 'user_handle', 1);
    insert into stories (filename, repository_id) values ('hello.story', 1);
    insert into applicationsstories (application_id, story_id) values (1, 1);

5. Run the story::

    #!/usr/bin/env python3
    from asyncy.CeleryTasks import process_story

    process_story.delay(1, 'hello.story')


Configuration options
----------------------
::

    export database=postgresql://postgres:postgres@localhost:5432/database
    export mongo=mongodb://localhost:27017/
    export broker=amqp://:@localhost:5672/
    export loggger.verbosity=1
    export github.app_name=myapp
    export github.pem_path=github.pem
    export github.app_identifier=123456789
