#ifndef EVENTORA_PROTOCOL_PROTOCOL_H
#define EVENTORA_PROTOCOL_PROTOCOL_H

/* Trạng thái kết quả tách khung bản tin theo dòng (FEAT-01) */
typedef enum eventora_frame_status {
    EVENTORA_FRAME_OK = 0,
    EVENTORA_FRAME_INCOMPLETE = 1,
    EVENTORA_FRAME_TOO_LARGE = -1,
    EVENTORA_FRAME_MALFORMED = -2
} eventora_frame_status_t;

/* Trả về tên phiên bản giao thức hiện hành ("eventora/1") */
const char *eventora_protocol_version(void);

/* Chuyển mã trạng thái tách khung thành chuỗi đọc được để ghi log hoặc kiểm thử */
const char *eventora_frame_status_str(eventora_frame_status_t status);

#endif /* EVENTORA_PROTOCOL_PROTOCOL_H */
