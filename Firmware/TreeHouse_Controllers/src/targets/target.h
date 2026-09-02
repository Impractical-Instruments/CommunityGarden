// Selects the location this build is for.  platformio.ini defines exactly one
// CG_TARGET_* macro per environment; everything else about a location lives in
// its own header next to this one.
#pragma once

#include "Patterns.h"
#include "net_config.h"

#if defined(CG_TARGET_SWANNATOPIA)
#include "swannatopia.h"
#elif defined(CG_TARGET_JULIA)
#include "julia.h"
#elif defined(CG_TARGET_JESS)
#include "jess.h"
#elif defined(CG_TARGET_DORMER)
#include "dormer.h"
#else
#error "No CG_TARGET_* defined. Build through one of the platformio.ini environments."
#endif
