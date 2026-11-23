#include "eventora/protocol/protocol.h"
#include "test_framework.h"

EV_TEST(test_protocol_version) {
    EV_ASSERT_EQ_STR(eventora_protocol_version(), "eventora/1");
}

EV_TEST(test_frame_status_strings) {
    EV_ASSERT_EQ_STR(eventora_frame_status_str(EVENTORA_FRAME_OK), "OK");
    EV_ASSERT_EQ_STR(eventora_frame_status_str(EVENTORA_FRAME_INCOMPLETE), "INCOMPLETE");
    EV_ASSERT_EQ_STR(eventora_frame_status_str(EVENTORA_FRAME_TOO_LARGE), "FRAME_TOO_LARGE");
    EV_ASSERT_EQ_STR(eventora_frame_status_str(EVENTORA_FRAME_MALFORMED), "MALFORMED_FRAME");
    EV_ASSERT_EQ_STR(eventora_frame_status_str((eventora_frame_status_t)99), "UNKNOWN");
}

int main(void) {
    EV_RUN_TEST(test_protocol_version);
    EV_RUN_TEST(test_frame_status_strings);
    EV_TEST_SUMMARY();
}
