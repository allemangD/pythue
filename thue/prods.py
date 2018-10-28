import re

import thue.parser


class Context:
    def __init__(self, string, match=None):
        if match is None:
            match = re.match(r'^.*$', string)

        self.string = string
        self.match = match

    def enter(self):
        return Context(self.string, self.match)

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


class Literal:
    def __init__(self, fmt):
        self.fmt = fmt

    def apply(self, ctx):
        ctx_ = ctx.enter()
        ctx_.expand(self.fmt)
        return ctx.exit(ctx_)

    def __str__(self):
        return f'Literal[{self.fmt}]'


class Full:
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def apply(self, ctx):
        ctx_ = ctx.enter()
        self.lhs.apply(ctx_)
        self.rhs.apply(ctx_)
        return ctx.exit(ctx_)

    def __str__(self):
        return f'Full[{self.lhs} => {self.rhs}]'


class Partial:
    def __init__(self, reg, rhs):
        self.reg = reg
        self.pat = re.compile(reg)
        self.rhs = rhs

    def apply(self, ctx):
        match = self.pat.search(ctx.string)

        if match:
            inner = Context(match[0], match)
            self.rhs.apply(inner)
            inner.string = ctx.string[:match.start()] + inner.string + ctx.string[match.end():]
            return ctx.exit(inner)

        return False

    def __str__(self):
        return f'Part[{self.reg} ::= {self.rhs}]'


class Input:
    def apply(self, ctx):
        ctx_ = ctx.enter()
        ctx_.string = input()
        ctx_.match = thue.parser.ALL_PAT.match(ctx_.string)
        return ctx.exit(ctx_)

    def __str__(self):
        return 'Input'


class Output:
    def __init__(self, prod):
        self.prod = prod

    def apply(self, ctx):
        _ctx = ctx.enter()
        self.prod.apply(_ctx)
        print(_ctx.string)
        return False

    def __str__(self):
        return f'Output[{self.prod}]'


class Suite:
    def __init__(self, prods, ctx=None):
        if ctx is None:
            ctx = Context('')

        self.prods = prods
        self.ctx = ctx

    def apply(self, ctx):
        ctx_ = ctx.enter()
        for prod in self.prods:
            if prod.apply(ctx_):
                break
        return ctx.exit(ctx_)

    def __str__(self):
        prod_list = ' '.join(map(str, self.prods))
        return f'Suite[{prod_list}]'


class Continual:
    def __init__(self, suite):
        self.suite = suite

    def apply(self, ctx):
        res = False
        while self.suite.apply(ctx):
            res = True
        return res

    def __str__(self):
        return f'Continual[{self.suite}]'


class Singular:
    def __init__(self, suite):
        self.suite = suite

    def apply(self, ctx):
        self.suite.apply(ctx)

    def __str__(self):
        return f'Singular[{self.suite}]'


class Program:
    def __init__(self, suite):
        self.suite = suite

    def run(self, init=''):
        ctx = Context(init)
        self.suite.apply(ctx)
        return ctx.string

    def __str__(self):
        return f'Program[{self.suite}]'
