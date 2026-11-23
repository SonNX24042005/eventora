#include "eventora/client/client.h"
#include "eventora/protocol/protocol.h"

#include <stdio.h>
#include <string.h>

static void print_usage(void) {
    printf("Cách dùng: eventora_cli [--version | --help]\n");
}

int main(int argc, char **argv) {
    if (argc == 2 && strcmp(argv[1], "--version") == 0) {
        printf("eventora_cli %s (%s)\n", eventora_client_version(), eventora_protocol_version());
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

    eventora_client_config_t cfg = eventora_client_config_default();
    if (!eventora_client_config_validate(&cfg)) {
        fprintf(stderr, "Cấu hình client mặc định không hợp lệ\n");
        return 1;
    }

    printf("Khung eventora_cli %s (%s) sẵn sàng (mặc định %s:%u)\n",
           eventora_client_version(),
           eventora_protocol_version(),
           cfg.host,
           (unsigned)cfg.port);
    return 0;
}
