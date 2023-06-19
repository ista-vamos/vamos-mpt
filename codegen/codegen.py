from os import mkdir, readlink
from os.path import join as pathjoin, abspath, dirname, islink, basename
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
    def __init__(self, args, outputdir="/tmp/mpt/", codemapper=None):
        if codemapper is None:
            self.codemapper = CodeMapper()
        else:
            self.codemapper = codemapper

        self.args  = args
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
        if name in self.args.overwrite_default:
            filename = "/dev/null"
        else:
            filename = pathjoin(self.out_dir, name)
            assert filename not in self.files
            self.files.append(filename)
        return open(filename, "w")

    def gen_config(self, infile, outfile, values):
        if outfile in self.args.overwrite_default:
            return
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
    if pos == "p":
        return "pos"
    if pos is None:
        return "MString::Letter::BOT"

    raise RuntimeError("Unreachable")


class CodeGenCpp(CodeGen):
    def __init__(self, args, outputdir="/tmp/mpt/", codemapper=None):
        super().__init__(args, outputdir, codemapper)
        self_path = abspath(
            dirname(readlink(__file__) if islink(__file__) else __file__)
        )
        self.templates_path = pathjoin(self_path, "templates/cpp")

    def _copy_common_files(self):
        files = ["monitor.h", "mstring.h", "trace.h", "inputs.h",
                 "workbag.h", "cfgset.h", "cfg.h", "prefixexpr.h",
                 "main.cpp", "cfgs.cpp", "mstring.cpp"]
        for f in files:
            if f not in self.args.overwrite_default:
                self.copy_file(f)

        for f in self.args.cpp_files:
            self.copy_file(f)

    def _generate_cmake(self):
        from config import vamos_buffers_DIR, vamos_hyper_DIR

        self.gen_config(
            "CMakeLists.txt.in",
            "CMakeLists.txt",
            {
                "@vamos-buffers_DIR@": vamos_buffers_DIR,
                "@vamos-hyper_DIR@": vamos_hyper_DIR,
                "@additional_sources@": " ".join((basename(f) for f in self.args.cpp_files))
            },
        )

    def _generate_add_cfgs(self, mpt, wr):
        wr("template <typename WorkbagTy, typename TracesT>\n")
        wr(
            "static void add_new_cfgs(WorkbagTy &workbag, const TracesT &traces, Trace<TraceEvent> *trace) {\n"
        )
        wr(f"  ConfigurationsSetTy S;\n")
        wr("  for (auto &t : traces) {\n")
        wr("    /* TODO: reflexivity reduction */\n")
        # #ifdef REDUCT_REFLEXIVITY
        #     if (trace == t.get())
        #       continue;
        # #endif

        wr("    S.clear();\n")
        wr("    // TODO: S.add(...)")
        # S.add(Cfg_1({t.get(), trace}));
        # S.add(Cfg_2({t.get(), trace}));
        # S.add(Cfg_3({t.get(), trace}));
        wr("    workbag.push(std::move(S));\n")

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

        wr(
            "  PEStepResult step(const TraceEvent *ev, size_t pos) {\n"
            "    switch (state) {\n"
        )
        for state in pet.states.values():
            wr(f"      case {state.id}: {{ // {state}\n")
            for l, succ in state.successors.items():
                if isinstance(l, Event) and l.params:
                    raise NotImplementedError(
                        f"Parameters binding not supported yet: {l}"
                    )

                ## OPTIMIZATION 1: successors of the accepting and rejecting states are BOT
                if state.pe.is_empty() or state.pe.is_bot():
                    wr(f"        return PEStepResult::Reject;\n")
                    break

                evkind = ev_kind(l)
                wr(f"        if ((Kind)ev->kind() == Kind::{evkind}) {{ // {l}\n")
                if succ[1]:  # output
                    wr(f"          // output: {succ[1]};\n")
                    for label, pos in succ[1].items():
                        labels.add(label)
                        for p in pos:
                            wr("          ")
                            wr(
                                self.codemapper.append_mstring(
                                    f"mstr_{label.name}", map_pos(p[0]), map_pos(p[1])
                                )
                            )
                            wr(";\n")

                pe = succ[0].pe
                if pe.is_empty():  # is accepting?
                    wr(f"          return PEStepResult::Accept;\n")
                elif pe.is_bot():
                    wr(f"          return PEStepResult::Reject;\n")
                else:
                    wr(f"          state = {succ[0].id};\n")
                wr("        }\n")
            wr("        break;\n" "        }\n")
        # (Kind)ev->kind()
        #     case Kind::InputL:
        #     case Kind::OutputL:
        #       state = 1;
        #       {codemapper.append_mstring('M', 'pos', 'pos')};
        #       return PEStepResult::Accept;
        wr("    default: abort();\n")
        wr("    }\n" "  }\n\n")
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
                    wr(
                        f"    return __subword_compare({ltrace}, pe_{ltrace}.mstr_{lhs.label.name.name},"
                        f" {rtrace}, pe_{rtrace}.mstr_{rhs.label.name.name});\n"
                    )
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
        params = (
            f"const Trace<TraceEvent> *{trace.name}" for trace in mpe.exprs.keys()
        )
        wr(f"  bool cond({', '.join(params)}) const {{\n")
        self._generate_mpe_cond(cond, wr)
        wr("  }\n\n")
        wr("};\n\n")

        return mpe_name

    def _generate_cfg(self, transition, cfwr, mfwr):
        mpe_name = self._generate_mpe(transition, mfwr)
        cfg_name = f"Cfg_{transition.start.name}_{transition.end.name}"
        cfwr(
            f"class {cfg_name} : public Configuration <Trace<TraceEvent>, {len(transition.mpe.exprs)}> {{\n\n"
        )
        cfwr("};\n\n")

        return cfg_name

    def _generate_AnyCfg(self, cfgs, wr):
        """
        This is a union of all configurations. It has smaller overhead than std::variant, so we use this.
        """
        wr("struct AnyCfg {\n" f"  unsigned short _idx{{{len(cfgs)}}};\n\n")
        wr("  auto index() const -> auto{ return _idx; }\n\n")

        wr("  union CfgTy {\n")
        wr("    ConfigurationBase none;\n")
        for cfg in cfgs:
            wr(f"    {cfg} {cfg.lower()};\n")

        wr("\n    CfgTy() : none() {}\n")
        for cfg in cfgs:
            wr(f"    CfgTy({cfg} &&c) : {cfg.lower()}(std::move(c)) {{}}\n")
        wr("  } cfg;\n\n")

        # wr("  template <typename CfgTy> CfgTy &get() { abort(); /*return std::get<CfgTy>(cfg);*/ }\n")
        # for cfg in cfgs:
        #    wr(f"  template <> {cfg} &get() {{ return cfg.{cfg.lower()}; }}\n")

        wr("\n  AnyCfg(){};\n")
        # wr( "  template <typename CfgTy> AnyCfg(CfgTy &&c) : cfg(std::move(c)) { abort(); }\n")
        for n, cfg in enumerate(cfgs):
            wr(f"  AnyCfg({cfg} &&c) : _idx({n}), cfg(std::move(c)) {{}}\n")

        wr("\n  AnyCfg(AnyCfg &&rhs) : _idx(rhs._idx) {\n" "    switch(_idx) {\n")
        for n, cfg in enumerate(cfgs):
            wr(
                f"    case {n}: cfg.{cfg.lower()} = std::move(rhs.cfg.{cfg.lower()}); break;\n"
            )
        wr("    default: break; // do nothing\n" "    }\n  }\n ")

        wr(
            "\n  AnyCfg& operator=(AnyCfg &&rhs) {\n"
            "    _idx = rhs._idx;\n"
            "    switch(_idx) {\n"
        )
        for n, cfg in enumerate(cfgs):
            wr(
                f"    case {n}: cfg.{cfg.lower()} = std::move(rhs.cfg.{cfg.lower()}); break;\n"
            )
        wr(
            "    default: break; // do nothing\n"
            "    }\n"
            "    return *this;\n"
            "  }\n "
        )

        wr("};\n\n")

    def _generate_cfgs(self, mpt):
        mf = self.new_file("mpes.h")
        cf = self.new_file("cfgs.h")
        mfwr = mf.write
        mfwr("#ifndef OD_MPES_H_\n#define OD_MPES_H_\n\n")
        mfwr('#include "trace.h"\n\n')
        mfwr('#include "prefixexpr.h"\n\n')
        mfwr('#include "subword-compare.h"\n\n')

        cfwr = cf.write
        cfwr("#ifndef OD_CFGS_H_\n#define OD_CFGS_H_\n\n")
        cfwr('#include "mpes.h"\n')
        cfwr('#include "cfg.h"\n\n')

        cfgs = []
        for transition in mpt.transitions:
            cfg_name = self._generate_cfg(transition, cfwr, mfwr)
            cfgs.append(cfg_name)

        self._generate_AnyCfg(cfgs, cfwr)

        mfwr("#endif")
        cfwr("#endif")
        mf.close()
        cf.close()

    def _generate_events(self, mpt):
        with self.new_file("events.h") as f:
            wr = f.write
            wr("#ifndef OD_EVENTS_H_\n#define OD_EVENTS_H_\n\n")
            wr("#include <vamos-buffers/cpp/event.h>\n\n")
            wr("using vamos::Event;\n\n")

            wr("enum class Kind : vms_kind {\n")
            wr("  END = Event::doneKind(),\n")
            for n, event in enumerate(mpt.alphabet):
                wr(
                    f'  {event.name.name}{" = Event::firstValidKind()" if n == 0 else ""},\n'
                )
            wr("};\n\n")

            wr("struct TraceEvent : Event {\n")
            wr("  union {\n")
            c_type = self.codemapper.c_type
            for event in mpt.alphabet:
                sname = event.name.name
                wr(f"    struct _{sname} {{\n")
                for field in event.fields:
                    wr(f"      {c_type(field.type)} {field.name.name}; // {field}\n")
                wr(f"      bool operator==(const _{sname}& rhs) const {{\n")
                wr("        return ")
                for n, field in enumerate(event.fields):
                    if n > 0:
                        wr(" && ")
                    wr(f"{field.name.name} == rhs.{field.name.name}")
                wr(";\n      }\n")
                wr(f"    }} {sname};\n")

            wr("  } data;\n\n")

            wr("  TraceEvent() = default;\n")
            wr("  TraceEvent(Kind k, vms_eventid id) : Event((vms_kind)k, id) {}\n")
            wr("  TraceEvent(vms_kind k, vms_eventid id) : Event(k, id) {}\n")

            wr(
                "  bool operator==(const TraceEvent &rhs) const {\n"
                "    if (kind() != rhs.kind()) return false;\n"
                "    switch (kind()) {\n"
                "      case (vms_kind)Kind::END: return true;\n"
            )
            for event in mpt.alphabet:
                sname = event.name.name
                wr(
                    f"      case (vms_kind)Kind::{sname}: return data.{sname} == rhs.data.{sname};\n"
                )
            wr(f"      default: abort();\n")
            wr("    }\n  }\n\n")

            wr(
                "  bool operator!=(const TraceEvent &rhs) const { return !operator==(rhs); }\n"
            )
            wr("};\n\n")

            wr(
                "#ifdef DBG\n#include <iostream>\n"
                "std::ostream &operator<<(std::ostream &s, const TraceEvent &ev);\n"
                "#endif\n\n"
            )

            wr("#endif")

        with self.new_file("events.cpp") as f:
            self.input_file(f, "partials/events_begin.cpp")
            wr = f.write

            wr(
                "std::ostream &operator<<(std::ostream &s, const TraceEvent &ev) {\n"
                '  s << "TraceEvent(" << color_green << std::setw(7) << std::left;\n'
            )

            wr("  switch((Kind)ev.kind()) {\n")
            wr('    case Kind::END: s << "END"; break;\n')
            for event in mpt.alphabet:
                wr(
                    f"    case Kind::{event.name.name}:\n"
                    f'      s << "{event.name.name}";\n'
                )
                if not event.fields:
                    continue

                wr(
                    '      s << color_reset << ", " << color_red << std::setw(2)'
                    " << std::right << ev.id() << color_reset;\n"
                )

                for n, field in enumerate(event.fields):
                    if n > 0:
                        wr(f'      s << ", ";\n')
                    wr(
                        f'      s << "{field.name.name}=" << ev.data.{event.name.name}.{field.name.name};\n'
                    )
                wr(f"      break;\n")

            wr('    default: s << "??"; assert(false && "Invalid kind"); break;\n')
            wr("  }\n")

            wr('  s << ")";\n\n')

            wr("  return s;\n")
            wr("}\n\n")
            wr("#endif\n")

    def _generate_monitor_core(self, mpt):
        pass

    def _generate_monitor(self, mpt):
        with self.new_file("monitor.cpp") as f:
            wr = f.write
            wr("#include <iostream>\n")
            wr("#include <cassert>\n\n")

            wr('#include "events.h"\n')
            wr('#include "monitor.h"\n')
            wr('#include "trace.h"\n')
            wr('#include "prefixexpr.h"\n')
            wr('#include "cfgset.h"\n')
            wr('#include "workbag.h"\n')
            wr('#include "inputs.h"\n\n')

            wr('#include "cfgs.h"\n\n')

            wr(f'using ConfigurationsSetTy = ConfigurationsSet<{mpt.get_max_outdegree()}>;\n\n')

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
