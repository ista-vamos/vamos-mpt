class CodeMapper:
    def append_mstring(M, pos_s, pos_e):
        return "{M}.append(MString::Letter({pos_s}, {pos_e}))"


class CodeGen:
    def __init__(self, stream, codemapper=None)
        self.stream = stream

        if codemapper is None:
            self.codemapper = CodeMapper()
        else:
            self.codemapper = codemapper


class CodeGenCpp:
    def __init__(self, stream, codemapper=None):
        super().__init__(stream, codemapper)

    def generate_pe_transducer(pe, name):
        code=\
f"""
  struct {name} : public PrefixExpressionTransducer {
  PEStepResult step(const Event *ev, size_t pos) {
    const auto *e = static_cast<const TraceEvent *>(ev);

    switch ((Kind)e->kind()) {
    case Kind::InputL:
    case Kind::OutputL:
      state = 1;
      {codemapper.append_mstring('M', 'pos', 'pos')};
      return PEStepResult::Accept;
    default:
      assert(state == 0);
      return PEStepResult::None;
    }
  }
};
"""


    def generate(mpt, codemapper=None):

        # generate transducers for prefix expressions
