class MPT:
    def __init__(self):
        self.states = set()
        self.transitions = []
        self.delta = {}
        self.init_state = None
        self.alphabet = set()
        self.traces_in = []
        self.traces_out = []

    def get_max_outdegree(self):
        return max(map(len, (self.delta.values())))

    def has_single_boolean_output(self):
        outs = self.traces_out
        return len(outs) == 1 and outs[0].has_simple_bool_type()

    def is_init_transition(self, t):
        assert t in self.transitions, self
        assert self.init_state is not None, self
        return t.start == self.init_state

    def successors(self, transition):
        "Successor transitions to a given transition"
        return [s for s in self.transitions if s.start == transition.end]

    def dump(self, fl=None):
        print(
            f"""
MPT:
  states: {self.states}
  init_state: {self.init_state}
  traces_in: {self.traces_in}
  traces_out: {self.traces_out}
  alphabet: {self.alphabet}
  transitions: {self.transitions}
  delta: {self.delta}
""",
            file=fl,
        )

    def to_dot(self, fl=None):
        def pr(msg):
            print(msg, file=fl)

        pr("digraph MPT {")
        for s in self.states:
            pr(f'{s.name}[label="{s.name}"];')
        pr("")
        for t in self.transitions:
            label = ""
            for tv, pe in t.mpe.exprs.items():
                label += f"{tv.pretty_str()}: {pe.pretty_str()}\\n"
            label += f"{t.cond.pretty_str()}\\n"
            label += f"~> {' '.join((v.pretty_str() for v in t.output.values))}"
            pr(f'{t.start.name} -> {t.end.name} [label="{label}"];')
        pr("}")
