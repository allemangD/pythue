from lark import Lark

grammar = r'''
suite: prod*

prod: _named_prod

_named_prod: _direct_prod | alias
_direct_prod: _compound_prod | _rule_prod | _literal_prod | _abstract_prod
_abstract_prod: output
_compound_prod: cont | sing
_rule_prod: full | part
_literal_prod: lit | ref

cont: "{" suite "}"             // continual production
sing: "[" suite "]"             // singular production

alias: ref "=" prod             // production alias
full: _direct_prod "=>" prod    // full application
part: ctx "::=" prod            // partial application

output: "~" prod

lit: STRING
ref: CNAME
ctx: REGEX

CNAME: /[a-z_][a-z0-9_]*/i
STRING: /(r)?(['"])(.*?)(?<!\\)\2/
REGEX: /(r)?([\/])(.*?)(?<!\\)\2(i)?/

%import common.WS
%ignore WS
'''


def main():
    lrk = Lark(grammar, start='suite')

    with open('sample.ret') as f:
        src = f.read()

    tree = lrk.parse(src)

    print(tree.pretty())


if __name__ == '__main__':
    main()
