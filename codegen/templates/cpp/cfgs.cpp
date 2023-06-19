#include <iostream>

#include "cfgs.h"

std::ostream &operator<<(std::ostream &s, const PEStepResult r) {
  switch (r) {
  case PEStepResult::None:
    s << "None";
    break;
  case PEStepResult::Accept:
    s << "Accept";
    break;
  case PEStepResult::Reject:
    s << "Reject";
    break;
  }
  return s;
}
