#ifndef VAMOS_HYPER_MSTRING_H_
#define VAMOS_HYPER_MSTRING_H_

#include <array>
#include <cstring>
#include <memory>
#include <vector>


class MString {
  static const size_t ARRAY_SIZE = 1;

public:
  struct Letter {
    static const size_t BOT = ~static_cast<size_t>(0);

    size_t start;
    size_t end;
    Letter() = default;
    Letter(size_t s, size_t e) : start(s), end(e) {}

    bool operator==(const Letter &rhs) const {
      return start == rhs.start && end == rhs.end;
    }
    bool operator!=(const Letter &rhs) const { return !(*this == rhs); }

  };

  void append(const MString::Letter &l);
  bool empty() const { return _size == 0; }
  size_t size() const { return _size; }

  bool operator==(const MString &rhs) const {
    if (_size != rhs._size)
      return false;

    if (_size <= ARRAY_SIZE) {
      for (size_t i = 0; i < _size; ++i) {
        if (_data.arr[i] != rhs._data.arr[i]) {
          return false;
        }
      }
      return true;
    }

    return _data.vec == rhs._data.vec;
  }
  bool operator!=(const MString &rhs) const { return !operator==(rhs); }

  Letter &operator[](size_t idx) {
    if (_size <= ARRAY_SIZE) {
      return _data.arr[idx];
    }
    return _data.vec[idx];
  }
  Letter operator[](size_t idx) const {
    if (_size <= ARRAY_SIZE) {
      return _data.arr[idx];
    }
    return _data.vec[idx];
  }

  /*
  auto begin() -> auto { return _data.begin(); }
  auto end() -> auto { return _data.end(); }
  auto begin() const -> auto { return _data.begin(); }
  auto end() const -> auto { return _data.end(); }
  */

  MString() : _size(0) {}
  ~MString() {
    if (_size > ARRAY_SIZE) {
      // destroy the vector
      _data.vec.~vector();
    }
  }
  MString(const MString &rhs) : _size(rhs._size) {
    if (_size <= ARRAY_SIZE) {
      memcpy(_data.arr, rhs._data.arr, _size * sizeof(Letter));
    } else {
      _data.vec = rhs._data.vec;
    }
  }

  /*
  MString &operator=(const MString &rhs) {
    _size = rhs._size;
    if (_size <= ARRAY_SIZE) {
      memcpy(_data.arr, rhs._data.arr, _size * sizeof(Letter));
    } else {
      _data.vec = rhs._data.vec;
    }

    return *this;
  }
  */

  MString &operator=(MString &&rhs) {
    _size = rhs._size;
    if (_size <= ARRAY_SIZE) {
      memcpy(_data.arr, rhs._data.arr, _size * sizeof(Letter));
    } else {
      _data.vec = std::move(rhs._data.vec);
    }

    return *this;
  }

  Letter &back() {
    if (_size <= ARRAY_SIZE) {
      return _data.arr[_size - 1];
    }
    return _data.vec.back();
  }

private:
  size_t _size{0};

  static_assert(ARRAY_SIZE * sizeof(Letter) <= sizeof(std::vector<Letter>),
                "Array is bigger than vec");
  union DataTy {
    Letter arr[ARRAY_SIZE];
    std::vector<Letter> vec;

    DataTy() {}
    ~DataTy() {}
  } _data;

  friend std::ostream &operator<<(std::ostream &s, const MString &ev);
};

template <size_t ARRAY_SIZE>
class FixedMString {
public:
  bool empty() const { return _size == 0; }
  size_t size() const { return _size; }

  void append(const MString::Letter &l) {
    if (_size == 0) {
      assert(l.start != MString::Letter::BOT);
      _data[0] = l;
      ++_size;
      return;
    }

    auto &last = back();
    if (last.end == MString::Letter::BOT) {
      assert(last.end != MString::Letter::BOT);
      assert(l.start != MString::Letter::BOT);
      last.start = l.start;
    } else {
      assert(last.start != MString::Letter::BOT);
      assert(l.start != MString::Letter::BOT);
      assert(_size < ARRAY_SIZE && "OOB write");
      _data[_size++] = l;
    }
  }

  bool operator==(const FixedMString &rhs) const {
    if (_size != rhs._size)
      return false;

    for (size_t i = 0; i < _size; ++i) {
      if (_data[i] != rhs._data[i]) {
        return false;
      }
    }
    return true;
  }
  bool operator!=(const FixedMString &rhs) const { return !operator==(rhs); }

  MString::Letter &operator[](size_t idx) {
    return _data[idx];
  }
  MString::Letter operator[](size_t idx) const {
    return _data[idx];
  }

  FixedMString() {}
  FixedMString(const FixedMString &rhs) : _size(rhs._size) {
    memcpy(_data, rhs._data, _size * sizeof(MString::Letter));
  }

  FixedMString &operator=(FixedMString &&rhs) {
    _size = rhs._size;
    memcpy(_data, rhs._data, _size * sizeof(MString::Letter));
    return *this;
  }

  MString::Letter &back() {
    assert(_size > 0);
    return _data[_size - 1];
  }

private:
  size_t _size{0};
  MString::Letter _data[ARRAY_SIZE];

  //friend std::ostream &operator<<(std::ostream &s, const MString &ev);
};


#define DBG
#ifdef DBG
#include <iostream>
std::ostream &operator<<(std::ostream &s, const MString &ev);
#endif

template <typename TraceT, typename MStringT>
bool match_eq(TraceT *t1, const MStringT &m1, TraceT *t2, const MStringT &m2) {
  assert(!m1.empty() && !m2.empty());

  // std::cout << "match_eq: " << m1 << ", " << m2 << "\n";

  auto pos1 = m1[0].start;
  auto pos2 = m2[0].start;
#ifndef NDEBUG
  const auto Bot = MString::Letter::BOT;
#endif
  size_t m1i = 0;
  size_t m2i = 0;

  while (true) {
    assert(pos1 != Bot);
    assert(pos2 != Bot);
    if (*static_cast<TraceEvent *>(t1->get(pos1)) !=
        *static_cast<TraceEvent *>(t2->get(pos2)))
      return false;

    if (pos1 == m1[m1i].end) {
      ++m1i;
      if (m1.size() == m1i) { // no more positions in m1
        if (pos2 == m2[m2i].end && m2.size() == m2i + 1) {
          // m2 ended as well
          return true;
        } else {
          return false;
        }
      }
      pos1 = m1[m1i].start;
    }
    if (pos2 == m2[m2i].end) {
      ++m2i;
      if (m2.size() == m2i) { // no more positions in m2
        if (pos1 == m1[m1i].end && m1.size() == m1i + 1) {
          // m1 ended as well
          return true;
        } else {
          return false;
        }
      }
      pos2 = m2[m2i].start;
    }
  }

  assert(false && "Unreachable");
  abort();
}
#endif
