#ifndef OD_EVENTS_H_
#define OD_EVENTS_H_

#include <vamos-buffers/cpp/event.h>

using vamos::Event;

enum class Kind : vms_kind {
  End = Event::doneKind(),
  InputL = Event::firstValidKind(),
  InputH,
  OutputL,
  Write
};

inline const char *kindToStr(Kind k) {
  switch (k) {
  case Kind::InputL:
    return "InputL";
  case Kind::InputH:
    return "InputH";
  case Kind::OutputL:
    return "OutputL";
  case Kind::Write:
    return "Write";
  case Kind::End:
    return "END";
  }
}

struct TraceEvent : Event {
  union {
    struct {
      void *addr;
      uint64_t value;
    } InputL;
    struct {
      void *addr;
      uint64_t value;
    } InputH;
    struct {
      void *addr;
      uint64_t value;
    } OutputL;
    struct {
      void *addr;
      uint64_t value;
    } Write;
  } data;

  TraceEvent() = default;
  TraceEvent(Kind k, vms_eventid id) : Event((vms_kind)k, id) {}
  TraceEvent(vms_kind k, vms_eventid id) : Event(k, id) {}

  bool operator==(const TraceEvent &rhs) const {
    return kind() == rhs.kind() && (kind() == Event::doneKind() ||
                                    (data.Write.value == rhs.data.Write.value &&
                                     data.Write.addr == rhs.data.Write.addr));
  }

  bool operator!=(const TraceEvent &rhs) const { return !operator==(rhs); }
};

struct Event_InputL : public TraceEvent {
  Event_InputL() = default;
  Event_InputL(vms_eventid id, void *addr, uint64_t value)
      : TraceEvent(Kind::InputL, id) {
    data.InputL.addr = addr;
    data.InputL.value = value;
  }

  auto addr() const { return data.InputL.addr; }
  auto value() const { return data.InputL.value; }
};

struct Event_OutputL : public TraceEvent {
  Event_OutputL() = default;
  Event_OutputL(vms_eventid id, void *addr, uint64_t value)
      : TraceEvent(Kind::OutputL, id) {
    data.OutputL.addr = addr;
    data.OutputL.value = value;
  }

  auto addr() const { return data.OutputL.addr; }
  auto value() const { return data.OutputL.value; }
};

struct Event_Write : public TraceEvent {
  Event_Write() = default;
  Event_Write(vms_eventid id, void *addr, uint64_t value)
      : TraceEvent(Kind::Write, id) {
    data.Write.addr = addr;
    data.Write.value = value;
  }

  auto addr() const { return data.Write.addr; }
  auto value() const { return data.Write.value; }
};

#define DBG
#ifdef DBG
#include <iostream>
std::ostream &operator<<(std::ostream &s, const TraceEvent &ev);
#endif

#endif
