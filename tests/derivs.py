#!/usr/bin/env python3

import sys
from os import readlink
from os.path import islink, dirname, abspath
from lark import Lark

self_path = abspath(dirname(readlink(__file__) if islink(__file__) else __file__))
sys.path.insert(0, abspath(f"{self_path}/.."))

from config import vamos_common_PYTHONPATH
sys.path.append(vamos_common_PYTHONPATH)

from parser.ast import ProcessPE

PATTERNS = [
    ("a + b", ["a"], "ε"),
    ("b + b", ["a"], "⊥"),
    ("{a + a}.a", ["a"], "a"),
    ("a*b", ["a"], "a*b"),
    ("b*a", ["a"], "ε"),
    ("b*c", ["a"], "⊥"),
    ("{{a*b}*c}*d", ["a"], "{{a*b.{a*b}*c}.{{a*b}*c}*d}"),
    ("{{a*b}*c}*d", ["a", "b"], "{{a*b}*c.{{a*b}*c}*d}"),
    ("{{a*b}*c}*d", ["a", "b", "a"], "{{a*b.{a*b}*c}.{{a*b}*c}*d}"),
    ("{{a*b}*c}*d", ["a", "b", "b"], "{{a*b}*c.{{a*b}*c}*d}"),
    ("{{a*b}*c}*d", ["a", "b", "c"], "{{a*b}*c}*d"),
    ("{{a*b}*c}*d", ["a", "b", "c", "c"], "{{a*b}*c}*d"),
    ("{{a*b}*c}*d", ["a", "b", "c", "d"], "ε"),
    ("a.b + b.a", ["a"], "b"),
    ("a.b + b.a", ["a", "b"], "ε"),
    ("a*b + b.a + a.b + c", ["a", "b"], "ε"),
    ("a*b + b.a + a.b + c", ["a", "a"], "a*b"),
    ("l1@{a*b} + l2@{b.a} + l3@{a.b} + l4@c", ["a", "a"], "l1'@{a*b}"),
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


def parse(s):
    t = parser.parse(s)
    return ProcessPE().transform(t)


for n, pattern in enumerate(PATTERNS):
    out = parse(pattern[0])
    letters = [parse(s) for s in pattern[1]]
    d = out
    history = [d.pretty_str()]
    for l in letters:
        d = d.derivation(l)
        history.append(d.pretty_str())
    d = d.pretty_str()
    print(f"{''.join(pattern[1])}/({pattern[0]}) = ", d)
    if d != pattern[2]:
        print(f"  -- Wrong output of derivation {n}")
        print(f"  Expression: {pattern[0]}")
        print(f"  Letters: {''.join(pattern[1])}")
        print(f"  Derivation: {d}")
        print(f"  History: {' -> '.join(history)}")
        print(f"  Expected: {pattern[2]}")
        exitval = 1

print(f"Tested {n+1} patterns")
exit(exitval)
