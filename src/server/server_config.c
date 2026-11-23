#include "eventora/server/server.h"

#include "eventora/common/config.h"

eventora_server_config_t eventora_server_config_default(void) {
    eventora_server_config_t cfg;
    cfg.bind_addr = EVENTORA_DEFAULT_BIND_ADDR;
    cfg.port = (uint16_t)EVENTORA_DEFAULT_PORT;
    cfg.thread_pool_size = EVENTORA_THREAD_POOL_SIZE;
    cfg.auth_pool_size = EVENTORA_AUTH_POOL_SIZE;
    cfg.max_clients = EVENTORA_MAX_CLIENTS;
    cfg.db_path = EVENTORA_DEFAULT_DB_PATH;
    cfg.log_path = EVENTORA_DEFAULT_LOG_PATH;
    return cfg;
}

bool eventora_server_config_validate(const eventora_server_config_t *cfg) {
    if (cfg == NULL) {
        return false;
    }
    if (cfg->bind_addr == NULL || cfg->bind_addr[0] == '\0') {
        return false;
    }
    if (cfg->port == 0U) {
        return false;
    }
    if (cfg->thread_pool_size < EVENTORA_THREAD_POOL_MIN ||
        cfg->thread_pool_size > EVENTORA_THREAD_POOL_MAX) {
        return false;
    }
    if (cfg->auth_pool_size == 0U) {
        return false;
    }
    if (cfg->max_clients == 0U) {
        return false;
    }
    if (cfg->db_path == NULL || cfg->db_path[0] == '\0') {
        return false;
    }
    if (cfg->log_path == NULL || cfg->log_path[0] == '\0') {
        return false;
    }
    return true;
}
