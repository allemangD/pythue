import re

import thue.parser


class Context:
    def __init__(self, string, match=None):
        self.string = self.match = None
        self.set(string, match)

    def enter(self):
        return Context(self.string, self.match)

    def set(self, string, match=None):
        if match is None:
            match = re.match(r'^.*$', string)
        self.string = string
        self.match = match

    def exit(self, ctx):
        diff = self.string != ctx.string
        self.string = ctx.string
        self.match = ctx.match
        return diff

    def expand(self, fmt):
        self.match = thue.parser.ALL_PAT.match(self.string)
        self.string = self.match.expand(fmt)

    def __str__(self):
        return f'Ctx[{self.string!r} {self.match[0]!r} {self.match.groups()}]'


class Production:
    fields = ()

    def apply_local(self, local):
        pass

    def apply(self, ctx):
        local = ctx.enter()
        self.apply_local(local)
        return ctx.exit(local)

    def __str__(self):
        field_list = ' '.join(map(str, self.fields))
        return f'{type(self)}[{field_list}]'


class Program(Production):
    def __init__(self, prod):
        self.prod = prod
        self.fields = prod,

    def apply_local(self, local):
        self.prod.apply(local)

    def run(self, init=''):
        ctx = Context(init)
        self.prod.apply(ctx)
        return ctx.string