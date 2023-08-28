
  bool canProceed(size_t idx) const {
    return !mPE.accepted(idx) && trace(idx)->size() > positions[idx];
  }

  PEStepResult step(size_t idx) {
    assert(canProceed(idx) && "Step on invalid PE");

    const TraceEvent *ev = static_cast<const TraceEvent*>(trace(idx)->get(positions[idx]));
    assert(ev && "No event");
    auto res = mPE.step(idx, ev, positions[idx]);

    ++positions[idx];

    switch (res) {
    case PEStepResult::Accept:
      if (mPE.accepted()) {
        if (mPE.cond(trace(0), trace(1))) {
          return PEStepResult::Accept;
        } else {
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

