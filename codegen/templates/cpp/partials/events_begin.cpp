#include <cassert>

#include "monitor.h"
#include "mstring.h"
#include "events.h"

#ifdef DBG
#include <iomanip>
#include <iostream>

static const char *color_green = "\033[0;32m";
static const char *color_red = "\033[0;31m";
static const char *color_reset = "\033[0m";

