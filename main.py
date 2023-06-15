import sys
from parser.parser import Parser
from codegen.codegen import CodeGenCpp


def main():
    if len(sys.argv) != 2:
        print("Usage: main.py file", file=sys.stderr)
        exit(1)

    parser = Parser()
    ast, mpt = parser.parse_path(sys.argv[1])
    mpt.todot()
    # print(ast.pretty())

    codegen = CodeGenCpp()
    codegen.generate(mpt)


if __name__ == "__main__":
    main()
