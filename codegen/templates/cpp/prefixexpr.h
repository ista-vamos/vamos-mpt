#ifndef PE_H_
#define PE_H_

#include "mstring.h"

struct PrefixExpression {
  // the state of the PE (transducer)
  size_t state{0};
  // how many characters this PE read
  // size_t pos{0};
};

template <size_t K> struct MultiTracePrefixExpression {
  bool _accepted[K]{false};

  bool accepted(size_t idx) const { return _accepted[idx]; }
  bool accepted() const {
    for (bool a : _accepted) {
      if (!a) {
        return false;
      }
    }
    return true;
  }
};

enum class PEStepResult { None = 1, Accept = 2, Reject = 3 };

#endif
