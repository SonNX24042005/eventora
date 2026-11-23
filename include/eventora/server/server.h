#ifndef EVENTORA_SERVER_SERVER_H
#define EVENTORA_SERVER_SERVER_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/* Cấu hình khởi chạy eventora_server theo docs/FEATURE_SPEC.md mục 2.7 */
typedef struct eventora_server_config {
    const char *bind_addr;
    uint16_t port;
    size_t thread_pool_size;
    size_t auth_pool_size;
    size_t max_clients;
    const char *db_path;
    const char *log_path;
} eventora_server_config_t;

/* Khởi tạo cấu hình server với các giá trị mặc định */
eventora_server_config_t eventora_server_config_default(void);

/* Kiểm tra tính hợp lệ của cấu hình server trước khi khởi động */
bool eventora_server_config_validate(const eventora_server_config_t *cfg);

#endif /* EVENTORA_SERVER_SERVER_H */
