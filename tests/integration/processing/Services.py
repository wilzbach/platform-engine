from pytest import mark

from tests.integration.processing.Entities import Case, Suite

from .Assertions import ContextAssertion


@mark.parametrize(
    "suite",
    [
        Suite(
            preparation_lines='a = json stringify content: {"a": "b"}',
            cases=[
                Case(
                    assertion=ContextAssertion(key="a", expected='{"a": "b"}')
                )
            ],
        ),
        Suite(
            preparation_lines="a = json stringify content: [1, 2, 3]",
            cases=[
                Case(assertion=ContextAssertion(key="a", expected="[1, 2, 3]"))
            ],
        ),
    ],
)
@mark.asyncio
async def test_json_service(suite: Suite, logger, run_suite):
    await run_suite(suite, logger)


@mark.parametrize(
    "suite",
    [
        Suite(
            preparation_lines='a = http fetch url: "https://www.google.com/"\n'
            "passed = true",
            cases=[
                Case(assertion=ContextAssertion(key="passed", expected=True))
            ],
        ),
        Suite(
            preparation_lines="a = http fetch "
            'url: "https://jsonplaceholder.'
            'typicode.com/todos/1"\n'
            "passed = true",
            cases=[
                Case(assertion=ContextAssertion(key="passed", expected=True))
            ],
        ),
    ],
)
@mark.asyncio
async def test_http_service(suite: Suite, logger, run_suite):
    await run_suite(suite, logger)


@mark.parametrize(
    "suite",
    [
        Suite(
            preparation_lines='exists = file exists path: "file"',
            cases=[
                Case(assertion=ContextAssertion(key="exists", expected=False))
            ],
        ),
        Suite(
            preparation_lines='file mkdir path: "file"\n'
            'exists = file exists path: "file"',
            cases=[
                Case(assertion=ContextAssertion(key="exists", expected=True))
            ],
        ),
        Suite(
            preparation_lines='file mkdir path: "/file"\n'
            'exists = file exists path: "file"',
            cases=[
                Case(assertion=ContextAssertion(key="exists", expected=True))
            ],
        ),
        Suite(
            preparation_lines='file mkdir path: "file"\n'
            'exists = file exists path: "/file"',
            cases=[
                Case(assertion=ContextAssertion(key="exists", expected=True))
            ],
        ),
        Suite(
            preparation_lines='file write path: "file" '
            'content: "hello world"\n'
            'exists = file exists path: "file"',
            cases=[
                Case(assertion=ContextAssertion(key="exists", expected=True))
            ],
        ),
        Suite(
            preparation_lines='file mkdir path: "file"\n'
            'exists = file exists path: "file"',
            cases=[
                Case(assertion=ContextAssertion(key="exists", expected=True))
            ],
        ),
        Suite(
            preparation_lines='file mkdir path: "file"\n'
            'isDir = file isDir path: "file"',
            cases=[
                Case(assertion=ContextAssertion(key="isDir", expected=True))
            ],
        ),
        Suite(
            preparation_lines='file write path: "file" content: "file"\n'
            'file mkdir path: "path"\n'
            "files = file list\n",
            cases=[
                Case(
                    assertion=ContextAssertion(
                        key="files", expected=["/file", "/path"]
                    )
                )
            ],
        ),
        Suite(
            preparation_lines='file write path: "file" content: "file"\n'
            'file mkdir path: "path/anotherdir"\n'
            "files = file list\n",
            cases=[
                Case(
                    assertion=ContextAssertion(
                        key="files", expected=["/file", "/path"]
                    )
                )
            ],
        ),
        Suite(
            preparation_lines='file write path: "file" content: "file"\n'
            'file mkdir path: "path/anotherdir"\n'
            "files = file list recursive: true\n",
            cases=[
                Case(
                    assertion=ContextAssertion(
                        key="files",
                        expected=["/file", "/path", "/path/anotherdir"],
                    )
                )
            ],
        ),
        Suite(
            preparation_lines='file write path: "file" content: "file"\n'
            'file mkdir path: "path/anotherdir"\n'
            'file write path: "/path/anotherdir/file" '
            'content: "file"\n'
            "files = file list recursive: true\n",
            cases=[
                Case(
                    assertion=ContextAssertion(
                        key="files",
                        expected=[
                            "/file",
                            "/path",
                            "/path/anotherdir",
                            "/path/anotherdir/file",
                        ],
                    )
                )
            ],
        ),
        Suite(
            preparation_lines='file write path: "file" content: "file"\n'
            'isDir = file isDir path: "file"',
            cases=[
                Case(assertion=ContextAssertion(key="isDir", expected=False))
            ],
        ),
        Suite(
            preparation_lines='file write path: "file" content: "file"\n'
            'isFile = file isFile path: "file"',
            cases=[
                Case(assertion=ContextAssertion(key="isFile", expected=True))
            ],
        ),
        Suite(
            preparation_lines='file mkdir path: "file"\n'
            'isFile = file isFile path: "file"',
            cases=[
                Case(assertion=ContextAssertion(key="isFile", expected=False))
            ],
        ),
        Suite(
            preparation_lines='file write path: "file" content: "file"\n'
            'data = file read path: "file"',
            cases=[
                Case(assertion=ContextAssertion(key="data", expected="file"))
            ],
        ),
        Suite(
            preparation_lines='file mkdir path: "/file/data"\n'
            'data = file isDir path: "file"',
            cases=[
                Case(assertion=ContextAssertion(key="data", expected=True))
            ],
        ),
        Suite(
            preparation_lines='file write path: "file" binary: true '
            'content: "hello world"\n'
            'data = file read path: "file" binary: true',
            cases=[
                Case(
                    assertion=ContextAssertion(
                        key="data", expected=b"hello world"
                    )
                )
            ],
        ),
        Suite(
            preparation_lines='file write path: "file" binary: true '
            'content: "hello world"\n'
            'data = file read path: "file" binary: false',
            cases=[
                Case(
                    assertion=ContextAssertion(
                        key="data", expected="hello world"
                    )
                )
            ],
        ),
        Suite(
            preparation_lines='file write path: "file" binary: false '
            'content: "hello world"\n'
            'data = file read path: "file" binary: true',
            cases=[
                Case(
                    assertion=ContextAssertion(
                        key="data", expected=b"hello world"
                    )
                )
            ],
        ),
    ],
)
@mark.asyncio
async def test_file_service(suite: Suite, logger, run_suite):
    await run_suite(suite, logger)
