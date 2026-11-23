#ifndef EVENTORA_TEST_FRAMEWORK_H
#define EVENTORA_TEST_FRAMEWORK_H

#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

/* Khung kiểm thử đơn vị siêu nhẹ bằng C11, tích hợp trực tiếp với CTest */
static int g_ev_tests_run = 0;
static int g_ev_tests_failed = 0;
static int g_ev_assertions_failed = 0;

#define EV_TEST(name) static void name(void)

#define EV_ASSERT_TRUE(expr)                                                     \
    do {                                                                         \
        if (!(expr)) {                                                           \
            fprintf(stderr, "  [FAIL] %s:%d: kỳ vọng đúng: %s\n",                \
                    __FILE__, __LINE__, #expr);                                  \
            g_ev_assertions_failed++;                                            \
            return;                                                              \
        }                                                                        \
    } while (0)

#define EV_ASSERT_FALSE(expr) EV_ASSERT_TRUE(!(expr))

#define EV_ASSERT_EQ_INT(actual, expected)                                       \
    do {                                                                         \
        int64_t ev_act_ = (int64_t)(actual);                                     \
        int64_t ev_exp_ = (int64_t)(expected);                                   \
        if (ev_act_ != ev_exp_) {                                                \
            fprintf(stderr,                                                      \
                    "  [FAIL] %s:%d: %s == %" PRId64 ", kỳ vọng %" PRId64 "\n",  \
                    __FILE__, __LINE__, #actual, ev_act_, ev_exp_);              \
            g_ev_assertions_failed++;                                            \
            return;                                                              \
        }                                                                        \
    } while (0)

#define EV_ASSERT_EQ_UINT(actual, expected)                                      \
    do {                                                                         \
        uint64_t ev_act_ = (uint64_t)(actual);                                   \
        uint64_t ev_exp_ = (uint64_t)(expected);                                 \
        if (ev_act_ != ev_exp_) {                                                \
            fprintf(stderr,                                                      \
                    "  [FAIL] %s:%d: %s == %" PRIu64 ", kỳ vọng %" PRIu64 "\n",  \
                    __FILE__, __LINE__, #actual, ev_act_, ev_exp_);              \
            g_ev_assertions_failed++;                                            \
            return;                                                              \
        }                                                                        \
    } while (0)

#define EV_ASSERT_EQ_STR(actual, expected)                                       \
    do {                                                                         \
        const char *ev_act_ = (actual);                                          \
        const char *ev_exp_ = (expected);                                        \
        if (ev_act_ == NULL || ev_exp_ == NULL || strcmp(ev_act_, ev_exp_) != 0) { \
            fprintf(stderr,                                                      \
                    "  [FAIL] %s:%d: %s == \"%s\", kỳ vọng \"%s\"\n",            \
                    __FILE__, __LINE__, #actual,                                 \
                    ev_act_ != NULL ? ev_act_ : "(null)",                        \
                    ev_exp_ != NULL ? ev_exp_ : "(null)");                       \
            g_ev_assertions_failed++;                                            \
            return;                                                              \
        }                                                                        \
    } while (0)

#define EV_RUN_TEST(fn)                                                          \
    do {                                                                         \
        int ev_before_ = g_ev_assertions_failed;                                 \
        g_ev_tests_run++;                                                        \
        fn();                                                                    \
        if (g_ev_assertions_failed == ev_before_) {                              \
            printf("[PASS] %s\n", #fn);                                          \
        } else {                                                                 \
            g_ev_tests_failed++;                                                 \
            printf("[FAIL] %s\n", #fn);                                          \
        }                                                                        \
    } while (0)

#define EV_TEST_SUMMARY()                                                        \
    do {                                                                         \
        printf("Kết quả: %d/%d ca đạt\n",                                        \
               g_ev_tests_run - g_ev_tests_failed, g_ev_tests_run);              \
        return (g_ev_tests_failed == 0) ? 0 : 1;                                 \
    } while (0)

#endif /* EVENTORA_TEST_FRAMEWORK_H */
