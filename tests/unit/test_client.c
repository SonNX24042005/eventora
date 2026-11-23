#include "eventora/client/client.h"
#include "eventora/common/config.h"
#include "test_framework.h"

#include <stddef.h>

EV_TEST(test_client_defaults_and_version) {
    eventora_client_config_t cfg = eventora_client_config_default();
    EV_ASSERT_EQ_STR(cfg.host, "127.0.0.1");
    EV_ASSERT_EQ_UINT(cfg.port, EVENTORA_DEFAULT_PORT);
    EV_ASSERT_EQ_UINT(cfg.ping_interval_sec, EVENTORA_CLIENT_PING_INTERVAL_SEC);
    EV_ASSERT_TRUE(eventora_client_config_validate(&cfg));
    EV_ASSERT_EQ_STR(eventora_client_version(), EVENTORA_VERSION);
}

EV_TEST(test_client_config_validation_failures) {
    EV_ASSERT_FALSE(eventora_client_config_validate(NULL));

    eventora_client_config_t cfg = eventora_client_config_default();
    cfg.host = NULL;
    EV_ASSERT_FALSE(eventora_client_config_validate(&cfg));

    cfg = eventora_client_config_default();
    cfg.host = "";
    EV_ASSERT_FALSE(eventora_client_config_validate(&cfg));

    cfg = eventora_client_config_default();
    cfg.port = 0U;
    EV_ASSERT_FALSE(eventora_client_config_validate(&cfg));

    cfg = eventora_client_config_default();
    cfg.ping_interval_sec = 0U;
    EV_ASSERT_FALSE(eventora_client_config_validate(&cfg));
}

int main(void) {
    EV_RUN_TEST(test_client_defaults_and_version);
    EV_RUN_TEST(test_client_config_validation_failures);
    EV_TEST_SUMMARY();
}
