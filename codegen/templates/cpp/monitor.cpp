#include <cassert>
#include <variant>

#include "monitor.h"
#include "cfgs.h"
#include "cfgset.h"
#include "events.h"
#include "workbag.h"
#include "update_traces.h"

//#define OUTPUT

// #include <iostream>
//struct Stats {
//  size_t max_wbg_size{0};
//  size_t cfgs_num{0};
//};

template <typename TracesT>
static void add_new_cfgs(Workbag &workbag, const TracesT &traces,
                         Trace<TraceEvent> *trace) {
  // set initially all elements to 'trace'
  ConfigurationsSet<3> S;

  for (auto &t : traces) {
    /* reflexivity reduction */
#ifdef REDUCT_REFLEXIVITY
    if (trace == t.get())
      continue;
#endif

    S.clear();
    S.add(Cfg_1({t.get(), trace}));
    S.add(Cfg_2({t.get(), trace}));
    S.add(Cfg_3({t.get(), trace}));
    workbag.push(std::move(S));

#ifdef REDUCT_SYMMETRY
    S.clear();
    S.add(Cfg_1({trace, t.get()}));
    S.add(Cfg_2({trace, t.get()}));
    S.add(Cfg_3({trace, t.get()}));
    workbag.push(std::move(S));
#endif
  }
}



int monitor(Inputs &inputs) {

  std::vector<std::unique_ptr<Trace<TraceEvent>>> traces;
  std::vector<InputStream *> online_traces;

  Workbag workbag;
  Workbag new_workbag;


#define STATS
#ifdef STATS
  //Stats stats;
  size_t max_wbg_size = 0;
  //size_t tuples_num = 0;
#endif

  while (true) {
    /////////////////////////////////
    /// UPDATE TRACES (NEW TRACES AND NEW EVENTS)
    /////////////////////////////////

    update_traces(inputs, workbag, traces, online_traces);

    /////////////////////////////////
    /// MOVE TRANSDUCERS
    /////////////////////////////////

    size_t wbg_size = workbag.size();
    size_t wbg_invalid = 0;
#ifdef STATS
    max_wbg_size = std::max(wbg_size, max_wbg_size);
#endif
#ifdef DEBUG
    std::cout << "WORKBAG size: " << wbg_size << "\n";
#endif

    for (auto &C : workbag) {
      if (C.invalid()) {
        ++wbg_invalid;
      }

      bool non_empty = false;
      for (auto &c : C) {
        switch (c.index()) {
        case 0: /* Cfg_1 */ {
          auto &cfg = c.get<Cfg_1>();
          if (cfg.failed())
            continue;
          non_empty = true;

          switch (move_cfg<Cfg_1>(new_workbag, cfg)) {
          case CFGSET_DONE:
          case CFGSET_MATCHED:
            C.setInvalid();
            ++wbg_invalid;
            goto outer_loop;
            break;
          case NONE:
          case CFG_FAILED:
            // remove c from C
            break;
          }
          break;
        }
        case 1: /* Cfg_2 */ {
          auto &cfg = c.get<Cfg_2>();
          if (cfg.failed())
            continue;
          non_empty = true;

          switch (move_cfg<Cfg_2>(new_workbag, cfg)) {
          case CFGSET_MATCHED:
#ifdef OUTPUT
            std::cout
                << "\033[1;31mOBSERVATIONAL DETERMINISM VIOLATED!\033[0m\n";
#endif
#ifdef EXIT_ON_ERROR
            goto violated;
#endif
          // fall-through to discard this set of configs
          case CFGSET_DONE:
            C.setInvalid();
            ++wbg_invalid;
            goto outer_loop;
          case NONE:
          case CFG_FAILED:
            // remove c from C
            break;
          }
          break;
        }
        case 2: /* Cfg_3 */ {
          auto &cfg = c.get<Cfg_3>();
          if (cfg.failed())
            continue;
          non_empty = true;

          switch (move_cfg<Cfg_3>(new_workbag, cfg)) {
          case CFGSET_MATCHED:
#ifdef OUTPUT
            std::cout << "OD holds for these traces\n";
#endif
          case CFGSET_DONE:
            C.setInvalid();
            ++wbg_invalid;
            goto outer_loop;
          case NONE:
          case CFG_FAILED:
            // remove c from C
            break;
          }
          break;
        }
        default:
          assert(false && "Unknown configuration");
          abort();
        }
      }

      if (!non_empty)
        C.setInvalid();

    outer_loop:
      (void)1;
    }

    if (!new_workbag.empty() || wbg_invalid >= wbg_size / 3) {
      for (auto &C : workbag) {
        if (C.invalid())
          continue;
        new_workbag.push(std::move(C));
      }
      workbag.swap(new_workbag);
      new_workbag.clear();
    }

    /////////////////////////////////

    if (workbag.empty() && inputs.done()) {
#ifdef OUTPUT
      std::cout << "No more traces to come, workbag empty\n";
      std::cout << "\033[1;32mNO VIOLATION OF OBSERVATIONAL DETERMINISM "
                   "FOUND!\033[0m\n";
#endif
      break;
    }
  }

#ifdef STATS
    std::cout << "Max workbag size: " << max_wbg_size << "\n";
    std::cout << "Traces #: " << traces.size() << "\n";
#endif

  return 0;

violated:
#ifdef STATS
  std::cout << "Max workbag size: " << max_wbg_size << "\n";
  std::cout << "Traces #: " << traces.size() << "\n";
#endif
  return 1;
}
