class MPT:
    def __init__(self):
        self.states = set()
        self.transitions = []
        self.delta = {}
        self.init_state = None
        self.alphabet = set()
        self.traces_in = []
        self.traces_out = []

    def dump(self):
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
"""
        )

    def todot(self, fl=None):
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
            label += f"~> {t.output.values}"
            pr(f'{t.start.name} -> {t.end.name} [label="{label}"];')
        pr("}")
