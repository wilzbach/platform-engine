# -*- coding: utf-8 -*-
import re


class RegExpUtils:

    @staticmethod
    def process_flags(flags):
        assert all(x in 'ims' for x in flags), \
            f'Invalid flag combination: `{flags}`'
        re_flags = 0

        if 'i' in flags:
            re_flags |= re.I
        if 'm' in flags:
            re_flags |= re.M
        if 's' in flags:
            re_flags |= re.S

        return re_flags
