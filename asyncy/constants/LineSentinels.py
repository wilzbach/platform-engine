# -*- coding: utf-8 -*-


class _Sentinel:
    def __init__(self, keyword):
        self.keyword = keyword

    def __str__(self):
        return f'_Sentinel#{self.keyword}'


class ReturnSentinel(_Sentinel):
    def __init__(self, return_value: any):
        super().__init__('return')
        self.return_value = return_value


class LineSentinels:
    """
    A collection for all sentinels, which are used as special line numbers
    during the execution of certain constructs, such as foreach, return, etc.

    How sentinels are used:
    During the flow of execution, they will almost always break
    the normal flow of execution in some manner. For example,
    Lexicon.for_loop calls Stories.execute_block in order to execute the same
    block multiple times. When Stories.execute_block returns the BREAK
    sentinel, Lexicon.for_loop knows that it's time to stop looping.

    Sentinels are used to control the flow of execution. The other approach
    was to start throwing exceptions during execution, but that is a horrible,
    horrible idea because:
    1. Incurs a runtime performance hit
    2. It's an exception, which is not what it was designed to do
    """
    BREAK = _Sentinel('break')
    CONTINUE = _Sentinel('continue')
    RETURN = ReturnSentinel(None)

    @staticmethod
    def is_sentinel(result):
        return isinstance(result, _Sentinel)

    @staticmethod
    def is_not_sentinel(result):
        return not LineSentinels.is_sentinel(result)
