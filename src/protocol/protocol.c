#include "eventora/protocol/protocol.h"

#include "eventora/common/config.h"

const char *eventora_protocol_version(void) {
    return EVENTORA_PROTOCOL_VERSION;
}

const char *eventora_frame_status_str(eventora_frame_status_t status) {
    switch (status) {
        case EVENTORA_FRAME_OK:
            return "OK";
        case EVENTORA_FRAME_INCOMPLETE:
            return "INCOMPLETE";
        case EVENTORA_FRAME_TOO_LARGE:
            return "FRAME_TOO_LARGE";
        case EVENTORA_FRAME_MALFORMED:
            return "MALFORMED_FRAME";
        default:
            return "UNKNOWN";
    }
}
