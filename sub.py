import re

from lark import Lark, InlineTransformer, Transformer

grammar = r'''
program: suite

suite: prod*

?prod: _named_prod | _direct_prod

_named_prod     : alias
_direct_prod    : _compound_prod | _rule_prod | _literal_prod | _abstract_prod
_abstract_prod  : output
_compound_prod  : cont | sing
_rule_prod      : full | part
_literal_prod   : lit | ref

alias : name "=" prod               // production alias
output: "~" prod                    // output production

cont  : "{" suite "}"               // continual production
sing  : "[" suite "]"               // singular production

full  : _direct_prod "=>" prod      // full application
part  : ctx "::=" prod              // partial application
ref   : name                        // production reference

lit   : STRING                      // literal production
name  : CNAME                       // named production

ctx   : REGEX

CNAME : /[a-z_][a-z0-9_]*/i
STRING: /(r)?(['"])(.*?)(?<!\\)\2/
REGEX : /(r)?([\/])(.*?)(?<!\\)\2(i)?/

%import common.WS
%ignore WS
'''


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
        self.string = self.match.expand(fmt)
        self.match = ALL_PAT.match(self.string)

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


STRING_PAT = re.compile(r'''(r)?(['"])(.*?)(?<!\\)\2''')
REGEX_PAT = re.compile(r'''(r)?([/])(.*?)(?<!\\)\2(i)?''')
ALL_PAT = re.compile(r'''^.*$''')


class ProductionTransformer(Transformer):
    def suite(self, prods):
        return Suite(prods)

    def lit(self, prods):
        fmt, = prods
        match = STRING_PAT.match(fmt)
        return Literal(match[3])

    def ctx(self, prods):
        reg, = prods
        match = REGEX_PAT.match(reg)
        return re.compile(match[3])

    def full(self, prods):
        lhs, rhs = prods
        return Full(lhs, rhs)

    def part(self, prods):
        pat, rhs = prods
        return Partial(pat, rhs)

    def cont(self, prods):
        suite, = prods
        return Continual(suite)

    def sing(self, prods):
        suite, = prods
        return Singular(suite)

    def program(self, prods):
        suite, = prods
        return Program(suite)


def main():
    lrk = Lark(grammar, start='program')

    with open('testing.ret') as f:
        src = f.read()

    tree = lrk.parse(src)
    print(tree.pretty())

    tform = ProductionTransformer()
    pgm = tform.transform(tree)
    print(pgm)
    print(pgm.run())


if __name__ == '__main__':
    main()
