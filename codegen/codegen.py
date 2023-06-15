from os import mkdir, readlink
from os.path import join as pathjoin, abspath, dirname, islink
from shutil import rmtree, copy as shutilcopy
from sys import stderr

from mpt.pet import PrefixExpressionTransducer
from parser.types.type import *


class CodeMapper:
    def append_mstring(M, pos_s, pos_e):
        return "{M}.append(MString::Letter({pos_s}, {pos_e}))"

    def c_type(self, ty: Type):
        assert isinstance(ty, Type), ty
        if isinstance(ty, BoolType):
            return f"bool"
        if isinstance(ty, IntType):
            return f"int{ty.bitwidth}_t"


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
            print("The output dir exists, overwriting its contents", file=stderr)
            # rmtree(outputdir)
            # mkdir(outputdir)

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

    def input_file(self, stream, name):
        inpath = pathjoin(self.templates_path, name)
        with open(inpath, "r") as infl:
            write = stream.write
            for line in infl:
                write(line)


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
        self.copy_file("monitor.h")
        self.copy_file("mstring.h")
        self.copy_file("trace.h")
        self.copy_file("inputs.h")
        self.copy_file("workbag.h")
        self.copy_file("cfgset.h")
        self.copy_file("main.cpp")
        self.copy_file("trace.cpp")
        self.copy_file("cfgs.cpp")
        self.copy_file("mstring.cpp")

    def _generate_cmake(self):
        from config import vamos_buffers_DIR, vamos_hyper_DIR
        self.gen_config("CMakeLists.txt.in", "CMakeLists.txt",
                        {"@vamos-buffers_DIR@" : vamos_buffers_DIR,
                         "@vamos-hyper_DIR@" : vamos_hyper_DIR})

    def _generate_add_cfgs(self, mpt, wr):
        wr("template <typename WorkbagTy, typename TracesT>\n")
        wr("static void add_new_cfgs(WorkbagTy &workbag, const TracesT &traces, Trace<TraceEvent> *trace) {\n")
        wr(f"  ConfigurationsSet<AnyCfg, {mpt.get_max_outdegree()}> S;\n")
        wr( "  for (auto &t : traces) {\n")
        wr( "    /* TODO: reflexivity reduction */\n")
# #ifdef REDUCT_REFLEXIVITY
#     if (trace == t.get())
#       continue;
# #endif

        wr( "    S.clear();\n")
        wr( "    // TODO: S.add(...)")
        # S.add(Cfg_1({t.get(), trace}));
        # S.add(Cfg_2({t.get(), trace}));
        # S.add(Cfg_3({t.get(), trace}));
        wr( "    workbag.push(std::move(S));\n")

# #ifdef REDUCT_SYMMETRY
#     S.clear();
#     S.add(Cfg_1({trace, t.get()}));
#     S.add(Cfg_2({trace, t.get()}));
#     S.add(Cfg_3({trace, t.get()}));
#     workbag.push(std::move(S));
# #endif
        wr("  }\n}\n\n")


    def _generate_events(self, mpt):
        with self.new_file("events.h") as f:
            wr = f.write
            wr('#ifndef OD_EVENTS_H_\n#define OD_EVENTS_H_\n\n')
            wr('#include <vamos-buffers/cpp/event.h>\n\n')
            wr('using vamos::Event;\n\n')

            wr('enum class Kind : vms_kind {\n')
            wr('  END = Event::doneKind(),\n')
            for n, event in enumerate(mpt.alphabet):
                wr(f'  {event.name.name}{" = Event::firstValidKind()" if n == 0 else ""},\n')
            wr('};\n\n')

            wr('struct TraceEvent : Event {\n')
            wr('  union {\n')
            c_type = self.codemapper.c_type
            for event in mpt.alphabet:
                sname = event.name.name
                wr(f'    struct _{sname} {{\n')
                for field in event.fields:
                    wr(f'      {c_type(field.type)} {field.name.name}; // {field}\n')
                wr(f'      bool operator==(const _{sname}& rhs) const {{\n')
                wr( '        return ')
                for n, field in enumerate(event.fields):
                    if n > 0:
                        wr(" && ")
                    wr(f'{field.name.name} == rhs.{field.name.name}')
                wr(';\n      }\n')
                wr(f'    }} {sname};\n')

            wr('  } data;\n\n')

            wr('  TraceEvent() = default;\n')
            wr('  TraceEvent(Kind k, vms_eventid id) : Event((vms_kind)k, id) {}\n')
            wr('  TraceEvent(vms_kind k, vms_eventid id) : Event(k, id) {}\n')

            wr('  bool operator==(const TraceEvent &rhs) const {\n'\
               '    if (kind() != rhs.kind()) return false;\n'\
               '    switch (kind()) {\n'\
               '      case (vms_kind)Kind::END: return true;\n')
            for event in mpt.alphabet:
                sname = event.name.name
                wr(f'      case (vms_kind)Kind::{sname}: return data.{sname} == rhs.data.{sname};\n')
            wr(f'      default: abort();\n')
            wr('    }\n  }\n\n')
               #'
#                                     (data.Write.value == rhs.data.Write.value &&
#                                      data.Write.addr == rhs.data.Write.addr));
#   }
#
            wr('  bool operator!=(const TraceEvent &rhs) const { return !operator==(rhs); }\n')
            wr('};\n\n')




            wr('\n\n#endif')

    def _generate_monitor_core(self, mpt):
        pass


    def _generate_monitor(self, mpt):
        with self.new_file("monitor.cpp") as f:
            wr = f.write
            wr('#include <cassert>\n\n')
            wr('#include "events.h"\n')
            wr('#include "monitor.h"\n')
            wr('#include "trace.h"\n')
            wr('#include "cfgset.h"\n')
            wr('#include "workbag.h"\n\n')
            wr('#include "inputs.h"\n\n')

            self._generate_add_cfgs(mpt, wr)

            self.input_file(f, "partials/update_traces.h")
            self.input_file(f, "partials/move_cfg.h")

            self.input_file(f, "partials/monitor_begin.h")
            self._generate_monitor_core(mpt)
            self.input_file(f, "partials/monitor_end.h")

    def generate(self, mpt):
        self._copy_common_files()
        self._generate_cmake()
        self._generate_events(mpt)
        self._generate_monitor(mpt)

