from parser.element import Element

class Decl(Element):
    pass


class DataField(Element):
    def __init__(self, name, ty):
        super().__init__(ty)
        self.name = name

    @property
    def children(self):
        return ()

    def __str__(self):
        return f"{self.name} : {self.type}"

    def __repr__(self):
        return f"DataField({self.name} : {self.type})"


class EventDecl(Decl):
    def __init__(self, name, fields):
        super().__init__()
        self.name = name
        assert isinstance(fields, list), fields
        assert all(map(lambda f: isinstance(f, DataField), fields)), fields
        self.fields = fields

    @property
    def children(self):
        return self.fields

    def __str__(self):
        return f"Event {self.name} {{{','.join(map(str, self.fields))}}}"

    def __repr__(self):
        return f"EventDecl({self.name} {{{','.join(map(str, self.fields))}}})"


class TraceDecl(Decl):
    def __init__(self, name, elements):
        super().__init__()
        self.name = name
        self.elements = elements

    @property
    def children(self):
        return [self.name, self.elements]

    def __repr__(self):
        return f"TraceDecl({self.name} : {self.elements})"
