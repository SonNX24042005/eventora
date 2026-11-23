#include "eventora/common/config.h"
#include "eventora/server/server.h"
#include "test_framework.h"

#include <stddef.h>

EV_TEST(test_server_config_defaults) {
    eventora_server_config_t cfg = eventora_server_config_default();
    EV_ASSERT_EQ_STR(cfg.bind_addr, EVENTORA_DEFAULT_BIND_ADDR);
    EV_ASSERT_EQ_UINT(cfg.port, EVENTORA_DEFAULT_PORT);
    EV_ASSERT_EQ_UINT(cfg.thread_pool_size, EVENTORA_THREAD_POOL_SIZE);
    EV_ASSERT_EQ_UINT(cfg.auth_pool_size, EVENTORA_AUTH_POOL_SIZE);
    EV_ASSERT_EQ_UINT(cfg.max_clients, EVENTORA_MAX_CLIENTS);
    EV_ASSERT_EQ_STR(cfg.db_path, EVENTORA_DEFAULT_DB_PATH);
    EV_ASSERT_EQ_STR(cfg.log_path, EVENTORA_DEFAULT_LOG_PATH);
    EV_ASSERT_TRUE(eventora_server_config_validate(&cfg));
}

EV_TEST(test_server_config_validation_failures) {
    EV_ASSERT_FALSE(eventora_server_config_validate(NULL));

    eventora_server_config_t cfg = eventora_server_config_default();
    cfg.bind_addr = NULL;
    EV_ASSERT_FALSE(eventora_server_config_validate(&cfg));

    cfg = eventora_server_config_default();
    cfg.bind_addr = "";
    EV_ASSERT_FALSE(eventora_server_config_validate(&cfg));

    cfg = eventora_server_config_default();
    cfg.port = 0U;
    EV_ASSERT_FALSE(eventora_server_config_validate(&cfg));

    cfg = eventora_server_config_default();
    cfg.thread_pool_size = EVENTORA_THREAD_POOL_MIN - 1U;
    EV_ASSERT_FALSE(eventora_server_config_validate(&cfg));

    cfg = eventora_server_config_default();
    cfg.thread_pool_size = EVENTORA_THREAD_POOL_MAX + 1U;
    EV_ASSERT_FALSE(eventora_server_config_validate(&cfg));

    cfg = eventora_server_config_default();
    cfg.auth_pool_size = 0U;
    EV_ASSERT_FALSE(eventora_server_config_validate(&cfg));

    cfg = eventora_server_config_default();
    cfg.max_clients = 0U;
    EV_ASSERT_FALSE(eventora_server_config_validate(&cfg));

    cfg = eventora_server_config_default();
    cfg.db_path = NULL;
    EV_ASSERT_FALSE(eventora_server_config_validate(&cfg));

    cfg = eventora_server_config_default();
    cfg.db_path = "";
    EV_ASSERT_FALSE(eventora_server_config_validate(&cfg));

    cfg = eventora_server_config_default();
    cfg.log_path = NULL;
    EV_ASSERT_FALSE(eventora_server_config_validate(&cfg));

    cfg = eventora_server_config_default();
    cfg.log_path = "";
    EV_ASSERT_FALSE(eventora_server_config_validate(&cfg));
}

int main(void) {
    EV_RUN_TEST(test_server_config_defaults);
    EV_RUN_TEST(test_server_config_validation_failures);
    EV_TEST_SUMMARY();
}
