#ifndef EVENTORA_CLIENT_CLIENT_H
#define EVENTORA_CLIENT_CLIENT_H

#include <stdbool.h>
#include <stdint.h>

/* Cấu hình kết nối của thư viện lõi libeventora_client */
typedef struct eventora_client_config {
    const char *host;
    uint16_t port;
    uint32_t ping_interval_sec;
} eventora_client_config_t;

/* Khởi tạo cấu hình mặc định cho libeventora_client */
eventora_client_config_t eventora_client_config_default(void);

/* Kiểm tra tính hợp lệ của cấu hình client */
bool eventora_client_config_validate(const eventora_client_config_t *cfg);

/* Trả về phiên bản hiện tại của libeventora_client */
const char *eventora_client_version(void);

#endif /* EVENTORA_CLIENT_CLIENT_H */
