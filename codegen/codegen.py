from os import mkdir, readlink
from os.path import join as pathjoin, abspath, dirname, islink
from shutil import rmtree, copy as shutilcopy
from sys import stderr

from mpt.pet import PrefixExpressionTransducer


class CodeMapper:
    def append_mstring(M, pos_s, pos_e):
        return "{M}.append(MString::Letter({pos_s}, {pos_e}))"


class CodeGen:
    def __init__(self, outputdir="/tmp/mpt/", codemapper=None):
        if codemapper is None:
            self.codemapper = CodeMapper()
        else:
            self.codemapper = codemapper

        self.files = []
        self.out_dir = abspath(outputdir)
        self.templates_path = None

        try:
            mkdir(outputdir)
        except OSError:
            print("The output dir exists, overwriting it", file=stderr)
            rmtree(outputdir)
            mkdir(outputdir)

    def copy_file(self, name):
        path = pathjoin(self.templates_path, name)
        shutilcopy(path, self.out_dir)

    def new_file(self, name):
        filename = pathjoin(self.out_dir, name)
        assert filename not in self.files
        self.files.append(filename)
        return open(filename, "w")

    def gen_config(self, infile, outfile, values):
        inpath = pathjoin(self.templates_path, infile)
        outpath = pathjoin(self.out_dir, outfile)
        with open(inpath, "r") as infl:
            with open(outpath, "w") as outfl:
                for line in infl:
                    if "@" in line:
                        for v, s in values.items():
                            assert v.startswith("@"), v
                            assert v.endswith("@"), v
                            line = line.replace(v, s)
                    outfl.write(line)


class CodeGenCpp(CodeGen):
    def __init__(self, outputdir="/tmp/mpt/", codemapper=None):
        super().__init__(outputdir, codemapper)
        self_path = abspath(dirname(readlink(__file__) if islink(__file__) else __file__))
        self.templates_path = pathjoin(self_path, "templates/cpp")


    def generate_pe_transducer(self, pe, name):
        pet = PrefixExpressionTransducer.from_pe(pe)
        pet.dump()
        emit = print
        emit(f"struct {name} : public PrefixExpressionTransducer {{")
        emit("PEStepResult step(const Event *ev, size_t pos) {")
        emit("const auto *e = static_cast<const TraceEvent *>(ev);")

#     switch ((Kind)e->kind()) {
#     case Kind::InputL:
#     case Kind::OutputL:
#       state = 1;
#       {codemapper.append_mstring('M', 'pos', 'pos')};
#       return PEStepResult::Accept;
#     default:
#       assert(state == 0);
#       return PEStepResult::None;
#     }
#   }
# };

    def _copy_common_files(self):
        self.copy_file("mstring.h")
        self.copy_file("trace.h")
        self.copy_file("inputs.h")
        self.copy_file("workbag.h")
        self.copy_file("main.cpp")

    def _generate_cmake(self):
        from config import vamos_buffers_DIR, vamos_hyper_DIR
        self.gen_config("CMakeLists.txt.in", "CMakeLists.txt",
                        {"@vamos-buffers_DIR@" : vamos_buffers_DIR,
                         "@vamos-hyper_DIR@" : vamos_hyper_DIR})

    def _generate_monitor(self):
        with self.new_file("monitor.cpp") as f:
            wr = f.write
            raise NotImplementedError("Not implemented YET")

    def generate(self, mpt):
        self._copy_common_files()
        self._generate_cmake()

