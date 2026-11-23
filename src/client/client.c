#include "eventora/client/client.h"

#include "eventora/common/config.h"

#include <stddef.h>

eventora_client_config_t eventora_client_config_default(void) {
    eventora_client_config_t cfg;
    cfg.host = "127.0.0.1";
    cfg.port = (uint16_t)EVENTORA_DEFAULT_PORT;
    cfg.ping_interval_sec = EVENTORA_CLIENT_PING_INTERVAL_SEC;
    return cfg;
}

bool eventora_client_config_validate(const eventora_client_config_t *cfg) {
    if (cfg == NULL) {
        return false;
    }
    if (cfg->host == NULL || cfg->host[0] == '\0') {
        return false;
    }
    if (cfg->port == 0U) {
        return false;
    }
    if (cfg->ping_interval_sec == 0U) {
        return false;
    }
    return true;
}

const char *eventora_client_version(void) {
    return EVENTORA_VERSION;
}
