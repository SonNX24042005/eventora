cmake_minimum_required(VERSION 3.20)

project(eventora VERSION 0.1.0 LANGUAGES C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

option(EVENTORA_ENABLE_COVERAGE "Bật cờ --coverage cho các thư viện lõi để đo độ bao phủ" OFF)
option(EVENTORA_BUILD_TESTS "Biên dịch các bộ unit test và đăng ký CTest" ON)
option(EVENTORA_ENABLE_WERROR "Coi mọi cảnh báo biên dịch là lỗi (-Werror)" OFF)

find_package(Threads REQUIRED)
find_package(SQLite3 REQUIRED)
if(TARGET SQLite3::SQLite3)
    set(EVENTORA_SQLITE3_TARGET SQLite3::SQLite3)
else()
    set(EVENTORA_SQLITE3_TARGET SQLite::SQLite3)
endif()
find_package(OpenSSL REQUIRED COMPONENTS Crypto SSL)

function(eventora_apply_warnings target_name)
    if(CMAKE_C_COMPILER_ID MATCHES "GNU|Clang")
        target_compile_options(${target_name} PRIVATE -Wall -Wextra -Wpedantic)
        if(EVENTORA_ENABLE_WERROR)
            target_compile_options(${target_name} PRIVATE -Werror)
        endif()
    endif()
endfunction()

function(eventora_enable_coverage target_name)
    if(EVENTORA_ENABLE_COVERAGE)
        if(CMAKE_C_COMPILER_ID MATCHES "GNU|Clang")
            target_compile_options(${target_name} PRIVATE -O0 -g --coverage)
            target_link_options(${target_name} PUBLIC --coverage)
        else()
            message(WARNING "EVENTORA_ENABLE_COVERAGE chỉ hỗ trợ trình biên dịch GCC hoặc Clang")
        endif()
    endif()
endfunction()

# 1. Tầng tiện ích dùng chung (common)
add_library(eventora_common STATIC
    src/common/clock.c
)
target_include_directories(eventora_common PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)
eventora_apply_warnings(eventora_common)
eventora_enable_coverage(eventora_common)

# 2. Tầng giao thức và đóng khung bản tin dùng chung (protocol)
add_library(eventora_protocol STATIC
    src/protocol/protocol.c
)
target_include_directories(eventora_protocol PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)
target_link_libraries(eventora_protocol PUBLIC
    eventora_common
)
eventora_apply_warnings(eventora_protocol)
eventora_enable_coverage(eventora_protocol)

# 3. Tầng lõi server (net, storage, service, log sẽ bổ sung dần vào đây)
add_library(eventora_server_core STATIC
    src/server/server_config.c
)
target_include_directories(eventora_server_core PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)
target_link_libraries(eventora_server_core
    PUBLIC
        eventora_protocol
        eventora_common
    PRIVATE
        Threads::Threads
        ${EVENTORA_SQLITE3_TARGET}
        OpenSSL::Crypto
        OpenSSL::SSL
)
eventora_apply_warnings(eventora_server_core)
eventora_enable_coverage(eventora_server_core)

# 4. Thư viện lõi phía client (libeventora_client)
add_library(eventora_client STATIC
    src/client/client.c
)
target_include_directories(eventora_client PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)
target_link_libraries(eventora_client
    PUBLIC
        eventora_protocol
        eventora_common
    PRIVATE
        Threads::Threads
        OpenSSL::Crypto
        OpenSSL::SSL
)
eventora_apply_warnings(eventora_client)
eventora_enable_coverage(eventora_client)

# 5. Chương trình thực thi (server và CLI)
add_executable(eventora_server
    src/server/main.c
)
target_link_libraries(eventora_server PRIVATE
    eventora_server_core
)
eventora_apply_warnings(eventora_server)

add_executable(eventora_cli
    src/cli/main.c
)
target_link_libraries(eventora_cli PRIVATE
    eventora_client
)
eventora_apply_warnings(eventora_cli)

# 6. Kiểm thử đơn vị và kiểm chứng lược đồ qua CTest
if(EVENTORA_BUILD_TESTS)
    enable_testing()

    function(eventora_add_unit_test test_name source_file)
        add_executable(${test_name} ${source_file})
        target_include_directories(${test_name} PRIVATE
            ${CMAKE_CURRENT_SOURCE_DIR}/tests/unit
        )
        target_link_libraries(${test_name} PRIVATE ${ARGN})
        eventora_apply_warnings(${test_name})
        add_test(NAME ${test_name} COMMAND ${test_name})
    endfunction()

    eventora_add_unit_test(unit_common tests/unit/test_common.c eventora_common)
    eventora_add_unit_test(unit_protocol tests/unit/test_protocol.c eventora_protocol)
    eventora_add_unit_test(unit_server_config tests/unit/test_server_config.c eventora_server_core)
    eventora_add_unit_test(unit_client tests/unit/test_client.c eventora_client)

    add_test(NAME smoke_server_version COMMAND eventora_server --version)
    add_test(NAME smoke_cli_version COMMAND eventora_cli --version)

    find_package(Python3 COMPONENTS Interpreter)
    if(Python3_FOUND)
        add_test(
            NAME schema_check
            COMMAND Python3::Interpreter ${CMAKE_CURRENT_SOURCE_DIR}/tests/schema/check_schema.py
        )
    else()
        message(WARNING "Không tìm thấy Python3; bỏ qua bài kiểm chứng lược đồ schema_check trong CTest")
    endif()
endif()

# 7. Mục tiêu tiện ích sinh báo cáo độ bao phủ bằng scripts/coverage.sh
if(EVENTORA_ENABLE_COVERAGE)
    add_custom_target(coverage
        COMMAND ${CMAKE_CURRENT_SOURCE_DIR}/scripts/coverage.sh ${CMAKE_BINARY_DIR} 90
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
        COMMENT "Chạy kiểm thử và xuất báo cáo độ bao phủ LCOV"
        USES_TERMINAL
    )
endif()
