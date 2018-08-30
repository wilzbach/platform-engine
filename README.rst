Asyncy platform engine
#######################
The engine powering Asyncy and executing stories.


Installing
-----------
See https://github.com/asyncy/stack-compose to install in production.


    python setup.py install


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
