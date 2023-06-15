#!/usr/bin/env python3

import sys
from os import readlink
from os.path import islink, dirname, abspath
from lark import Lark

self_path = abspath(dirname(readlink(__file__) if islink(__file__) else __file__))
sys.path.insert(0, abspath(f"{self_path}/.."))

from parser.ast import ProcessPE, visit_ast
from mpt.pet import PrefixExpressionTransducer

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

pe = parse(sys.argv[1])
print(f"Parsed PE: {pe}\n----", file=sys.stderr)
pet = PrefixExpressionTransducer.from_pe(pe)
pet.to_dot()
exit(0)
