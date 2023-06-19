#ifndef MSTRING_COMPARE_H_
#define MSTRING_COMPARE_H_

#include "events.h"

template <typename TraceT, typename MStringT>
bool __subword_compare(TraceT *t1, const MStringT &m1, TraceT *t2, const MStringT &m2) {
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
    if (*static_cast<const TraceEvent *>(t1->get(pos1)) !=
        *static_cast<const TraceEvent *>(t2->get(pos2)))
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
