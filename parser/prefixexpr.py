from parser.element import Identifier
from copy import deepcopy


class PrefixExpr:
    def derivation(self, a):
        assert isinstance(a, PrefixExpr), a
        raise NotImplementedError("Child must override")

    def is_empty(self):
        return False

    def is_bot(self):
        return False

    def copy(self):
        return deepcopy(self)


class Bot(PrefixExpr):
    def pretty_str(self):
        return "⊥"

    def derivation(self, a):
        assert isinstance(a, PrefixExpr), a
        return self

    def is_bot(self):
        return True

    def __repr__(self):
        return "⊥"

# one instance of Bot() that we where we do not need new instances of Bots'
BOT = Bot()

class Empty(PrefixExpr):

    def derivation(self, a):
        assert isinstance(a, PrefixExpr), a
        return BOT

    def pretty_str(self):
        return "ε"

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

    def derivation(self, a):
        assert isinstance(a, Atom), a
        if a == self:
            return EMPTY
        return BOT

    def pretty_str(self):
        if isinstance(self.value, Identifier):
            return self.value.name
        return self.value

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

    def derivation(self, a):
        assert isinstance(a, Atom), a
        ending = self.end.derivation(a)
        if ending.is_empty():
            return ending
        return Seq([self.a.derivation(a), self.copy()])

    def pretty_str(self):
        return f"{self.a.pretty_str()}*{self.end.pretty_str()}"

    def __repr__(self):
        return f"Star({self.a}, {self.end})"



class Choice(PrefixExpr):
    def __init__(self, elems):
        assert isinstance(elems, list), elems
        self.elems = elems


    def derivation(self, a):
        assert isinstance(a, Atom), a
        new_elems = [d for d in (e.derivation(a) for e in self.elems) if not d.is_bot()]
        if not new_elems: # all derivations are BOT
            return BOT
        if any(map(lambda e: e.is_empty(), new_elems)):
            return EMPTY
        return Choice(new_elems)

    def pretty_str(self):
        return f"{{{'+'.join((s.pretty_str() for s in self.elems))}}}"

    def __repr__(self):
        return f"Choice({' + '.join(map(str, self.elems))})"


class Seq(PrefixExpr):
    def __init__(self, elems):
        assert isinstance(elems, list), elems
        self.elems = elems

    def derivation(self, a):
        assert isinstance(a, Atom), a
        elems_len = len(self.elems)
        assert elems_len > 0
        first_elem = self.elems[0]
        assert not first_elem.is_bot(), self
        assert not first_elem.is_empty(), self
        d = first_elem.derivation(a)
        if d.is_bot():
            return BOT
        if d.is_empty():
            if elems_len == 1:
                return EMPTY
            if elems_len == 2:
                return self.elems[1]
            assert elems_len > 2
            return Seq(self.elems[1:])
        return Seq([d]+self.elems[1:])

    def pretty_str(self):
        return f"{{{'.'.join((s.pretty_str() for s in self.elems))}}}"

    def __repr__(self):
        return f"Seq({'.'.join(map(str, self.elems))})"



class NamedGroup(PrefixExpr):
    def __init__(self, elem, name=None):
        assert name is None or isinstance(name, Identifier), name
        self.name = name
        self.elem = elem

    def derivation(self, a):
        assert isinstance(a, Atom), a
        assert self.name
        assert self.elem
        assert not self.elem.is_empty()
        assert not self.elem.is_bot()

        return NamedGroupDeriv(self.elem.derivation(a), self.name)

    def pretty_str(self):
        inner = self.elem.pretty_str()
        if inner[0] == "{" and inner[-1] == "}":
            inner = inner[1:-1]
        if self.name:
            return f"{self.name.name}@{{{inner}}}"
        return f"{{{inner}}}"

    def __repr__(self):
        return f"NamedGroup({self.name}, {self.elem})"


class NamedGroupDeriv(NamedGroup):
    """
    Named group that is being derived -- to keep track about the names
    """
    def __init__(self, elems, name=None):
        super().__init__(elems, name)

    def __repr__(self):
        return f"NamedGroup'({self.name}, {self.elem})"
