from mpt.mstring import MMap
from parser.element import Identifier
from copy import deepcopy


class PrefixExpr:
    def derivation(self, a):
        return self.step(a)[0]

    def step(self, a, p="p"):
        assert isinstance(a, PrefixExpr), a
        raise NotImplementedError("Child must override")

    def is_empty(self):
        return False

    def is_bot(self):
        return False

    def copy(self):
        return deepcopy(self)

    def alphabet(self):
        return []

    def __hash__(self):
        return str(self).__hash__()

    # raise NotImplementedError(f"Child must override: in {type(self)}")


class Bot(PrefixExpr):
    def pretty_str(self):
        return "⊥"

    def step(self, a, p="p"):
        return self, None

    def __eq__(self, rhs):
        return isinstance(rhs, Bot)

    def __hash__(self):
        return str(self).__hash__()

    def is_bot(self):
        return True

    def __repr__(self):
        return "⊥"


# one instance of Bot() that we where we do not need new instances of Bots'
BOT = Bot()


class Empty(PrefixExpr):
    def step(self, a, p="p"):
        return BOT, None

    def pretty_str(self):
        return "ε"

    def __eq__(self, rhs):
        return isinstance(rhs, Empty)

    def __hash__(self):
        return str(self).__hash__()

    def is_empty(self):
        return True

    def __repr__(self):
        return "ε"


EMPTY = Empty()


class Atom(PrefixExpr):
    """
    An atom or `letter` of PEs.
    """

    def __init__(self, val):
        self.value = val

    def step(self, a, p="p"):
        assert isinstance(a, Atom), a
        if a == self:
            return EMPTY, None
        return BOT, None

    def pretty_str(self):
        if isinstance(self.value, Identifier):
            return self.value.name
        return self.value

    def alphabet(self):
        return [self]

    def __hash__(self):
        return self.value.__hash__()

    def __eq__(self, other):
        return self.value == other.value

    def __repr__(self):
        return f"Atom({self.value})"


class Event(Atom):
    """
    Specialization of Atom -- an event.
    """

    def __init__(self, val, params=None):
        assert params is None or isinstance(params, list)
        super().__init__(val)
        self.params = params or []

    def pretty_str(self):
        if self.params:
            return f"{self.value.name}({', '.join((p.name for p in self.params))})"
        return self.value.name

    def __eq__(self, other):
        return self.value == other.value and self.params == other.params

    def __repr__(self):
        return f"Event({self.value}: {', '.join(map(str, self.params))})"


class SpecialAtom(Atom):
    """
    Special atoms: `end of trace` and `any atom (that makes sense in the context)`
    """

    def pretty_str(self):
        if self.value == "ANY":
            return "_"
        if self.value == "END":
            return "$"
        return super().pretty_str()


class Star(PrefixExpr):
    """
    Binary "Kleene" bounded iteration, something like `until`
    from LTL but with the shortest-match semantics.
    """

    def __init__(self, a, end):
        self.a = a
        self.end = end

    def step(self, a, p="p"):
        assert isinstance(a, Atom), a
        ending, m = self.end.step(a, p)
        if ending.is_empty():
            return EMPTY, m
        d, m = self.a.step(a, p)
        if d.is_empty():
            return self.copy(), m
        if d.is_bot():
            return BOT, None
        return Seq([d, self.copy()]), m

    def alphabet(self):
        return self.a.alphabet() + self.end.alphabet()

    def pretty_str(self):
        lhs = self.a.pretty_str()
        if isinstance(self.a, Star):
            lhs = f"{{{lhs}}}"
        return f"{lhs}*{self.end.pretty_str()}"

    def __eq__(self, rhs):
        return isinstance(rhs, Star) and self.end == rhs.end and self.a == rhs.a

    def __hash__(self):
        return str(self).__hash__()

    def __repr__(self):
        return f"Star({self.a}, {self.end})"


class Choice(PrefixExpr):
    def __init__(self, elems):
        assert isinstance(elems, list), elems
        self.elems = elems

    def step(self, a, p="p"):
        # TODO: refactor
        assert isinstance(a, Atom), a
        new_elems = []
        mm = MMap()
        for d, m in (e.step(a, p) for e in self.elems):
            if d.is_bot():
                continue
            new_elems.append(d)
            if d.is_empty():
                mm.update(m)

        if not new_elems:  # all derivations are BOT
            return BOT, None
        if any(map(lambda e: e.is_empty(), new_elems)):
            return EMPTY, mm or None
        if len(new_elems) == 1:
            return new_elems[0], mm or None
        return Choice(new_elems), mm or None

    def __eq__(self, rhs):
        return isinstance(rhs, Choice) and self.elems == rhs.elems

    def __hash__(self):
        return str(self).__hash__()

    def alphabet(self):
        return [x for e in self.elems for x in e.alphabet()]

    def pretty_str(self):
        assert len(self.elems) > 1, self
        return f"{{{'+'.join((s.pretty_str() for s in self.elems))}}}"

    def __repr__(self):
        return f"Choice({' + '.join(map(str, self.elems))})"


class Seq(PrefixExpr):
    def __init__(self, elems):
        assert isinstance(elems, list), elems
        self.elems = elems

    def step(self, a, p="p"):
        assert isinstance(a, Atom), a
        elems_len = len(self.elems)
        assert elems_len > 0
        first_elem = self.elems[0]
        assert not first_elem.is_bot(), self
        assert not first_elem.is_empty(), self
        d, m = first_elem.step(a, p)
        if d.is_bot():
            return BOT, None
        if d.is_empty():
            if elems_len == 1:
                return EMPTY, m
            if elems_len == 2:
                return self.elems[1], m
            assert elems_len > 2
            return Seq(self.elems[1:]), m
        return Seq([d] + self.elems[1:]), m

    def __eq__(self, rhs):
        return isinstance(rhs, Seq) and self.elems == rhs.elems

    def __hash__(self):
        return str(self).__hash__()

    def alphabet(self):
        return [x for e in self.elems for x in e.alphabet()]

    def pretty_str(self):
        if len(self.elems) == 1:
            return self.elems[0].pretty_str()
        return f"{{{'.'.join((s.pretty_str() for s in self.elems))}}}"

    def __repr__(self):
        return f"Seq({'.'.join(map(str, self.elems))})"


class NamedGroup(PrefixExpr):
    def __init__(self, elem, name=None):
        assert name is None or isinstance(name, Identifier), name
        self.name = name
        self.elem = elem

    def step(self, a, p="p"):
        assert isinstance(a, Atom), a
        assert self.name
        assert self.elem
        assert not self.elem.is_empty(), self
        assert not self.elem.is_bot(), self

        d, m = self.elem.step(a, p)
        if d.is_bot():
            return BOT, None

        if m is None:
            m = MMap()
        if d.is_empty():
            return d, m.append(self.name, (p, p))
        return NamedGroupDeriv(d, self.name), m.append(self.name, (p, None))

    def __eq__(self, rhs):
        return (
            isinstance(rhs, NamedGroup)
            and self.name == rhs.name
            and self.elem == rhs.elem
        )

    def alphabet(self):
        return [x for x in self.elem.alphabet()]

    def pretty_str(self):
        inner = self.elem.pretty_str()
        if inner[0] == "{" and inner[-1] == "}":
            inner = inner[1:-1]
        assert self.name, self
        return f"{self.name.name}@{{{inner}}}"

    def __repr__(self):
        return f"NamedGroup({self.name}, {self.elem})"


class NamedGroupDeriv(NamedGroup):
    """
    Named group that is being derived -- to keep track about the names
    """

    def __init__(self, elem, name=None):
        super().__init__(elem, name)

    def pretty_str(self):
        inner = self.elem.pretty_str()
        if inner[0] == "{" and inner[-1] == "}":
            inner = inner[1:-1]
        assert self.name, self
        return f"{self.name.name}'@{{{inner}}}"

    def step(self, a, p="p"):
        assert isinstance(a, Atom), a
        assert self.name
        assert self.elem
        assert not self.elem.is_empty(), self
        assert not self.elem.is_bot(), self

        d, m = self.elem.step(a, p)
        if d.is_bot():
            return BOT, None

        if m is None:
            m = MMap()
        if d.is_empty():
            return d, m.append(self.name, (None, p))
        return NamedGroupDeriv(d, self.name), m or None

    def __eq__(self, rhs):
        return (
            isinstance(rhs, NamedGroupDeriv)
            and self.name == rhs.name
            and self.elem == rhs.elem
        )

    def __repr__(self):
        return f"NamedGroupDeriv({self.name}, {self.elem})"
