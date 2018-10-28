import re

import thue.core


class Literal(thue.core.Production):
    def __init__(self, fmt):
        self.fmt = fmt
        self.fields = fmt,

    def apply_local(self, local):
        local.expand(self.fmt)


class Full(thue.core.Production):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs
        self.fields = (lhs, '=>', rhs)

    def apply_local(self, local):
        self.lhs.apply(local)
        self.rhs.apply(local)


class Partial(thue.core.Production):
    def __init__(self, reg, rhs):
        self.reg = reg
        self.pat = re.compile(reg)
        self.rhs = rhs
        self.fields = reg, '::=', rhs

    def apply_local(self, local):
        match = self.pat.search(local.string)
        if not match:
            return

        sub = thue.core.Context(match[0], match)
        self.rhs.apply(sub)

        local.string = local.string[:match.start()] + sub.string + local.string[match.end():]


class Input(thue.core.Production):
    def apply_local(self, local):
        local.set(input())


class Output(thue.core.Production):
    def __init__(self, prod):
        self.prod = prod
        self.fields = prod,

    def apply(self, ctx):
        local = ctx.enter()
        self.prod.apply(local)
        print(local.string)


class Continual(thue.core.Production):
    def __init__(self, prod):
        self.prod = prod
        self.fields = prod,

    def apply_local(self, local):
        while self.prod.apply(local):
            pass


class Suite(thue.core.Production):
    def __init__(self, prods):
        self.prods = prods
        self.fields = prods

    def apply_local(self, local):
        for prod in self.prods:
            if prod.apply(local):
                break


class Singular(thue.core.Production):
    def __init__(self, prod):
        self.prod = prod

        self.fields = prod,

    def apply_local(self, local):
        self.prod.apply(local)
