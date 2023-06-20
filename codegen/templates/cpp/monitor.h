#ifndef MONITOR_H_
#define MONITOR_H_

enum Actions {
  NONE,
  CFGSET_MATCHED,
  CFG_FAILED,
  CFGSET_DONE,
};

inline const char *actionToStr(Actions a) {
  switch(a) {
    case NONE: return "NONE";
    case CFGSET_MATCHED: return "CFGSET_MATCHED";
    case CFGSET_DONE: return "CFGSET_DONE";
    case CFG_FAILED: return "CFG_FAILED";
    default: return "<unknown action>";
  }
}

#endif
