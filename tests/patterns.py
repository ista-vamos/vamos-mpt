#!/usr/bin/env python3

import sys
from os import readlink
from os.path import islink, dirname, abspath
from lark import Lark

self_path = abspath(dirname(readlink(__file__) if islink(__file__) else __file__))
sys.path.insert(0, abspath(f"{self_path}/.."))
grammars_dir = f"{self_path}/../parser/"

from parser.ast import transform_ast

PATTERNS = [
    ("ev(x) ev(y)", "s{`ev(x)`.`ev(y)`}"),
    ("ev(x)*ev(y)", "u{`ev(x)` * `ev(y)`}"),
    ("{ev(x)*ev(y)}*ev(z)", "u{u{`ev(x)` * `ev(y)`} * `ev(z)`}"),
    ("{ev(x)*ev(y)}*ev(z) + a", "p{u{u{`ev(x)` * `ev(y)`} * `ev(z)`} + `a()`}"),
    (
        "{ev(x)*ev(y)}*ev(z) + a + b",
        "p{u{u{`ev(x)` * `ev(y)`} * `ev(z)`} + `a()` + `b()`}",
    ),
    (
        "{ev(x)*ev(y)}*ev(z) + a + b*c",
        "p{u{u{`ev(x)` * `ev(y)`} * `ev(z)`} + `a()` + u{`b()` * `c()`}}",
    ),
    (
        "{ev(x)*ev(y)}*ev(z) + a + b*c$",
        "p{u{u{`ev(x)` * `ev(y)`} * `ev(z)`} + `a()` + s{u{`b()` * `c()`}.`END`}}",
    ),
]

parser = Lark.open(
    "grammar.lark", rel_to=grammars_dir, import_paths=[grammars_dir], start="pattern"
)

exitval = 0
for n, pattern in enumerate(PATTERNS):
    t = parser.parse(pattern[0])
    out = str(transform_ast(t)[0])
    if out != pattern[1]:
        print(f"-- Wrong output for pattern {n}")
        print(f"Pattern: {pattern[0]}")
        print(f"Got     : {out}")
        print(f"Expected: {pattern[1]}")
        exitval = 1

exit(exitval)
