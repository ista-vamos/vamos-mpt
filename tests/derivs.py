#!/usr/bin/env python3

import sys
from os import readlink
from os.path import islink, dirname, abspath
from lark import Lark

self_path = abspath(dirname(readlink(__file__) if islink(__file__) else __file__))
sys.path.insert(0, abspath(f"{self_path}/.."))

from parser.ast import ProcessPE, visit_ast
from parser.prefixexpr import *
from parser.element import Identifier

PATTERNS = [
    ("a + b", "ε"),
    ("b + b", "⊥"),
    ("{a + a}.a", "a"),
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
    out = ProcessPE().transform(t)
    a = Atom(Identifier("a"))
    d = out.derivation(a).pretty_str()
    print(pattern[0], "->", d)
    if d != pattern[1]:
        print(f"  -- Wrong output of derivation {n}")
        print(f"  Pattern: {pattern[0]}")
        print(f"  Derivation: {d}")
        print(f"  Expected: {pattern[1]}")
        exitval = 1

print(f"Tested {n+1} patterns")
exit(exitval)
