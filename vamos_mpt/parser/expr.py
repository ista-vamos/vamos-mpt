from vamos_common.spec.ir.element import Element
from vamos_common.spec.ir.expr import Expr
from vamos_common.types.type import BoolType

from vamos_mpt.mpt.prefixexpr import Atom


class ConstExpr(Expr):
    def __init__(self, c, ty=None):
        super().__init__()
        self.value = c
        self.type = ty

    def pretty_str(self):
        return f"{self.value} : {self.type or ''}"

    def __str__(self):
        return f"CONST({self.value} : {self.type or ''})"

    def __repr__(self):
        return f"ConstExpr({self.value} : {self.type or ''})"


class Cast(Expr):
    def __init__(self, val, ty):
        super().__init__()
        self._value = val
        self._type = ty

    @property
    def value(self):
        return self._value

    def type(self):
        return self._type

    def pretty_str(self):
        return f"{self.value} as {self.type()}"

    def __repr__(self):
        return f"Cast({self.value}, {self.type()})"


class Var(Expr):
    def __init__(self, v):
        super().__init__()
        self.name = v

    def pretty_str(self):
        return self.name

    def __str__(self):
        return f"VAR({self.name})"

    def __repr__(self):
        return f"Var({self.name})"


class SubWord(Expr):
    def __init__(self, lhs, lbl):
        super().__init__()
        self.lhs = lhs
        self.label = lbl

    def pretty_str(self):
        return f"{self.lhs.pretty_str()}[{self.label.pretty_str()}]"

    def __repr__(self):
        return f"SubWord({self.lhs}, {self.label})"

    @property
    def children(self):
        return []


class Label(Expr):
    def __init__(self, name):
        super().__init__()
        self.name = name

    def pretty_str(self):
        return self.name.pretty_str()

    def __repr__(self):
        return f"Label({self.name})"


class BoolExpr(Expr):
    def __init__(self):
        super().__init__()
        self.type = BoolType


class CompareExpr(BoolExpr):
    def __init__(self, comparison, lhs, rhs):
        super().__init__()
        self.comparison = comparison
        self.lhs = lhs
        self.rhs = rhs

    def pretty_str(self):
        return f"{self.lhs.pretty_str()} {self.comparison} {self.rhs.pretty_str()}"

    def __str__(self):
        return f"{self.lhs} {self.comparison} {self.rhs}"

    def __repr__(self):
        return f"CompareExpr({self.lhs} {self.comparison} {self.rhs})"

    @property
    def children(self):
        return [self.lhs, self.rhs]


class And(BoolExpr):
    def __init__(self, lhs, rhs):
        super().__init__()
        self.lhs = lhs
        self.rhs = rhs

    def pretty_str(self):
        return f"({self.lhs.pretty_str()} && {self.rhs.pretty_str()})"

    def __str__(self):
        return f"({self.lhs} && {self.rhs})"

    def __repr__(self):
        return f"And({self.lhs} && {self.rhs})"


class Or(BoolExpr):
    def __init__(self, lhs, rhs):
        super().__init__()
        self.lhs = lhs
        self.rhs = rhs

    def pretty_str(self):
        return f"({self.lhs.pretty_str()} || {self.rhs.pretty_str()})"

    def __str__(self):
        return f"({self.lhs} || {self.rhs})"

    def __repr__(self):
        return f"Or({self.lhs} || {self.rhs})"


class MPE(Element):
    def __init__(self, exprmap):
        super().__init__()
        self.exprs = exprmap

    def get(self, t):
        return self.exprs.get(t)

    def __repr__(self):
        return f"MPE({self.exprs})"


class EventVar(Atom):
    def __repr__(self):
        return f"EventVar({self.value})"
