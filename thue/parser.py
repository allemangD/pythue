import re

import lark
from lark import Lark

import thue.core
import thue.prods

grammar = r'''
program: suite

suite: prod*

?prod: _named_prod | _direct_prod

_named_prod     : alias
_direct_prod    : _compound_prod | _rule_prod | _literal_prod | _io_prod
_io_prod  : output | input
_compound_prod  : cont | sing
_rule_prod      : full | part
_literal_prod   : lit | ref

alias : name "=" prod               // production alias
output: "~" prod                    // output production
input: ":::"                        // input production

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

STRING_PAT = re.compile(r'''(r)?(['"])(.*?)(?<!\\)\2''')
REGEX_PAT = re.compile(r'''(r)?([/])(.*?)(?<!\\)\2(i)?''')
ALL_PAT = re.compile(r'''^.*$''')


class ProductionTransformer(lark.Transformer):
    def suite(self, prods):
        return thue.prods.Suite(prods)

    def lit(self, prods):
        fmt, = prods
        match = STRING_PAT.match(fmt)
        return thue.prods.Literal(match[3])

    def ctx(self, prods):
        reg, = prods
        match = REGEX_PAT.match(reg)
        return re.compile(match[3])

    def input(self, prods):
        return thue.prods.Input()

    def output(self, prods):
        prod, = prods
        return thue.prods.Output(prod)

    def full(self, prods):
        lhs, rhs = prods
        return thue.prods.Full(lhs, rhs)

    def part(self, prods):
        pat, rhs = prods
        return thue.prods.Partial(pat, rhs)

    def cont(self, prods):
        suite, = prods
        return thue.prods.Continual(suite)

    def sing(self, prods):
        suite, = prods
        return thue.prods.Singular(suite)

    def program(self, prods):
        suite, = prods
        return thue.core.Program(suite)


THUE_TRANSFORMER = ProductionTransformer()
THUE_LARK = Lark(grammar, start='program')


def compile(src):
    tree = THUE_LARK.parse(src)
    pgm = THUE_TRANSFORMER.transform(tree)
    return pgm
