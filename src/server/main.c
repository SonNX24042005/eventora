#include "eventora/common/config.h"
#include "eventora/protocol/protocol.h"
#include "eventora/server/server.h"

#include <stdio.h>
#include <string.h>

static void print_usage(void) {
    printf("Cách dùng: eventora_server [--version | --help]\n");
}

int main(int argc, char **argv) {
    if (argc == 2 && strcmp(argv[1], "--version") == 0) {
        printf("eventora_server %s (%s)\n", EVENTORA_VERSION, eventora_protocol_version());
        return 0;
    }
    if (argc == 2 && strcmp(argv[1], "--help") == 0) {
        print_usage();
        return 0;
    }
    if (argc > 1) {
        fprintf(stderr, "Tham số không hợp lệ: %s\n", argv[1]);
        print_usage();
        return 2;
    }

    eventora_server_config_t cfg = eventora_server_config_default();
    if (!eventora_server_config_validate(&cfg)) {
        fprintf(stderr, "Cấu hình mặc định không hợp lệ\n");
        return 1;
    }

    printf("Khung eventora_server %s (%s) sẵn sàng (cổng mặc định %u)\n",
           EVENTORA_VERSION,
           eventora_protocol_version(),
           (unsigned)cfg.port);
    return 0;
}
