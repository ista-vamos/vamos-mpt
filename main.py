import sys
from parser.parser import Parser


def main():
    if len(sys.argv) != 2:
        print("Usage: main.py file", file=sys.stderr)
        exit(1)

    parser = Parser()
    ast = parser.parse_path(sys.argv[1])
    #print(ast.pretty())


if __name__ == "__main__":
    main()
