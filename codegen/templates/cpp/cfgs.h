#ifndef OD_CFGS_H_
#define OD_CFGS_H_

#include <cassert>
#include <vamos-buffers/cpp/event.h>

#include "monitor.h"
#include "mstring.h"
#include "events.h"

// #define DEBUG

enum class PEStepResult { None = 1, Accept = 2, Reject = 3 };

std::ostream &operator<<(std::ostream &s, const PEStepResult r);

class Workbag;

struct PE1 : public PrefixExpression {
  PEStepResult step(const Event *ev, size_t pos) {
    const auto *e = static_cast<const TraceEvent *>(ev);

    switch ((Kind)e->kind()) {
    case Kind::InputL:
    case Kind::OutputL:
      state = 1;
      M.append(MString::Letter(pos, pos));
      return PEStepResult::Accept;
    default:
      assert(state == 0);
      return PEStepResult::None;
    }
  }
};

struct PE2 : public PrefixExpression {
  PEStepResult step(const Event *ev, size_t pos) {
    const auto *e = static_cast<const TraceEvent *>(ev);

    switch ((Kind)e->kind()) {
    case Kind::OutputL:
    case Kind::End:
      state = 1;
      M.append(MString::Letter(pos, pos));
      return PEStepResult::Accept;
    default:
      assert(state == 0);
      return PEStepResult::None;
    }
  }
};

struct PE3 : public PrefixExpression {
  PEStepResult step(const Event *ev, size_t pos) {
    const auto *e = static_cast<const TraceEvent *>(ev);

    switch ((Kind)e->kind()) {
    case Kind::InputL:
      state = 1;
      M.append(MString::Letter(pos, pos));
      return PEStepResult::Accept;
    default:
      assert(state == 0);
      return PEStepResult::None;
    }
  }
};

struct mPE_1 : public MultiTracePrefixExpression<2> {

  mPE_1() : MultiTracePrefixExpression<2>({PE1(), PE1()}) {}

  PEStepResult step(size_t idx, const Event *ev, size_t pos) {
    assert(idx < 2);
    auto res = static_cast<PE1 *>(&_exprs[idx])->step(ev, pos);
    if (res == PEStepResult::Accept)
      _accepted[idx] = true;
    return res;
  }

  template <typename TraceT> bool cond(TraceT *t1, TraceT *t2) const {
    return match_eq(t1, _exprs[0].M, t2, _exprs[1].M);
  }
};

struct mPE_2 : public MultiTracePrefixExpression<2> {

  mPE_2() : MultiTracePrefixExpression<2>({PE2(), PE2()}) {}

  PEStepResult step(size_t idx, const Event *ev, size_t pos) {
    assert(idx < 2);
    auto res = static_cast<PE2 *>(&_exprs[idx])->step(ev, pos);
    if (res == PEStepResult::Accept)
      _accepted[idx] = true;
    return res;
  }

  template <typename TraceT> bool cond(TraceT *t1, TraceT *t2) const {
    return !match_eq(t1, _exprs[0].M, t2, _exprs[1].M);
  }
};

struct mPE_3 : public MultiTracePrefixExpression<2> {

  mPE_3() : MultiTracePrefixExpression<2>({PE3(), PE3()}) {}

  PEStepResult step(size_t idx, const Event *ev, size_t pos) {
    assert(idx < 2);
    auto res = static_cast<PE3 *>(&_exprs[idx])->step(ev, pos);
    if (res == PEStepResult::Accept)
      _accepted[idx] = true;
    return res;
  }

  template <typename TraceT> bool cond(TraceT *t1, TraceT *t2) const {
    return !match_eq(t1, _exprs[0].M, t2, _exprs[1].M);
  }
};

class ConfigurationBase {};

template <typename TraceTy, size_t K>
class Configuration : public ConfigurationBase {
protected:
  bool _failed{false};
  size_t positions[K] = {0};
  std::array<TraceTy *, K> traces;

public:
  Configuration() {}
  // Configuration& operator=(const Configuration&) = default;
  Configuration(const std::array<TraceTy *, K> &tr) : traces(tr) {}

  TraceTy *trace(size_t idx) { return traces[idx]; }
  const TraceTy *trace(size_t idx) const { return traces[idx]; }

  bool failed() const { return _failed; }
};

template <typename MpeTy>
class CfgTemplate : public Configuration<Trace<TraceEvent>, 2> {
protected:
  MpeTy mPE{};

public:
  bool canProceed(size_t idx) const {
    return !mPE.accepted(idx) && trace(idx)->size() > positions[idx];
  }

  void queueNextConfigurations(Workbag &) { /* no next configurations */
  }

  PEStepResult step(size_t idx) {
    assert(canProceed(idx) && "Step on invalid PE");

    const Event *ev = trace(idx)->get(positions[idx]);
    assert(ev && "No event");
    auto res = mPE.step(idx, ev, positions[idx]);

    assert(static_cast<const TraceEvent *>(ev)->data.InputL.addr != 0 ||
           ev->is_done());
#ifdef DEBUG
    std::cout << "Cfg[" << this << "](tau_" << idx << ") t" << trace(idx)->id()
              << "[" << positions[idx] << "]"
              << "@" << *static_cast<const TraceEvent *>(ev) << ", "
              << positions[idx] << " => " << res << "\n";
#endif

    ++positions[idx];

    switch (res) {
    case PEStepResult::Accept:
      if (mPE.accepted()) {
        // std::cout << "mPE matched prefixes\n";
        if (mPE.cond(trace(0), trace(1))) {
          // std::cout << "Condition SAT!\n";
          return PEStepResult::Accept;
        } else {
          // std::cout << "Condition UNSAT!\n";
          _failed = true;
          return PEStepResult::Reject;
        }
      }
      return PEStepResult::None;
    case PEStepResult::Reject:
      _failed = true;
      // fall-through
    default:
      return res;
    }
  }

  CfgTemplate() {}
  // CfgTemplate& operator=(const CfgTemplate&) = default;
  CfgTemplate(const std::array<Trace<TraceEvent> *, 2> &traces)
      : Configuration(traces) {}

  CfgTemplate(const std::array<Trace<TraceEvent> *, 2> &traces,
              const size_t pos[2])
      : Configuration(traces) {
    positions[0] = pos[0];
    positions[1] = pos[1];
  }
};

struct Cfg_1 : public CfgTemplate<mPE_1> {
  Cfg_1(){};
  // Cfg_1& operator=(const Cfg_1&) = default;
  Cfg_1(const std::array<Trace<TraceEvent> *, 2> &traces)
      : CfgTemplate(traces) {}

  Cfg_1(const std::array<Trace<TraceEvent> *, 2> &traces, const size_t pos[2])
      : CfgTemplate(traces, pos) {}

  void queueNextConfigurations(Workbag &);
};

struct Cfg_2 : public CfgTemplate<mPE_2> {
  Cfg_2(){};
  Cfg_2(const std::array<Trace<TraceEvent> *, 2> &traces)
      : CfgTemplate(traces) {}

  Cfg_2(const std::array<Trace<TraceEvent> *, 2> &traces, const size_t pos[2])
      : CfgTemplate(traces, pos) {}
};

struct Cfg_3 : public CfgTemplate<mPE_3> {
  Cfg_3(){};
  Cfg_3(const std::array<Trace<TraceEvent> *, 2> &traces)
      : CfgTemplate(traces) {}

  Cfg_3(const std::array<Trace<TraceEvent> *, 2> &traces, const size_t pos[2])
      : CfgTemplate(traces, pos) {}
};


struct AnyCfg {
  unsigned short _idx{3};
  union CfgTy {
      Cfg_1 cfg1;
      Cfg_2 cfg2;
      Cfg_3 cfg3;
      ConfigurationBase none;

      CfgTy() : none() {}
      CfgTy(Cfg_1 &&c) : cfg1(std::move(c)) {}
      CfgTy(Cfg_2 &&c) : cfg2(std::move(c)) {}
      CfgTy(Cfg_3 &&c) : cfg3(std::move(c)) {}
  } cfg;

  template <typename CfgTy> CfgTy &get() { abort(); /*return std::get<CfgTy>(cfg);*/ }
  template <> Cfg_1 &get() { return cfg.cfg1; }
  template <> Cfg_2 &get() { return cfg.cfg2; }
  template <> Cfg_3 &get() { return cfg.cfg3; }

  auto index() const -> auto{ return _idx; }

  AnyCfg(){};
  /*
  template <typename CfgTy> AnyCfg(const CfgTy &c) : cfg(c) {}
  AnyCfg(const AnyCfg &rhs) = default;
  AnyCfg &operator=(const AnyCfg &rhs) {
    cfg = rhs.cfg;
    return *this;
  }
  */
  template <typename CfgTy> AnyCfg(CfgTy &&c) : cfg(std::move(c)) { abort(); }
  template <> AnyCfg(Cfg_1 &&c) : _idx(0), cfg(std::move(c)) { }
  template <> AnyCfg(Cfg_2 &&c) : _idx(1), cfg(std::move(c)) { }
  template <> AnyCfg(Cfg_3 &&c) : _idx(2), cfg(std::move(c)) { }

  AnyCfg(AnyCfg &&rhs) : _idx(rhs._idx) {
      switch(_idx) {
      case 0: cfg.cfg1 = std::move(rhs.cfg.cfg1); break;
      case 1: cfg.cfg2 = std::move(rhs.cfg.cfg2); break;
      case 2: cfg.cfg3 = std::move(rhs.cfg.cfg3); break;
      default: break; // do nothing
      }
  };

  AnyCfg &operator=(AnyCfg &&rhs) {
       _idx = rhs._idx;
      switch(_idx) {
      case 0: cfg.cfg1 = std::move(rhs.cfg.cfg1); break;
      case 1: cfg.cfg2 = std::move(rhs.cfg.cfg2); break;
      case 2: cfg.cfg3 = std::move(rhs.cfg.cfg3); break;
      default: break; // do nothing
      }
    return *this;
  }
};


#endif
