#ifndef OD_CFGSET_H
#define OD_CFGSET_H

#include <cstddef>
#include <array>

template <typename AnyCfgTy, size_t MAX_SIZE>
struct ConfigurationsSet {
  size_t _size{0};
  bool _invalid{false};
  std::array<AnyCfgTy, MAX_SIZE> _confs;

  /*
  void add(const AnyCfg &c) {
    assert(_size < MAX_SIZE);
    _confs[_size++] = c;
  }
  */

  void add(AnyCfgTy &&c) {
    assert(_size < MAX_SIZE);
    _confs[_size++] = std::move(c);
  }

  void clear() {
    _size = 0;
    assert(!_invalid);
  }

  ConfigurationsSet(const ConfigurationsSet &) = delete;
  ConfigurationsSet(ConfigurationsSet &&) = default;
  ConfigurationsSet& operator=(ConfigurationsSet &&) = default;
  ConfigurationsSet() = default;

  void setInvalid() { _invalid = true; }
  bool invalid() const { return _invalid; }

  auto begin() -> auto{ return _confs.begin(); }
  auto end() -> auto{ return _confs.end(); }
};

#endif // OD_CFGSET_H
