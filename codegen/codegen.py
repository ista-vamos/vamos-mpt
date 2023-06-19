from os import mkdir, readlink
from os.path import join as pathjoin, abspath, dirname, islink
from shutil import rmtree, copy as shutilcopy
from sys import stderr

from mpt.pet import PrefixExpressionTransducer
from mpt.prefixexpr import SpecialAtom, Atom, Event
from parser.expr import CompareExpr, SubWord
from parser.types.type import *


class CodeMapper:
    def append_mstring(self, M, pos_s, pos_e):
        return f"{M}.append(MString::Letter({pos_s}, {pos_e}))"

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

def ev_kind(ev):
    assert isinstance(ev, Atom), ev
    if isinstance(ev, SpecialAtom):
        if ev.is_end():
            return "END"
        raise NotImplementedError(f"Invalid event kind: {ev}")
    return ev.value.name

def map_pos(pos):
    if pos == 'p':
        return 'pos'
    if pos is None:
        return 'MString::Letter::BOT'

    raise RuntimeError("Unreachable")

class CodeGenCpp(CodeGen):
    def __init__(self, outputdir="/tmp/mpt/", codemapper=None):
        super().__init__(outputdir, codemapper)
        self_path = abspath(dirname(readlink(__file__) if islink(__file__) else __file__))
        self.templates_path = pathjoin(self_path, "templates/cpp")


    def _copy_common_files(self):
        self.copy_file("monitor.h")
        self.copy_file("mstring.h")
        self.copy_file("trace.h")
        self.copy_file("inputs.h")
        self.copy_file("workbag.h")
        self.copy_file("cfgset.h")
        self.copy_file("cfg.h")
        self.copy_file("prefixexpr.h")
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

    def _generate_pe(self, pe, name, wr):
        print(name, pe)
        pet = PrefixExpressionTransducer.from_pe(pe)
        pet.dump()
        labels = set()
        wr(f"struct {name} : public PrefixExpression {{\n\n")

        wr("  PEStepResult step(const TraceEvent *ev, size_t pos) {\n"
           "    switch (state) {\n")
        for state in pet.states.values():
            wr(f"      case {state.id}: {{ // {state}\n")
            for l, succ in state.successors.items():
                if isinstance(l, Event) and l.params:
                    raise NotImplementedError(f"Parameters binding not supported yet: {l}")

                ## OPTIMIZATION 1: successors of the accepting and rejecting states are BOT
                if state.pe.is_empty() or state.pe.is_bot():
                    wr(f"        return PEStepResult::Reject;\n")
                    break

                evkind = ev_kind(l)
                wr(f"        if ((Kind)ev->kind() == Kind::{evkind}) {{ // {l}\n")
                if succ[1]: # output
                    wr(f"          // output: {succ[1]};\n")
                    for label, pos in succ[1].items():
                        labels.add(label)
                        for p in pos:
                            wr("          ")
                            wr(self.codemapper.append_mstring(f"mstr_{label.name}",
                                                              map_pos(p[0]),
                                                              map_pos(p[1])))
                            wr(';\n')

                pe = succ[0].pe
                if pe.is_empty(): # is accepting?
                    wr(f"          return PEStepResult::Accept;\n")
                elif pe.is_bot():
                    wr(f"          return PEStepResult::Reject;\n")
                else:
                    wr(f"          state = {succ[0].id};\n")
                wr( "        }\n")
            wr ("        break;\n"
                "        }\n")
           # (Kind)ev->kind()
        #     case Kind::InputL:
        #     case Kind::OutputL:
        #       state = 1;
        #       {codemapper.append_mstring('M', 'pos', 'pos')};
        #       return PEStepResult::Accept;
        wr("    default: abort();\n")
        wr("    }\n"
           "  }\n\n")
        wr("  // TODO: use MStringFixed when possible\n")
        for label in labels:
            wr(f"  MString mstr_{label.name};\n")

        wr("};\n\n")

    def _generate_mpe_cond(self, cond, wr):
        if isinstance(cond, CompareExpr):
            lhs, rhs = cond.lhs, cond.rhs
            if isinstance(lhs, SubWord):
                if isinstance(rhs, SubWord):
                    # compare two subwords
                    ltrace = lhs.lhs.name
                    rtrace = rhs.lhs.name
                    wr(f"    return __subword_compare({ltrace}, pe_{ltrace}.mstr_{lhs.label.name.name},"
                       f" {rtrace}, pe_{rtrace}.mstr_{rhs.label.name.name});\n")
                else:
                    raise NotImplementedError(f"Unhandled condition: {cond}")
            return

        raise NotImplementedError(f"Unhandled condition: {cond}")

    def _generate_mpe(self, transition, wr):
        mpe = transition.mpe
        mpe_name = f"MPE_{transition.start.name}_{transition.end.name}"
        pes = []
        for trace, pe in mpe.exprs.items():
            pe_name = f"{mpe_name}_PE_{trace.name}"
            self._generate_pe(pe, pe_name, wr)
            pes.append((pe_name, trace))
            print(trace, pe)

        wr(f"struct {mpe_name} : MultiTracePrefixExpression<{len(pes)}> {{\n")
        for pe, trace in pes:
            wr(f"  {pe} pe_{trace.name};\n")

        cond = transition.cond
        wr(f"\n  // cond: {cond}\n")
        params = (f"const Trace<TraceEvent> *{trace.name}" for trace in mpe.exprs.keys())
        wr(f"  bool cond({', '.join(params)}) const {{\n")
        self._generate_mpe_cond(cond, wr)
        wr("  }\n\n")
        wr('};\n\n')

    def _generate_cfg(self, transition, cfwr, mfwr):
        self._generate_mpe(transition, mfwr)

    def _generate_cfgs(self, mpt):
        mf = self.new_file("mpes.h")
        cf = self.new_file("cfgs.h")
        mfwr = mf.write
        mfwr('#ifndef OD_MPES_H_\n#define OD_MPES_H_\n\n')
        mfwr('#include "prefixexpr.h"\n\n')

        cfwr = cf.write
        cfwr('#ifndef OD_CFGS_H_\n#define OD_CFGS_H_\n\n')
        cfwr('#include "mpes.h"\n\n')

        for transition in mpt.transitions:
            self._generate_cfg(transition, cfwr, mfwr)

        mfwr('#endif')
        cfwr('#endif')
        mf.close()
        cf.close()


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

            wr('  bool operator==(const TraceEvent &rhs) const {\n'
               '    if (kind() != rhs.kind()) return false;\n'
               '    switch (kind()) {\n'
               '      case (vms_kind)Kind::END: return true;\n')
            for event in mpt.alphabet:
                sname = event.name.name
                wr(f'      case (vms_kind)Kind::{sname}: return data.{sname} == rhs.data.{sname};\n')
            wr(f'      default: abort();\n')
            wr('    }\n  }\n\n')

            wr('  bool operator!=(const TraceEvent &rhs) const { return !operator==(rhs); }\n')
            wr('};\n\n')

            wr('#ifdef DBG\n#include <iostream>\n'
               'std::ostream &operator<<(std::ostream &s, const TraceEvent &ev);\n'
               '#endif\n\n')

            wr('#endif')

    def _generate_monitor_core(self, mpt):
        pass


    def _generate_monitor(self, mpt):
        with self.new_file("monitor.cpp") as f:
            wr = f.write
            wr('#include <iostream>\n')
            wr('#include <cassert>\n\n')

            wr('#include "events.h"\n')
            wr('#include "monitor.h"\n')
            wr('#include "trace.h"\n')
            wr('#include "prefixexpr.h"\n')
            wr('#include "cfgset.h"\n')
            wr('#include "workbag.h"\n')
            wr('#include "inputs.h"\n\n')

            wr('#include "cfgs.h"\n\n')

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
        self._generate_cfgs(mpt)
        self._generate_monitor(mpt)

