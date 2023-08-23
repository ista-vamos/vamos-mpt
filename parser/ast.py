from sys import stderr

from mpt.mpt import MPT
from vamos_common.parser.context import Context
from .expr import (
    BoolExpr,
    ConstExpr,
    CompareExpr,
    And,
    Or,
    Label,
    SubWord,
    MPE,
    EventVar,
)
from mpt.prefixexpr import *
from vamos_common.spec.ir.decls import *
from .transition import TransitionOutput, Transition
from vamos_common.types.type import (
    type_from_token,
    NumType,
    UserType,
    TraceType,
    HypertraceType,
    Type,
    BoolType,
)
from vamos_common.spec.ir.identifier import Identifier
from vamos_common.spec.ir.element import ElementList

from lark import Transformer
from lark.visitors import merge_transformers


class BaseTransformer(Transformer):
    def __init__(self, ctx=None):
        self.ctx = ctx or Context()

    def NUMBER(self, items):
        return ConstExpr(int(items.value), NumType())

    def NAME(self, items):
        return Identifier(str(items.value))


class ProcessPE(BaseTransformer):
    def __init__(self, events=None):
        super().__init__()
        """
        :param events: set of event names
        """
        self.events = events

    def get_eventdecl(self, name):
        if self.events:
            if isinstance(name, Identifier):
                name = name.name
            assert isinstance(name, str), (name, type(name))
            return self.events.get(name)
        return None

    def ANY(self, items):
        return SpecialAtom("ANY")

    def END(self, items):
        return SpecialAtom("END")

    def START(self, items):
        return SpecialAtom("START")

    def prefixexpr(self, items):
        return items[0]

    name = str

    def eventvar(self, items):
        if items[0].name == "_":
            return SpecialAtom("ANY")
        assert items[0].name not in ("$", "nil"), items

        # is this a name of event?
        if self.events:
            if self.get_eventdecl(items[0]):
                return Event(items[0])

            raise NotImplementedError(
                f"Event variables not implemented yet: {items[0]}"
            )

        print("Event variables not implemented, assuming this is a test", file=stderr)
        return EventVar(items[0])

    def event(self, items):
        return items[0]

    def params(self, items):
        return items

    def eventpattern(self, items):
        return Event(items[0], items[1])

    def atom(self, items):
        assert len(items) == 1
        return items[0]

    param = atom

    def oneletter(self, items):
        assert len(items) == 1, items
        return items[0]

    def choiceone(self, items):
        assert len(items) == 2, items
        return Choice(items)

    def until(self, items):
        assert len(items) == 2
        return Star(items[0], items[1])

    def choice(self, items):
        if items[0] is None:
            return items[1]
        return Choice(items)
    
    def longest_sequence(self,items):
        assert len(items)==1
        return Plus(items[0])

    def diff(self, items):
        return Not(items)

    def seq(self, items):
        if len(items) == 1:  # do not create trivial sequences
            return items[0]
        return Seq(items)

    def group(self, items):
        if len(items) == 1:  # do not create trivial groups
            return items[0]
        assert False, "Only named groups should propagate"
        return NamedGroup(items)

    def namedgroup(self, items):
        name = items[0]
        return NamedGroup(items[1], name)


class ProcessExpr(BaseTransformer):
    def eq(self, items):
        assert len(items) == 2, items
        return CompareExpr("==", items[0].children[0], items[1].children[0])

    def ne(self, items):
        assert len(items) == 2, items
        return CompareExpr("!=", items[0].children[0], items[1].children[0])

    def ge(self, items):
        assert len(items) == 2, items
        return CompareExpr(">=", items[0].children[0], items[1].children[0])

    def gt(self, items):
        assert len(items) == 2, items
        return CompareExpr(">", items[0].children[0], items[1].children[0])

    def land(self, items):
        if len(items) == 1:
            return items[0]
        return And(items[0], items[1])

    def lor(self, items):
        if len(items) == 1:
            return items[0]
        return Or(items[0], items[1])

    def constexpr(self, items):
        assert isinstance(items[0], ConstExpr), items
        return items[0]

    def labelexpr(self, items):
        return Label(items[0])

    def subwordexpr(self, items):
        return SubWord(items[0], items[1])


class ProcessTypes(BaseTransformer):
    def simpletype(self, items):
        assert len(items) == 1, items
        return type_from_token(items[0])

    def usertype(self, items):
        return UserType(str(items[0]))

    def tracetype(self, items):
        return TraceType(items)

    def hypertracetype(self, items):
        return HypertraceType(items)

    def type(self, items):
        return items[0]


class ProcessAST(BaseTransformer):
    def __init__(self, ctx=None):
        super().__init__(ctx)

        self.mpt = MPT()

    def initstate(self, items):
        self.mpt.init_state = items[0]
        return items

    def outs(self, items):
        self.mpt.traces_out = items
        return items

    def boolconst(self, items):
        assert items[0] in ("true", "false"), items
        if items[0] == "true":
            return ConstExpr(True, BoolType())
        if items[0] == "false":
            return ConstExpr(False, BoolType())
        raise RuntimeError(f"Invalid `boolconst` value: {items[0]}")

    def inputs(self, items):
        self.mpt.traces_in = items
        return items

    def transitions(self, items):
        self.mpt.transitions = items
        return items

    def eventdecl(self, items):
        fields = []
        if items[0].data == "name":
            assert len(items[0].children) == 1, items[0].children
            names = [items[0].children[0]]
        elif items[0].data == "namelist":
            assert len(items[0].children) > 1, items[0].children
            names = items[0].children
        else:
            assert False, items[0]

        if len(items) > 1:
            if items[1].data == "fieldsdecl":
                fields = items[1].children
                assert len(fields) > 0, items[1]

        assert names, items
        decls = {name: EventDecl(name, fields) for name in names}

        self.ctx.decls.update(decls)
        self.ctx.add_eventdecl(*decls.values())
        self.ctx.usertypes.update(decls)

        return ElementList(decls.values())

    def tracedecl(self, items):
        return TraceDecl(items[0], items[1])

    def prefixexpr(self, items):
        return items[0]

    def eventpattern(self, items):
        return Event(items[0], items[1])

    def traceelem(self, items):
        raise NotImplementedError(str(items))

    def tracevar(self, items):
        assert items[0].data == "name", items
        return items[0].children[0]

    def state(self, items):
        assert items[0].data == "name", items
        return items[0].children[0]

    def transition(self, items):
        start = items[0]
        end = items[1]
        exprmap = {}
        out, cond = TransitionOutput([]), None
        for it in items[2:]:
            if it is None:
                continue
            if it.data == "matchstmt":
                assert len(it.children) == 2, it
                tracevar = it.children[0]
                assert tracevar not in exprmap
                exprmap[tracevar] = it.children[1]
            elif it.data == "out":
                out = TransitionOutput(it.children)
            elif it.data == "condition":
                assert len(it.children) == 1, it
                cond = it.children[0]
            else:
                raise NotImplementedError(f"Invalid token: {it}")
        return Transition(start, end, MPE(exprmap), cond, out)

    def pattern(self, items):
        assert 1 <= len(items) <= 2, items
        assert len(items[0].children) == 1, items
        if len(items) == 1:
            return (None, items[0].children[0])
        assert items[1] is None or len(items[1].children) == 1, items
        return (items[0].children[0], items[1].children[0] if items[1] else None)

    def boolexpr(self, items):
        assert len(items) == 1, items
        assert isinstance(items[0], BoolExpr)
        return items[0]

    def typeannot(self, items):
        return items[0]

    def hypertracetype_unbounded(self, items):
        return HypertraceType(items, bounded=False)

    def simpletype(self, items):
        assert len(items) == 1, items
        return type_from_token(items[0])

    def datafield(self, items):
        assert items[0].data == "name", items
        name = items[0].children[0]
        ty = items[1]
        return DataField(name, ty)

    def type(self, items):
        assert len(items) == 1, items
        assert isinstance(items[0], Type), items
        return items[0]

    def tracelist(self, items):
        return items


def visit_ast(node, lvl, fn, *args):
    fn(lvl, node, *args)
    if node is None:
        return

    if not hasattr(node, "children"):
        return
    for ch in node.children:
        visit_ast(ch, lvl + 1, fn, args)


def prnode(lvl, node, *args):
    print(" " * lvl * 2, node)


def transform_ast(lark_ast, ctx):
    ctx = ctx or Context()
    base = ProcessAST(ctx)
    T = merge_transformers(
        base,
        comm=ProcessAST(),
        types=ProcessTypes(),
        expr=ProcessExpr(),
        prefixexpr=ProcessPE(base.ctx.eventdecls),
    )
    ast = T.transform(lark_ast)

    # print_ast:
    # visit_ast(ast, 0, prnode)
    finish_mpt(base.mpt, base.ctx.eventdecls)
    # base.mpt.dump()
    return ast, base


def finish_mpt(mpt, eventdecls):
    # gather all states and construct transition function
    for t in mpt.transitions:
        mpt.states.add(t.start)
        mpt.states.add(t.end)
        mpt.delta.setdefault(t.start, []).append(t)

    for _, ev in eventdecls.items():
        mpt.alphabet.add(ev)
