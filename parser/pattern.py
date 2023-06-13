class PatternElement:
    pass


class Atom(PatternElement):
    def __init__(self, val):
        self.value = val

    def __str__(self):
        return f"`{self.value}`"


class Event(Atom):
    def __init__(self, val, params=None):
        assert params is None or isinstance(params, list)
        super().__init__(val)
        self.params = params or []

    def __str__(self):
        return f"`{self.value}({', '.join(self.params)})`"


class SpecialAtom(Atom):
    def __init__(self, val):
        super().__init__(val)


class Until(PatternElement):
    def __init__(self, a, end):
        self.a = a
        self.end = end

    def __str__(self):
        return f"u{{{self.a} * {self.end}}}"


class Not(PatternElement):
    def __init__(self, elems):
        self.elems = elems

    def __str__(self):
        return f"!{{{self.elems}}}"


class Or(PatternElement):
    def __init__(self, elems):
        assert isinstance(elems, list), elems
        self.elems = elems

    def __str__(self):
        return f"p{{{' + '.join(map(str, self.elems))}}}"


class Seq(PatternElement):
    def __init__(self, elems):
        assert isinstance(elems, list), elems
        self.elems = elems

    def __str__(self):
        return f"s{{{'.'.join(map(str, self.elems))}}}"


class Group(PatternElement):
    def __init__(self, elems, name=None):
        assert isinstance(elems, list), elems
        assert name is None or isinstance(name, str), name
        self.name = name
        self.elems = elems

    def __str__(self):
        return f"g{{{' '.join(map(str, self.elems))}}}"


class Pattern:
    def __init__(self, consume, noconsume=None):
        self.consume = consume
        self.noconsume = noconsume

    def __str__(self):
        return f"{self.consume} | {self.noconsume}"
