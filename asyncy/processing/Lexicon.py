# -*- coding: utf-8 -*-


class Lexicon:

    @staticmethod
    def if_condition(line, args):
        if args[0]:
            return line['enter']
        return line['exit']

    @staticmethod
    def unless_condition(line, args):
        if args[0]:
            return line['exit']
        return line['enter']

    @staticmethod
    def next(command):
        if command.endswith('.story'):
            return command
        return '{}.story'.format(command)
