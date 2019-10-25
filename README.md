[![CircleCI](https://img.shields.io/circleci/project/github/storyscript/runtime/master.svg?style=for-the-badge)](https://circleci.com/gh/storyscript/runtime)
[![Codecov](https://img.shields.io/codecov/c/github/storyscript/runtime.svg?style=for-the-badge)](https://codecov.io/github/storyscript/runtime)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge)](https://github.com/psf/black)
[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-v1.4%20adopted-ff69b4.svg?style=for-the-badge)](https://github.com/storyscript/.github/blob/master/CODE_OF_CONDUCT.md)

[![FOSSA Status](https://app.fossa.io/api/projects/git%2Bgithub.com%2Fasyncy%2Fplatform-engine.svg?type=small)](https://app.fossa.io/projects/git%2Bgithub.com%2Fasyncy%2Fplatform-engine?ref=badge_shield)

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
$ export logger_name=storyscript
$ export logger_level=debug
```

## License

[![FOSSA Status](https://app.fossa.io/api/projects/git%2Bgithub.com%2Fasyncy%2Fplatform-engine.svg?type=large)](https://app.fossa.io/projects/git%2Bgithub.com%2Fasyncy%2Fplatform-engine?ref=badge_large)
