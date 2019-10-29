[![CircleCI](https://img.shields.io/circleci/project/github/storyscript/runtime/master.svg?style=for-the-badge)](https://circleci.com/gh/storyscript/runtime)
[![Codecov](https://img.shields.io/codecov/c/github/storyscript/runtime.svg?style=for-the-badge)](https://codecov.io/github/storyscript/runtime)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge)](https://github.com/psf/black)
[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-v1.4%20adopted-ff69b4.svg?style=for-the-badge)](https://github.com/storyscript/.github/blob/master/CODE_OF_CONDUCT.md)

[![FOSSA Status](https://app.fossa.io/api/projects/git%2Bgithub.com%2Fasyncy%2Fplatform-engine.svg?type=small)](https://app.fossa.io/projects/git%2Bgithub.com%2Fasyncy%2Fplatform-engine?ref=badge_shield)

# Storyscript Cloud Runtime

The runtime powering Storyscript Cloud and executing stories.

## Setup

- Install dependencies
```bash
$ pip install -e ".[pytest,stylecheck]"
```

- Run tests
```bash
$ pytest
```

- Populate [environment variables](https://github.com/storyscript/runtime/blob/master/storyruntime/Config.py) and start!
```bash
$ storyscript-server start
```

See https://github.com/storyscript/stack-compose to install in production.

## Contributing
- Install [pre-commit](https://pre-commit.com/#install) and set up the git hook scripts
```bash
$ pip install --user pre-commit
$ pre-commit install
```
- Pin exact dependencies in `requirements.txt` after any changes to `setup.py`
```bash
$ pip-compile                        # available in the pip-tools package
```

## License

[![FOSSA Status](https://app.fossa.io/api/projects/git%2Bgithub.com%2Fasyncy%2Fplatform-engine.svg?type=large)](https://app.fossa.io/projects/git%2Bgithub.com%2Fasyncy%2Fplatform-engine?ref=badge_large)
