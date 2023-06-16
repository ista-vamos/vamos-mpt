#ifndef PE_H_
#define PE_H_

#include "mstring.h"

struct PrefixExpression {
  size_t state{0};
  MString M;
};

template <size_t MSTRING_SIZE>
struct PrefixExpressionFixedMString {
  size_t state{0};
  FixedMString<MSTRING_SIZE> M;
};

template <size_t K, typename PETy>
struct MultiTracePrefixExpression {
  bool _accepted[K]{false};
  std::array<PETy, K> _exprs;

  MultiTracePrefixExpression(const std::array<PETy, K> &PEs)
      : _exprs(PEs) {}

  bool cond() const;
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
