[![FOSSA Status](https://app.fossa.io/api/projects/git%2Bgithub.com%2Fasyncy%2Fplatform-engine.svg?type=shield)](https://app.fossa.io/projects/git%2Bgithub.com%2Fasyncy%2Fplatform-engine?ref=badge_shield)

# Storyscript Cloud Runtime
The Storyscript runtime powering the Storyscript Cloud and executing stories.


## Installing
See https://github.com/storyscript/stack-compose to install in production.

```
$ python setup.py install
```

## Testing

1. Compile assets required for the engine
2. Set the ASSET_DIR environment variable to this dir
3. Start the engine

```
$ asyncy-server start
```

## Configuration options
The engine loads its configuration options from the environment. Defaults are
provided:

```
$ export logger_name=asyncy
$ export loggger_level=debug
```

## License
[![FOSSA Status](https://app.fossa.io/api/projects/git%2Bgithub.com%2Fasyncy%2Fplatform-engine.svg?type=large)](https://app.fossa.io/projects/git%2Bgithub.com%2Fasyncy%2Fplatform-engine?ref=badge_large)
