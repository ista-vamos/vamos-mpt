// returns true to continue with next CFG
template <typename CfgTy, typename WorkbagTy, size_t TRACES_NUM>
Actions move_cfg(WorkbagTy &workbag, CfgTy &cfg) {
  bool no_progress = true;
  for (size_t idx = 0; idx < TRACES_NUM; ++idx) {
    if (cfg.canProceed(idx)) {
      no_progress = false;
      auto res = cfg.step(idx);
      if (res == PEStepResult::Accept) {
        // std::cout << "CFG " << &c << " from " << &C << " ACCEPTED\n";
        cfg.queueNextConfigurations(workbag);
        return CFGSET_MATCHED;
      }
      if (res == PEStepResult::Reject) {
        // std::cout << "CFG " << &c << " from " << &C << " REJECTED\n";
        return CFG_FAILED;
      }
    }
  }

  if (no_progress) {
    // check if the traces are done
    for (size_t idx = 0; idx < TRACES_NUM; ++idx) {
      if (!cfg.trace(idx)->done())
        return NONE;
    }
    // std::cout << "CFG discarded becase it has read traces entirely\n";
    return CFGSET_DONE;
  }

  return NONE;
}