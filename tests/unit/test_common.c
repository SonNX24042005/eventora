#include "eventora/common/clock.h"
#include "eventora/common/config.h"
#include "test_framework.h"

#include <stddef.h>

static int64_t fake_clock_now(void *ctx) {
    const int64_t *fixed = (const int64_t *)ctx;
    return *fixed;
}

EV_TEST(test_fake_clock_injection) {
    int64_t fake_now = 1795400000;
    eventora_clock_t clk;
    clk.now_fn = fake_clock_now;
    clk.ctx = &fake_now;

    EV_ASSERT_EQ_INT(eventora_clock_now(&clk), 1795400000);

    fake_now += 3600;
    EV_ASSERT_EQ_INT(eventora_clock_now(&clk), 1795403600);
}

EV_TEST(test_system_clock_and_fallbacks) {
    eventora_clock_t sys = eventora_clock_system();
    EV_ASSERT_TRUE(sys.now_fn != NULL);
    EV_ASSERT_TRUE(eventora_clock_now(&sys) > 0);
    EV_ASSERT_TRUE(eventora_clock_now(NULL) > 0);

    eventora_clock_t empty_clk;
    empty_clk.now_fn = NULL;
    empty_clk.ctx = NULL;
    EV_ASSERT_TRUE(eventora_clock_now(&empty_clk) > 0);
}

EV_TEST(test_default_config_constants) {
    EV_ASSERT_EQ_UINT(EVENTORA_DEFAULT_PORT, 8888U);
    EV_ASSERT_EQ_UINT(EVENTORA_MAX_FRAME_SIZE, 65536U);
    EV_ASSERT_EQ_UINT(EVENTORA_MAX_TX_BUFFER, 1048576U);
    EV_ASSERT_EQ_UINT(EVENTORA_PBKDF2_ITERATIONS, 600000U);
}

int main(void) {
    EV_RUN_TEST(test_fake_clock_injection);
    EV_RUN_TEST(test_system_clock_and_fallbacks);
    EV_RUN_TEST(test_default_config_constants);
    EV_TEST_SUMMARY();
}
