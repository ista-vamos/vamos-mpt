from mpt.prefixexpr import PrefixExpr


class PrefixExpressionTransducer:
    class State:
        def __init__(self, num, pe=None):
            self.pe = pe
            self.id = num
            self.successors = {}

        def add_succ(self, l, s, out=None):
            assert l not in self.successors or self.successors[l] == (s, out), (
                self,
                l,
                s,
                out,
                self.successors[l],
            )
            self.successors[l] = (s, out)

        def __hash__(self):
            return self.pe.__hash__()

        def __eq__(self, rhs):
            return self.pe == rhs.pe

        def __repr__(self):
            return f"<{self.id} | {self.pe.pretty_str()}>"

    def __init__(self):
        self.states = {}
        self.init_state = None
        self.acc_state = None

    def new_state(self, pe):
        if pe in self.states:
            return None

        state = PrefixExpressionTransducer.State(len(self.states), pe)
        self.states[pe] = state
        return state

    def get(self, pe):
        return self.states.get(pe)

    def accepts(self, word: list):
        state = self.init_state
        for w in word:
            x = state.successors.get(w)
            if x is None:
                return False
            state, _ = x
        return state is self.acc_state

    def trajectory(self, word: list):
        states = [self.init_state]
        for w in word:
            x = states[-1].successors.get(w)
            if x is None:
                break
            state, _ = x
            states.append(state)
        return states

    def dump(self, fl=None):
        for s in self.states.values():
            print(s, file=fl)
        for s in self.states.values():
            for l, x in s.successors.items():
                succ, out = x
                print(f"{s} -{l.pretty_str()}/{out}-> {succ}", file=fl)

    def to_dot(self, reduced=True, fl=None):
        print("digraph PET {", file=fl)
        print(f'  label="{self.init_state.pe.pretty_str()}"\n', file=fl)
        print("00 [style=invisible]", file=fl)
        for s in self.states.values():
            if reduced and s.pe.is_bot():
                continue
            print(
                f'{s.id}[label="{s.pe.pretty_str()}" shape={"doublecircle" if self.acc_state is s else "box"}]',
                file=fl
            )

        print("00 -> 0", file=fl)
        for s in self.states.values():
            for l, x in s.successors.items():
                succ, out = x
                if reduced and succ.pe.is_bot():
                    continue
                print(f'{s.id} -> {succ.id} [label="{l.pretty_str()}/{out or ""}"]', file=fl)
        print("}", file=fl)

    def from_pe(PE: PrefixExpr, alphabet: list = None):
        assert isinstance(PE, PrefixExpr), PE

        if alphabet is None:
            alphabet = PE.alphabet()
        pet = PrefixExpressionTransducer()
        pet.init_state = pet.new_state(PE)
        if PE.is_empty():
            pet.acc_state = pet.init_state
            return pet

        cur_states = [pet.init_state]
        while cur_states:
            new_states = []

            for cur_s in cur_states:
                for l in alphabet:
                    d, m = cur_s.pe.step(l)
                    state = pet.get(d)
                    if state is None:
                        state = pet.new_state(d)
                        assert state is not None
                        new_states.append(state)
                        if d.is_empty():
                            assert pet.acc_state is None, (state, pet.acc_state)
                            pet.acc_state = state
                    cur_s.add_succ(l, state, m)

            cur_states = new_states
        return pet
