#!/usr/bin/env python3

import sys
from os import readlink
from os.path import islink, dirname, abspath
from lark import Lark

self_path = abspath(dirname(readlink(__file__) if islink(__file__) else __file__))
sys.path.insert(0, abspath(f"{self_path}/.."))

from parser.ast import ProcessPE, visit_ast
from mpt.pe import PrefixExpressionTransducer

PATTERNS = [
    ("a + b", ["a", "b"], ["aa", "ab", "c"]),
    ("a*b", ["b", "ab", "aab", "aaaaaab"], ["aa", "ba", "bb", "c"]),
    ("a.{a*b}", ["aab", "ab"], ["a", "aa", "aaa", "ac", "b"]),
    ("a.{a*b}.b", ["abb", "aabb"], ["ab", "aaab", "aca", "aaaaab"]),
    ("{a*b}*c", ["abc"], []),
    ("{{a*b}*c}*d", ["abcd"], []),
    ("{{{a + b}*b}*{c + b}}*{d + e}", ["d", "e", "ce"], []),
]

grammars_dir = abspath(f"{self_path}/../parser/grammars/")
parser = Lark.open(
    "prefixexpr.lark",
    rel_to=f"{grammars_dir}/grammar.lark",
    import_paths=[grammars_dir],
    start="prefixexpr",
)

def parse(s):
    t = parser.parse(s)
    return ProcessPE().transform(t)

exitval = 0
n = 0
for n, pattern in enumerate(PATTERNS):
    pe = parse(pattern[0])
    pet = PrefixExpressionTransducer.from_pe(pe)
    for word in pattern[1]:
        atoms = [parse(l) for l in word]
        if not pet.accepts(atoms):
            print("---", pattern[0], "---")
            pet.dump()
            print("------")
            print("Should accept: ", word)
            print(f"Trajectory: {pet.trajectory(atoms)}")
            print("------")
    for word in pattern[2]:
        atoms = [parse(l) for l in word]
        if pet.accepts(atoms):
            print("---", pattern[0], "---")
            pet.dump()
            print("------")
            print("Should NOT accept: ", word)
            print(f"Trajectory: {pet.trajectory(atoms)}")
            print("------")




print(f"Tested {n+1} expressions")
exit(exitval)
