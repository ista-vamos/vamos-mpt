#ifndef PE_H_
#define PE_H_

struct PrefixExpression {
  size_t state{0};
  FixedMString<1> M;
};

template <size_t K> struct MultiTracePrefixExpression {
  bool _accepted[K]{false};
  std::array<PrefixExpression, K> _exprs;

  MultiTracePrefixExpression(const std::array<PrefixExpression, K> &PEs)
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

#endif
