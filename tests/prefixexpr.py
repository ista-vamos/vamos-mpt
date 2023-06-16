#!/usr/bin/env python3

import sys
from os import readlink
from os.path import islink, dirname, abspath
from lark import Lark

self_path = abspath(dirname(readlink(__file__) if islink(__file__) else __file__))
sys.path.insert(0, abspath(f"{self_path}/.."))

from parser.ast import ProcessPE, visit_ast

PATTERNS = [
    ("a + b", "Choice(EventVar(ID(a)) + EventVar(ID(b)))"),
    (
        "c + {a + b}",
        "Choice(EventVar(ID(c)) + Choice(EventVar(ID(a)) + EventVar(ID(b))))",
    ),
    (
        "{c + a} + b",
        "Choice(Choice(EventVar(ID(c)) + EventVar(ID(a))) + EventVar(ID(b)))",
    ),
    (
        "{c + {a + d}} + b",
        "Choice(Choice(EventVar(ID(c)) + Choice(EventVar(ID(a)) + EventVar(ID(d)))) + EventVar(ID(b)))",
    ),
    ("{b + c}*a", "Star(Choice(EventVar(ID(b)) + EventVar(ID(c))), EventVar(ID(a)))"),
    (
        "{b*c + d}*a",
        "Star(Choice(Star(EventVar(ID(b)), EventVar(ID(c))) + EventVar(ID(d))), EventVar(ID(a)))",
    ),
    (
        "{{a.b}*c + d}*a",
        "Star(Choice(Star(Seq(EventVar(ID(a)).EventVar(ID(b))), EventVar(ID(c))) + EventVar(ID(d))), EventVar(ID(a)))",
    ),
    (
        "{{a b}*c + d}*a",
        "Star(Choice(Star(Seq(EventVar(ID(a)).EventVar(ID(b))), EventVar(ID(c))) + EventVar(ID(d))), EventVar(ID(a)))",
    ),
    (
        "{a b*c + d}*a",
        "Star(Choice(Star(Seq(EventVar(ID(a)).EventVar(ID(b))), EventVar(ID(c))) + EventVar(ID(d))), EventVar(ID(a)))",
    ),
    (
        "{a {b*c} + d}*a",
        "Star(Choice(Seq(EventVar(ID(a)).Star(EventVar(ID(b)), EventVar(ID(c)))) + EventVar(ID(d))), EventVar(ID(a)))",
    ),
    ("e@b", "NamedGroup(ID(e), EventVar(ID(b)))"),
    ("e1@b", "NamedGroup(ID(e1), EventVar(ID(b)))"),
    ("e@{b}", "NamedGroup(ID(e), EventVar(ID(b)))"),
    ("e@{b + c}", "NamedGroup(ID(e), Choice(EventVar(ID(b)) + EventVar(ID(c))))"),
    (
        "e@{b + c}*a",
        "Star(NamedGroup(ID(e), Choice(EventVar(ID(b)) + EventVar(ID(c)))), EventVar(ID(a)))",
    ),
    (
        "e@{{b + c}*a}",
        "NamedGroup(ID(e), Star(Choice(EventVar(ID(b)) + EventVar(ID(c))), EventVar(ID(a))))",
    ),
    (
        "_*e1@{a + b}",
        "Star(Atom(ANY), NamedGroup(ID(e1), Choice(EventVar(ID(a)) + EventVar(ID(b)))))",
    ),
    ("e@b(x)", "NamedGroup(ID(e), Event(ID(b): ID(x)))"),
    ("e@b(x, y)", "NamedGroup(ID(e), Event(ID(b): ID(x), ID(y)))"),
]

grammars_dir = abspath(f"{self_path}/../parser/grammars/")
parser = Lark.open(
    "prefixexpr.lark",
    rel_to=f"{grammars_dir}/grammar.lark",
    import_paths=[grammars_dir],
    start="prefixexpr",
)

exitval = 0
n = 0
for n, pattern in enumerate(PATTERNS):
    t = parser.parse(pattern[0])
    out = str(ProcessPE().transform(t))
    if out != pattern[1]:
        print(f"-- Wrong output for pattern {n}")
        print(f"Pattern: {pattern[0]}")
        print(f"Got     : {out}")
        print(f"Expected: {pattern[1]}")
        exitval = 1

print(f"Tested {n} patterns")
exit(exitval)
