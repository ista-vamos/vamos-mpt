#!/usr/bin/env python3

import sys
from os import readlink
from os.path import islink, dirname, abspath

self_path = dirname(readlink(__file__) if islink(__file__) else __file__)
sys.path.insert(0, abspath(f"{self_path}/.."))

from parser.parser import Parser


parser = Parser()
for path in sys.argv[1:]:
    t = parser.parse_path(path)
    print(t.pretty())
