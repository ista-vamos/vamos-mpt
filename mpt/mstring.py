class MString(list):
    def append(self, x):
        if isinstance(x, list):
            for l in x:
                self._append_one(l)
        else:
            self._append_one(x)

    def _append_one(self, x):
        if not self:
            super().append(x)
            return

        last_start, last_end = self[-1]
        if last_end is not None:
            super().append(x)
            return

        # last end is None
        start, end = x
        if start is None:
            assert end is not None
            self[-1][1] = end
            return
        assert "BUG", (self, x)


class MMap:
    def __init__(self):
        self.data = {}

    def append(self, label, mstr):
        self.data.setdefault(label, MString()).append(mstr)
        return self

    def update(self, mmap):
        if mmap is None:
            return self
        for l, mstr in mmap.data.items():
            # labels must be unique
            assert l not in self.data, (self, mmap)
            self.data[l] = mstr
        return self

    def items(self):
        return self.data.items()

    def __bool__(self):
        return bool(self.data)

    def __eq__(self, rhs):
        return self.data == rhs.data

    def __hash__(self):
        return self.data.__hash__()

    def __repr__(self):
        return f"MMap{self.data}"

    def __str__(self):
        contents = ', '.join((f"{l.pretty_str()} -> {''.join(map(str, s))}" for l, s in self.data.items()))
        return f"{{{contents}}}"
