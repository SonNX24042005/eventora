#ifndef EVENTORA_COMMON_CLOCK_H
#define EVENTORA_COMMON_CLOCK_H

#include <stdint.h>

/* Giao diện đồng hồ có thể thay thế trong unit test (docs/FEATURE_SPEC.md mục 1.3) */
typedef int64_t (*eventora_clock_now_fn)(void *ctx);

typedef struct eventora_clock {
    eventora_clock_now_fn now_fn;
    void *ctx;
} eventora_clock_t;

/* Trả về đồng hồ hệ thống mặc định (Unix timestamp tính bằng giây, UTC) */
eventora_clock_t eventora_clock_system(void);

/* Lấy thời điểm hiện tại theo đồng hồ truyền vào; fallback sang đồng hồ hệ thống nếu NULL */
int64_t eventora_clock_now(const eventora_clock_t *clock);

#endif /* EVENTORA_COMMON_CLOCK_H */
