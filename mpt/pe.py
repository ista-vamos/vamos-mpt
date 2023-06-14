class PrefixExpressionTransducer:
    class State:
        def __init__(self, num, pe=None):
            self.pe = pe
            self.id = num
            self.successors = {}

        def add_succ(self, l, s):
            assert l not in self.successors or self.successors[l] == s, self
            self.successors[l] = s

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
            state = state.successors.get(w)
            if state is None:
                return False
        return state is self.acc_state

    def trajectory(self, word: list):
        states = [self.init_state]
        for w in word:
            state = states[-1].successors.get(w)
            states.append(state)
            if state is None:
                break
        return states



    def dump(self):
        for s in self.states.values():
            print(s)
        for s in self.states.values():
            for l, succ in s.successors.items():
                print(f"{s} -{l.pretty_str()}-> {succ}")

    def from_pe(PE, alphabet=None):
        #assert isinstance(PE, PrefixExpression), PE

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
                    d = cur_s.pe.derivation(l)
                    state = pet.get(d)
                    if state is None:
                        state = pet.new_state(d)
                        assert state is not None
                        new_states.append(state)
                        if d.is_empty():
                            assert pet.acc_state is None, (state, pet.acc_state)
                            pet.acc_state = state
                    cur_s.add_succ(l, state)

            cur_states = new_states
        return pet

