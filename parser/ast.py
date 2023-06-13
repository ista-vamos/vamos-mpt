from .pattern import *
from .expr import *
from .decls import *
from .rule import Action, MatchPrefix, Rule
from .transformers import TraceTransformer, TraceQuantifier, Input, TransformerApplication, TransformerComposition
from .types.type import (
    type_from_token,
    NumType,
    UserType,
    TraceType,
    HypertraceType,
    Type,
)
from parser.element import Identifier, ElementList

from lark import Transformer
from lark.visitors import merge_transformers


class BaseTransformer(Transformer):
    def NUMBER(self, items):
        return ConstExpr(int(items.value), NumType())

    def NAME(self, items):
        return Identifier(str(items.value))


class ProcessPattern(Transformer):
    def ANY(self, items):
        return SpecialAtom("ANY")

    def END(self, items):
        return SpecialAtom("END")

    def START(self, items):
        return SpecialAtom("START")

    name = str

    def event(self, items):
        params = None
        if len(items) > 1:
            params = []
            for item in items[1:]:
                assert len(item.children) == 1
                params.append(item.children[0])
        return Event(items[0], params)

    def atom(self, items):
        assert len(items) == 1
        return items[0]

    def until(self, items):
        assert isinstance(items[1], Atom)
        assert len(items) == 2
        return Until(items[0], items[1])

    def choice(self, items):
        return Or(items)

    def diff(self, items):
        return Not(items)

    def seq(self, items):
        if len(items) == 1:  # do not create trivial sequences
            return items[0]
        return Seq(items)

    def group(self, items):
        if len(items) == 1:  # do not create trivial groups
            return items[0]
        return Group(items)

    def namedgroup(self, items):
        print(items)
        name = items[0]
        assert isinstance(name, str), items
        return Group(items[1] if isinstance(items[1], list) else [items[1]], name)

    def consume(self, items):
        return items[0]

    def noconsume(self, items):
        return items[0]


class ProcessRules(BaseTransformer):
    def tracelist(self, items):
        return items

    def rulebody(self, items):
        return items

    def action(self, items):
        assert len(items) == 1, items
        assert isinstance(items[0], Action), items
        return items[0]

    def act_yield(self, items):
        assert len(items) == 3, items
        return Action("yield", items)

    def yieldwhat(self, items):
        assert len(items) == 1, items
        return items[0]

    def yieldstream(self, items):
        assert len(items) == 1, items
        return items[0]

    def drulehead(self, items):
        assert False, items

    def pattern(self, items):
        assert len(items) == 2, items
        return Pattern(items[0], items[1])

    def matchprefix(self, items):
        assert len(items) == 2, items
        return MatchPrefix(items[0], items[1])

    def rulehead(self, items):
        return items

    def boolexpr(self, items):
        assert len(items) == 1, items
        assert isinstance(items[0], BoolExpr)
        return items[0]

    def rulecond(self, items):
        assert len(items) == 1, items
        assert isinstance(items[0], BoolExpr)
        return items[0]

    def rule(self, items):
        assert len(items) == 3, items
        return Rule(items[0], items[1], items[2])


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

    def access_index(self, items):
        assert len(items) == 2, items
        return AccessIndex(items[0].children[0], items[1].children[0])

    def access_identifier(self, items):
        return items[0]

    def identifier(self, items):
        return Identifier("::".join(map(lambda i: i.name if isinstance(i, Identifier) else i, items)))

    def call_or_event_pattern(self, items):
        params = [x for it in items[1].children for x in it.children if it is not None]
        return CallOrEventPattern(items[0].children[0], params)

    def var(self, items):
        return Var(items[0])


class ProcessAST(BaseTransformer):
    def __init__(self):
        super().__init__()
        self.decls = {}
        self.eventdecls = {}
        self.datadecls = {}
        self.tracedecls = {}
        self.streamdecls = {}
        self.usertypes = {}

    def eventdecl(self, items):
        fields = []
        if items[0].data == "name":
            assert len(items[0].children) == 1, items[0].children
            names = [str(items[0].children[0])]
        elif items[0].data == "namelist":
            assert len(items[0].children) > 1, items[0].children
            names = [str(ch) for ch in items[0].children]
        else:
            assert False, items[0]

        if len(items) > 1:
            if items[1].data == "fieldsdecl":
                fields = items[1].children
                assert len(fields) > 0, items[1]

        assert names, items
        decls = {name: EventDecl(name, fields) for name in names}

        self.decls.update(decls)
        self.eventdecls.update(decls)
        self.usertypes.update(decls)

        return ElementList(decls.values())

    def datadecl(self, items):
        if items[0].data == "name":
            assert len(items[0].children) == 1, items[0].children
            names = [str(items[0].children[0])]
        elif items[0].data == "namelist":
            assert len(items[0].children) > 1, items[0].children
            names = [str(ch) for ch in items[0].children]
        else:
            assert False, items[0]

        assert len(items) > 1, items
        fields = items[1:]

        decls = {name: DataDecl(name, fields) for name in names}

        self.decls.update(decls)
        self.datadecls.update(decls)
        self.usertypes.update(decls)

        return ElementList(decls.values())

    def traceelem(self, items):
        assert len(items) == 1, items
        if items[0].data == "name":
            assert len(items[0].children) == 1, items
            return UserType(str(items[0].children[0]))
        elif items[0].data == "inlineeventdecl":
            chlds = items[0].children
            assert chlds[0].data == "name"
            assert len(chlds[0].children) == 1, chlds
            assert chlds[1].data == "fieldsdecl"
            assert len(chlds) == 2, chlds
            name = chlds[0].children[0].name
            fields = chlds[1].children
            return EventDecl(name, fields)
        raise NotImplementedError(str(items))

    def tracedecl(self, items):
        decls = ElementList()
        assert items[0].data == "name", items
        name = items[0].children[0]
        elems = []
        for it in items[1:]:
            if isinstance(it, EventDecl):
                decls.append(it)
                # rename the declaration to be in the scope
                # of the trace
                it.name = Identifier(f"{name.name}::{it.name}")
                elems.append(UserType(it.name.name))

                self.decls[it.name] = it
                self.eventdecls[it.name] = it
                self.usertypes[it.name] = it
            else:
                elems.append(it)
        decls.append(TraceDecl(name, elems))
        return decls

    def pattern(self, items):
        assert 1 <= len(items) <= 2, items
        assert len(items[0].children) == 1, items
        if len(items) == 1:
            return (None, items[0].children[0])
        assert items[1] is None or len(items[1].children) == 1, items
        return (items[0].children[0], items[1].children[0] if items[1] else None)

    def usertype(self, items):
        return UserType(str(items[0]))

    def boolexpr(self, items):
        assert len(items) == 1, items
        assert isinstance(items[0], BoolExpr)
        return items[0]

    def iterrules(self, items):
        return items

    def tracetrans(self, items):
        return TraceTransformer(items[0], items[1], items[2])

    def transformerappl(self, items):
        assert items[0].data == "transformer"
        assert len(items[0].children) == 1
        T = items[0].children[0]
        print(items[0])
        if isinstance(T, TransformerComposition):
            assert False, T
        return TransformerApplication(T, items[1:])

    def transformercomp(self, items):
        return TransformerComposition([it.children[0] for it in items])


    def exist(self, items):
        assert len(items) >= 4, items
        return TraceQuantifier("exist", items[0], items[1], items[2], items[3:])

    def forall(self, items):
        assert len(items) >= 4, items
        return TraceQuantifier("forall", items[0], items[1], items[2], items[3:])

    def tracequantify(self, items):
        assert len(items) == 1
        return items[0]

    def inputdef(self, items):
        ty = items[1].children[0] if len(items) > 1 else None
        items[0].type = ty
        return Input(items[0])

    def tracetype(self, items):
        return TraceType(items)

    def hypertracetype(self, items):
        return HypertraceType(items)

    def hypertracetype_unbounded(self, items):
        return HypertraceType(items, bounded=False)

    def simpletype(self, items):
        assert len(items) == 1, items
        return type_from_token(items[0])

    def datafield(self, items):
        assert items[0].data == "name", items
        assert len(items[0].children) == 1, items
        assert len(items) == 2, items
        assert len(items[1].children) == 1, items
        name = items[0].children[0]
        ty = items[1].children[0]
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

    for ch in node.children:
        visit_ast(ch, lvl + 1, fn, args)

def prnode(lvl, node, *args):
    print(" "*lvl*2, node)

def transform_ast(lark_ast):
    T = merge_transformers(
        ProcessAST(),
        expr=ProcessExpr(),
        rules=merge_transformers(
            ProcessRules(), pattern=ProcessPattern(), expr=ProcessExpr()
        ),
        pattern=ProcessPattern(),
    )
    ast = T.transform(lark_ast)

    visit_ast(ast, 0, prnode)
    return ast
