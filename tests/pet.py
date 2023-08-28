#!/usr/bin/env python3

import sys
from os import readlink
from os.path import islink, dirname, abspath
from lark import Lark

self_path = abspath(dirname(readlink(__file__) if islink(__file__) else __file__))
sys.path.insert(0, abspath(f"{self_path}/.."))

from config import vamos_common_PYTHONPATH

sys.path.append(vamos_common_PYTHONPATH)


from vamos_mpt.parser.ast import ProcessPE
from vamos_mpt.mpt.pet import PrefixExpressionTransducer

PATTERNS = [
    ("a + b", ["a", "b"], ["aa", "ab", "c"]),
    ("a*b", ["b", "ab", "aab", "aaaaaab"], ["aa", "ba", "bb", "c"]),
    ("a.{a*b}", ["aab", "ab"], ["a", "aa", "aaa", "ac", "b"]),
    ("a.{a*b}.b", ["abb", "aabb"], ["ab", "aaab", "aca", "aaaaab"]),
    ("{a*b}*c", ["abc"], []),
    ("{{a*b}*c}*d", ["abcd"], []),
    ("{{{a + b}*b}*{c + b}}*{d + e}", ["d", "e", "ce"], []),
    ("l@{a*b}*c", ["abc"], []),
    ("_*c", ["aac", "aaaac"], ["d", "aaaad"]),
    ("l@_*{c + b}", ["aac", "aaaac", "aab"], ["d", "aaaad", "abc"]),
    ("l@{_}*{c + b}", ["aac", "aaaac", "aab"], ["d", "aaaad", "abc"]),
]

grammars_dir = abspath(f"{self_path}/../vamos_mpt/parser/grammars/")
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
    # print("----")
    # pet.dump()
    for word in pattern[1]:
        atoms = [parse(l) for l in word]
        alphabet = list(set(atoms + pe.alphabet()))
        # print(pe.pretty_str(), [a.pretty_str() for a in alphabet])
        pet = PrefixExpressionTransducer.from_pe(pe, alphabet)
        if not pet.accepts(atoms):
            print("---", pattern[0], "---")
            pet.dump()
            print("------")
            print("Should accept: ", word)
            print(f"Trajectory: {pet.trajectory(atoms)}")
            print("------")
    for word in pattern[2]:
        atoms = [parse(l) for l in word]
        alphabet = list(set(atoms + pe.alphabet()))
        pet = PrefixExpressionTransducer.from_pe(pe, alphabet)
        if pet.accepts(atoms):
            print("---", pattern[0], "---")
            pet.dump()
            print("------")
            print("Should NOT accept: ", word)
            print(f"Trajectory: {pet.trajectory(atoms)}")
            print("------")


print(f"Tested {n+1} expressions")
exit(exitval)
