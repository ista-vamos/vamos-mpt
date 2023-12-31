#include <cassert>

#include "events.h"
#include "mstring.h"

void MString::append(const MString::Letter &l) {
  if (_size == 0) {
    assert(l.start != MString::Letter::BOT);
    _data.arr[0] = l;
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
    ++_size;
    if (_size <= ARRAY_SIZE) {
      _data.arr[_size - 1] = l;
    } else {
      _data.vec.push_back(l);
    }
  }
}

#ifdef DBG
#include <iomanip>
#include <iostream>

static const char *color_green = "\033[0;32m";
static const char *color_red = "\033[0;31m";
static const char *color_reset = "\033[0m";

std::ostream &operator<<(std::ostream &s, const MString &ev) {
  auto sz = ev.size();
  for (size_t i = 0; i < sz; ++i) {
    const auto &l = ev[i];
    s << "(";
    if (l.start == MString::Letter::BOT)
      s << "⊥";
    else
      s << l.start;
    s << ", ";
    if (l.end == MString::Letter::BOT)
      s << "⊥";
    else
      s << l.end;
    s << ")";
  }
  return s;
}

#endif
