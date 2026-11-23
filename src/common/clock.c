#include "eventora/common/clock.h"

#include <stddef.h>
#include <time.h>

static int64_t system_clock_now(void *ctx) {
    (void)ctx;
    return (int64_t)time(NULL);
}

eventora_clock_t eventora_clock_system(void) {
    eventora_clock_t clock;
    clock.now_fn = system_clock_now;
    clock.ctx = NULL;
    return clock;
}

int64_t eventora_clock_now(const eventora_clock_t *clock) {
    if (clock != NULL && clock->now_fn != NULL) {
        return clock->now_fn(clock->ctx);
    }
    return system_clock_now(NULL);
}
