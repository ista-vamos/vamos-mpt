#ifndef CFH_H_
#define CFH_H_

class ConfigurationBase {};

template <typename TraceTy, size_t K>
class Configuration : public ConfigurationBase {
protected:
  bool _failed{false};
  size_t positions[K] = {0};
  std::array<TraceTy *, K> traces;

public:
  Configuration() {}
  ~Configuration() {}
  // Configuration& operator=(const Configuration&) = default;
  Configuration(const std::array<TraceTy *, K> &tr) : traces(tr) {}
  Configuration(const std::array<TraceTy *, K> &tr, size_t pos[K])
    : traces(tr) {
    for (unsigned i = 0; i < K; ++i) {
        positions[i] = pos[i];
    }
  }

  TraceTy *trace(size_t idx) { return traces[idx]; }
  const TraceTy *trace(size_t idx) const { return traces[idx]; }

  bool failed() const { return _failed; }
};

#endif