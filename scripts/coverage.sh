#!/usr/bin/env bash
set -euo pipefail

BUILD_DIR="${1:-build}"
MIN_LINE_COVERAGE="${2:-90}"

for tool in ctest lcov genhtml python3; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "Lỗi: thiếu công cụ '$tool' trong PATH." >&2
        exit 2
    fi
done

if [ ! -d "$BUILD_DIR" ]; then
    echo "Lỗi: thư mục build '$BUILD_DIR' không tồn tại." >&2
    exit 2
fi

LCOV_VER="$(lcov --version | head -n 1)"
LCOV_MAJOR="$(printf '%s\n' "$LCOV_VER" | sed -nE 's/.*version ([0-9]+)\..*/\1/p')"
LCOV_MAJOR="${LCOV_MAJOR:-1}"

if [ "$LCOV_MAJOR" -ge 2 ]; then
    BRANCH_RC=(--rc branch_coverage=1)
    CAPTURE_IGNORE=(--ignore-errors mismatch,gcov,inconsistent,unused,empty)
    MERGE_IGNORE=(--ignore-errors empty,inconsistent,corrupt)
    REMOVE_IGNORE=(--ignore-errors unused,empty,inconsistent)
    SUMMARY_IGNORE=(--ignore-errors empty)
    GENHTML_ARGS=(--branch-coverage --ignore-errors inconsistent,corrupt,source,empty)
else
    BRANCH_RC=(--rc lcov_branch_coverage=1)
    CAPTURE_IGNORE=()
    MERGE_IGNORE=()
    REMOVE_IGNORE=()
    SUMMARY_IGNORE=()
    GENHTML_ARGS=(--branch-coverage)
fi

BASE_INFO="$BUILD_DIR/coverage_base.info"
TEST_INFO="$BUILD_DIR/coverage_test.info"
TOTAL_INFO="$BUILD_DIR/coverage_total.info"
FINAL_INFO="$BUILD_DIR/coverage.info"
HTML_DIR="$BUILD_DIR/coverage_html"

echo "==> Đặt lại bộ đếm coverage và chụp baseline ($LCOV_VER)"
lcov --zerocounters --directory "$BUILD_DIR"
lcov --capture --initial \
    --directory "$BUILD_DIR" \
    --output-file "$BASE_INFO" \
    "${BRANCH_RC[@]}" \
    "${CAPTURE_IGNORE[@]}"

echo "==> Chạy toàn bộ bộ kiểm thử CTest"
ctest --test-dir "$BUILD_DIR" --output-on-failure

echo "==> Thu thập dữ liệu coverage và ghép với baseline"
lcov --capture \
    --directory "$BUILD_DIR" \
    --output-file "$TEST_INFO" \
    "${BRANCH_RC[@]}" \
    "${CAPTURE_IGNORE[@]}"

lcov --add-tracefile "$BASE_INFO" \
    --add-tracefile "$TEST_INFO" \
    --output-file "$TOTAL_INFO" \
    "${BRANCH_RC[@]}" \
    "${MERGE_IGNORE[@]}"

lcov --remove "$TOTAL_INFO" \
    '/usr/*' \
    '*/tests/*' \
    --output-file "$FINAL_INFO" \
    "${BRANCH_RC[@]}" \
    "${REMOVE_IGNORE[@]}"

echo "==> Sinh báo cáo HTML tại $HTML_DIR"
genhtml "$FINAL_INFO" \
    --output-directory "$HTML_DIR" \
    "${GENHTML_ARGS[@]}"

echo "==> Tóm tắt độ bao phủ LCOV"
lcov --summary "$FINAL_INFO" "${BRANCH_RC[@]}" "${SUMMARY_IGNORE[@]}"

python3 - "$FINAL_INFO" "$MIN_LINE_COVERAGE" << 'EOF'
import os
import sys

info_path = sys.argv[1]
min_line = float(sys.argv[2])

lf = lh = fnf = fnh = brf = brh = 0
with open(info_path, encoding="utf-8") as fh:
    for line in fh:
        if line.startswith("LF:"):
            lf += int(line[3:].strip())
        elif line.startswith("LH:"):
            lh += int(line[3:].strip())
        elif line.startswith("FNF:"):
            fnf += int(line[4:].strip())
        elif line.startswith("FNH:"):
            fnh += int(line[4:].strip())
        elif line.startswith("BRF:"):
            brf += int(line[4:].strip())
        elif line.startswith("BRH:"):
            brh += int(line[4:].strip())

if lf == 0:
    print("Lỗi: không tìm thấy dòng mã nào được đo trong coverage.info.", file=sys.stderr)
    sys.exit(1)

line_pct = (lh * 100.0) / lf
func_pct = (fnh * 100.0) / fnf if fnf > 0 else 100.0
branch_pct = (brh * 100.0) / brf if brf > 0 else 100.0

print(f"Độ bao phủ dòng (line)    : {line_pct:.2f}% ({lh}/{lf}) — yêu cầu > {min_line:.1f}%")
print(f"Độ bao phủ hàm (function) : {func_pct:.2f}% ({fnh}/{fnf})")
if brf > 0:
    print(f"Độ bao phủ nhánh (branch) : {branch_pct:.2f}% ({brh}/{brf})")
else:
    print("Độ bao phủ nhánh (branch) : không có dữ liệu nhánh")

summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
if summary_file:
    with open(summary_file, "a", encoding="utf-8") as out:
        out.write("## Báo cáo độ bao phủ mã nguồn (LCOV)\n\n")
        out.write("| Chỉ số | Độ bao phủ | Chi tiết |\n")
        out.write("| :--- | :---: | :---: |\n")
        out.write(f"| Line coverage | {line_pct:.2f}% | {lh} / {lf} |\n")
        out.write(f"| Function coverage | {func_pct:.2f}% | {fnh} / {fnf} |\n")
        if brf > 0:
            out.write(f"| Branch coverage | {branch_pct:.2f}% | {brh} / {brf} |\n")
        else:
            out.write("| Branch coverage | N/A | 0 / 0 |\n")
        out.write(f"\nNgưỡng bắt buộc: line coverage > `{min_line:.1f}%`.\n")

if line_pct <= min_line:
    print(
        f"Không đạt ngưỡng độ bao phủ dòng: {line_pct:.2f}% <= {min_line:.1f}%",
        file=sys.stderr,
    )
    sys.exit(1)
EOF
