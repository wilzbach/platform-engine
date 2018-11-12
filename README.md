Asyncy platform engine
----------------------
The engine powering Asyncy and executing stories.


Developing
-----------
The engine typically runs as a Pod in Kubernetes. However, during local development, it might be useful to run it directly, outside of Kubernetes.

To be able to do so, follow these instructions:

1. Create and seed the `asyncy` database by following [this](https://github.com/asyncy/database)
2. Create a virtualenv
    1. `$ virtualenv --python=python3.6 platform-engine/venv`
    2. `$ cd platform-engine`
    3. `$ source venv/bin/activate`
2. Install the Storyscript compiler
    - `pip install storyscript`
2. Compile the `hello world` story:
    1. `$ curl https://raw.githubusercontent.com/asyncy/examples/master/hello-world.story > hello.story`
    2. `storyscript compile -j hello.story | awk '{ printf "%s", $0 }'`
        - The `awk` usage above is only to remove the new lines outputted by the compiler
    3. The expected output should look like `{"stories":{"hello.story":{"tree":{"1":{"method":"execute","ln":"1","output":[],"name":null,"service":"log","command":"info","function":null,"args":[{"$OBJECT":"argument","name":"msg","argument":{"$OBJECT":"string","string":"Helloworld!"}}],"enter":null,"exit":null,"parent":null}},"services":["log"],"entrypoint":"1","modules":{},"functions":{},"version":"0.6.0"}},"services":["log"],"entrypoint":["hello.story"]}`
2. Create a release manually in the database using the compiled output above
```
$ psql asyncy
psql (10.5)
Type "help" for help.

asyncy=# set search_path to app_public,app_private,app_hidden,app_runtime;
SET
asyncy=# INSERT INTO releases (app_uuid, config, message, owner_uuid, payload) VALUES ('e9e97287-3aac-44df-a5e0-67aa42f00429', '{}', 'Test release', 'eb0c25d8-5b5a-43f6-81b4-1a3880243c96', '{"stories":{"hello.story":{"tree":{"1":{"method":"execute","ln":"1","output":[],"name":null,"service":"log","command":"info","function":null,"args":[{"$OBJECT":"argument","name":"msg","argument":{"$OBJECT":"string","string":"Helloworld!"}}],"enter":null,"exit":null,"parent":null}},"services":["log"],"entrypoint":"1","modules":{},"functions":{},"version":"0.6.0"}},"services":["log"],"entrypoint":["hello.story"]}');
INSERT 0 1
asyncy=# \q
```
3. Start the engine
    1. `$ export POSTGRES="options=--search_path=app_public,app_hidden,app_private,public dbname=asyncy user=postgres"`
    2. `$ python setup.py install` (execute this inside platform-engine)
    3. `$ asyncy-server start`
    



Testing
----------------
1. Compile assets required for the engine
2. Set the ASSET_DIR environment variable to this dir
3. Start the engine

    asyncy-server start


Configuration options
----------------------
The engine loads its configuration options from the environment. Defaults are
provided:

    export logger_name=asyncy
    export loggger_level=debug
