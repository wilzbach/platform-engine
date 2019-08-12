# -*- coding: utf-8 -*-
class Assertion:
    key: str

    def __init__(self, key):
        self.key = key

    def verify(self, context):
        # Must be implemented by the child.
        pass


class ContextAssertion(Assertion):
    expected: str

    def __init__(self, key, expected):
        super().__init__(key)
        self.expected = expected

    def verify(self, context):
        assert context.get(self.key) == self.expected


class ListItemAssertion(ContextAssertion):
    index: int

    def __init__(self, key, index, expected):
        super().__init__(key, expected)
        self.index = index

    def verify(self, context):
        assert isinstance(context[self.key], list)
        assert context[self.key][self.index] == self.expected


class MapValueAssertion(ContextAssertion):
    map_key: any

    def __init__(self, key, map_key, expected):
        super().__init__(key, expected)
        self.map_key = map_key

    def verify(self, context):
        assert isinstance(context[self.key], dict)
        assert context[self.key][self.map_key] == self.expected


class IsANumberAssertion(Assertion):
    def __init__(self, key):
        super().__init__(key)

    def verify(self, context):
        val = context[self.key]
        assert type(val) == int or type(val) == float


class RuntimeExceptionAssertion():

    def __init__(self, exception_type, context_assertion=None,
                 **fields_to_check):
        self.exception_type = exception_type
        self.context_assertion = context_assertion
        self.fields_to_check = fields_to_check

    def verify(self, exception, context):
        assert isinstance(exception, self.exception_type), str(exception)
        for k, v in self.fields_to_check.items():
            attr = getattr(exception, k)
            assert attr == v

        if self.context_assertion is not None and \
                context is not None:
            assert isinstance(self.context_assertion, ContextAssertion)
            self.context_assertion.verify(context)
