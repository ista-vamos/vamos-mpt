from parser.element import Identifier


class PrefixExprElement:
    pass


class Atom(PrefixExprElement):
    def __init__(self, val):
        self.value = val

    def pretty_str(self):
        if isinstance(self.value, Identifier):
            return self.value.name
        return self.value

    def __repr__(self):
        return f"Atom({self.value})"


class Event(Atom):
    def __init__(self, val, params=None):
        assert params is None or isinstance(params, list)
        super().__init__(val)
        self.params = params or []

    def pretty_str(self):
        if self.params:
            return f"{self.value.name}({', '.join((p.name for p in self.params))})"
        return self.value.name

    def __repr__(self):
        return f"Event({self.value}: {', '.join(map(str, self.params))})"


class EventVar(Atom):
    def __init__(self, val):
        super().__init__(val)

    def __repr__(self):
        return f"EventVar({self.value})"


class SpecialAtom(Atom):
    def __init__(self, val):
        super().__init__(val)

    def pretty_str(self):
        if self.value == "ANY":
            return "_"
        if self.value == "END":
            return "$"
        return super().pretty_str()


class Until(PrefixExprElement):
    def __init__(self, a, end):
        self.a = a
        self.end = end

    def pretty_str(self):
        return f"{self.a.pretty_str()}*{self.end.pretty_str()}"
    def __repr__(self):
        return f"Star({self.a}, {self.end})"


class Not(PrefixExprElement):
    def __init__(self, elems):
        self.elems = elems

    def pretty_str(self):
        return f"!({self.elems.pretty_str()})"

    def __repr__(self):
        return f"Not({self.elems})"


class Choice(PrefixExprElement):
    def __init__(self, elems):
        assert isinstance(elems, list), elems
        self.elems = elems

    def pretty_str(self):
        return f"{{{'+'.join((s.pretty_str() for s in self.elems))}}}"

    def __repr__(self):
        return f"Choice({' + '.join(map(str, self.elems))})"


class Seq(PrefixExprElement):
    def __init__(self, elems):
        assert isinstance(elems, list), elems
        self.elems = elems

    def pretty_str(self):
        return f"{{{'.'.join((s.pretty_str() for s in self.elems))}}}"
    def __repr__(self):
        return f"Seq({'.'.join(map(str, self.elems))})"


class Group(PrefixExprElement):
    def __init__(self, elems, name=None):
        assert isinstance(elems, list), elems
        assert name is None or isinstance(name, Identifier), name
        self.name = name
        self.elems = elems

    def pretty_str(self):
        inner = ' '.join((s.pretty_str() for s in self.elems))
        if len(self.elems) == 1 and inner[0] == "{" and inner[-1] == "}":
            inner = inner[1:-1]
        if self.name:
            return f"{self.name.name}@{{{inner}}}"
        return f"{{{inner}}}"

    def __repr__(self):
        return f"Group({self.name}, {' '.join(map(str, self.elems))})"
