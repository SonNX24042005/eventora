#!/usr/bin/env python3
"""Kiểm chứng docs/DATABASE_SCHEMA.md bằng cách chạy nguyên văn DDL và truy vấn mẫu trong tài liệu.

Cách chạy (từ gốc repo):
    python3 tests/schema/check_schema.py [đường_dẫn_tài_liệu]

Mặc định đọc docs/DATABASE_SCHEMA.md. Script tách các khối ```sql theo dấu hiệu đầu khối:
    -- schema: ...           khối DDL ở mục 8 (đúng một khối)
    PRAGMA foreign_keys ...  khối PRAGMA theo từng kết nối ở mục 10 (đúng một khối)
    -- query: <tên>          từng truy vấn mẫu ở mục 11
Đổi các dấu hiệu này trong tài liệu thì phải sửa script theo.

Yêu cầu: Python >= 3.11 (thuộc tính sqlite_errorname) và SQLite >= 3.37.0 (bảng STRICT).
Mã thoát: 0 khi mọi ca đạt, 1 khi có ca hỏng, 2 khi môi trường hoặc tài liệu không hợp lệ.
"""
import os
import re
import sqlite3
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "docs", "DATABASE_SCHEMA.md")
EXPECTED_QUERIES = 15


def die(msg):
    """Lỗi môi trường hoặc tài liệu (không phải ca kiểm tra hỏng): thoát với mã 2."""
    print("error:", msg, file=sys.stderr)
    sys.exit(2)


if sys.version_info < (3, 11):
    die(f"cần Python >= 3.11, đang dùng {sys.version.split()[0]}")
if sqlite3.sqlite_version_info < (3, 37, 0):
    die(f"cần SQLite >= 3.37.0, đang dùng {sqlite3.sqlite_version}")

try:
    with open(DOC, encoding="utf-8") as fh:
        text = fh.read()
except OSError as e:
    die(f"không đọc được tài liệu: {e}")
blocks = re.findall(r"```sql\n(.*?)```", text, re.S)
ddl = [b for b in blocks if b.startswith("-- schema:")]
pragma = [b for b in blocks if b.startswith("PRAGMA foreign_keys")]
queries = {}
for b in blocks:
    m = re.match(r"-- query: (\w+)\n", b)
    if m:
        queries[m.group(1)] = b[m.end():]
if len(ddl) != 1 or len(pragma) != 1:
    die(f"cần đúng 1 khối DDL và 1 khối PRAGMA, tìm thấy {len(ddl)} và {len(pragma)}")
DDL, PRAGMA = ddl[0], pragma[0]

passed = 0
failed = []


def check(name, cond, detail=""):
    global passed
    if cond:
        passed += 1
    else:
        failed.append(f"{name}: {detail}")


def expect_error(name, conn, sql, params=(), errorname=None):
    """Câu lệnh phải bị từ chối, và nếu có errorname thì phải đúng mã lỗi mở rộng đó."""
    try:
        conn.execute(sql, params)
    except sqlite3.Error as e:
        got = getattr(e, "sqlite_errorname", None)
        check(name, errorname is None or got == errorname, f"got {got} ({e})")
        return
    check(name, False, "no error raised")


def connect(path=":memory:", timeout=5.0):
    c = sqlite3.connect(path, isolation_level=None, timeout=timeout)
    c.executescript(PRAGMA)
    return c


NOW = 1_800_000_000
H32, S16 = b"\x01" * 32, b"\x02" * 16

db = connect()
db.executescript(DDL)
check("user_version", db.execute("PRAGMA user_version").fetchone()[0] == 1)
check("foreign_keys on", db.execute("PRAGMA foreign_keys").fetchone()[0] == 1)
strict = {r[1]: r[5] for r in db.execute("PRAGMA table_list") if r[0] == "main"}
for t in ("users", "friendships", "events", "event_participants"):
    check(f"{t} strict", strict.get(t) == 1, strict)
check("no organizer index", db.execute(
    "SELECT count(*) FROM sqlite_schema WHERE name = 'ux_ep_one_organizer'").fetchone()[0] == 0)

U = "INSERT INTO users (username, password_hash, salt, pbkdf2_iterations, full_name, email, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)"


def user(name, full="Người dùng", email=None, h=H32, s=S16, created=NOW):
    return db.execute(U, (name, h, s, 600000, full, email, created, created)).lastrowid


# ---- users ----
an = user("an_nguyen", "Nguyễn An", "an@example.com")
binh, chi, dung, em, giang = (user(n) for n in ("binh", "chi", "dung", "em_le", "giang"))
expect_error("username nocase unique", db, U, ("AN_NGUYEN", H32, S16, 1, "Ab", None, NOW, NOW), "SQLITE_CONSTRAINT_UNIQUE")
expect_error("username space", db, U, ("an nguyen", H32, S16, 1, "Ab", None, NOW, NOW), "SQLITE_CONSTRAINT_CHECK")
expect_error("username too short", db, U, ("ab", H32, S16, 1, "Ab", None, NOW, NOW), "SQLITE_CONSTRAINT_CHECK")
expect_error("username too long", db, U, ("a" * 33, H32, S16, 1, "Ab", None, NOW, NOW), "SQLITE_CONSTRAINT_CHECK")
expect_error("username unicode", db, U, ("nguyễn", H32, S16, 1, "Ab", None, NOW, NOW), "SQLITE_CONSTRAINT_CHECK")
expect_error("hash 31 bytes", db, U, ("hash31", b"x" * 31, S16, 1, "Ab", None, NOW, NOW), "SQLITE_CONSTRAINT_CHECK")
expect_error("salt 15 bytes", db, U, ("salt15", H32, b"x" * 15, 1, "Ab", None, NOW, NOW), "SQLITE_CONSTRAINT_CHECK")
# Python không ánh xạ được tên SQLITE_CONSTRAINT_DATATYPE nên kiểm tra theo nội dung thông báo lỗi.
try:
    db.execute(U, ("strict1", H32, S16, 1, "Ab", None, "abc", NOW))
    check("strict datatype", False, "no error raised")
except sqlite3.IntegrityError as e:
    check("strict datatype", "cannot store TEXT value in INTEGER column" in str(e), str(e))
expect_error("iterations 0", db, U, ("iter0", H32, S16, 0, "Ab", None, NOW, NOW), "SQLITE_CONSTRAINT_CHECK")
check("full_name 2 vn chars ok", user("vn2", "Ấn") > 0)
expect_error("full_name 1 char", db, U, ("vn1", H32, S16, 1, "Ấ", None, NOW, NOW), "SQLITE_CONSTRAINT_CHECK")
check("full_name 100 vn chars ok", user("vn100", "ệ" * 100) > 0)
expect_error("full_name 101 chars", db, U, ("vn101", H32, S16, 1, "ệ" * 101, None, NOW, NOW), "SQLITE_CONSTRAINT_CHECK")
expect_error("email no @", db, U, ("mail1", H32, S16, 1, "Ab", "abc", NOW, NOW), "SQLITE_CONSTRAINT_CHECK")
expect_error("email @ first", db, U, ("mail2", H32, S16, 1, "Ab", "@a.b", NOW, NOW), "SQLITE_CONSTRAINT_CHECK")
check("email ok", user("mail3", email="a@b.c") > 0)
expect_error("bio 256", db, "UPDATE users SET bio = ? WHERE user_id = ?", ("x" * 256, an), "SQLITE_CONSTRAINT_CHECK")

# ---- friendships ----
F = "INSERT INTO friendships (requester_id, addressee_id, status, message, created_at, updated_at) VALUES (?,?,?,?,?,?)"
expect_error("friend self", db, F, (an, an, "PENDING", "", NOW, NOW), "SQLITE_CONSTRAINT_CHECK")
db.execute(F, (an, binh, "ACCEPTED", "", NOW, NOW))
expect_error("friend duplicate", db, F, (an, binh, "PENDING", "", NOW, NOW), "SQLITE_CONSTRAINT_UNIQUE")
expect_error("friend reverse pair", db, F, (binh, an, "PENDING", "", NOW, NOW), "SQLITE_CONSTRAINT_UNIQUE")
expect_error("friend status REJECTED", db, F, (an, chi, "REJECTED", "", NOW, NOW), "SQLITE_CONSTRAINT_CHECK")
expect_error("friend fk", db, F, (an, 9999, "PENDING", "", NOW, NOW), "SQLITE_CONSTRAINT_FOREIGNKEY")
expect_error("friend message 201", db, F, (an, chi, "PENDING", "x" * 201, NOW, NOW), "SQLITE_CONSTRAINT_CHECK")
db.execute(F, (chi, an, "ACCEPTED", "", NOW, NOW))
db.execute(F, (dung, an, "PENDING", "kết bạn nhé", NOW, NOW))
last = db.execute(F, (an, em, "PENDING", "", NOW + 1, NOW + 1)).lastrowid
db.execute("DELETE FROM friendships WHERE request_id = ?", (last,))
again = db.execute(F, (an, em, "PENDING", "", NOW + 2, NOW + 2)).lastrowid
check("friendships autoincrement no reuse", again > last, (last, again))

# ---- events ----
E = "INSERT INTO events (creator_id, title, description, location, start_time, end_time, visibility, max_participants, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?)"


def event(creator, title, start, dur, vis, maxp=0, desc=""):
    return db.execute(E, (creator, title, desc, "Hà Nội", start, start + dur, vis, maxp, NOW, NOW)).lastrowid


expect_error("event duration 899", db, E, (an, "Abc", "", "Hà Nội", NOW, NOW + 899, "PUBLIC", 0, NOW, NOW), "SQLITE_CONSTRAINT_CHECK")
expect_error("event duration > 30d", db, E, (an, "Abc", "", "Hà Nội", NOW, NOW + 2592001, "PUBLIC", 0, NOW, NOW), "SQLITE_CONSTRAINT_CHECK")
expect_error("event visibility lower", db, E, (an, "Abc", "", "Hà Nội", NOW, NOW + 900, "public", 0, NOW, NOW), "SQLITE_CONSTRAINT_CHECK")
expect_error("event max -1", db, E, (an, "Abc", "", "Hà Nội", NOW, NOW + 900, "PUBLIC", -1, NOW, NOW), "SQLITE_CONSTRAINT_CHECK")
expect_error("event max 10001", db, E, (an, "Abc", "", "Hà Nội", NOW, NOW + 900, "PUBLIC", 10001, NOW, NOW), "SQLITE_CONSTRAINT_CHECK")
expect_error("event title 2", db, E, (an, "Ab", "", "Hà Nội", NOW, NOW + 900, "PUBLIC", 0, NOW, NOW), "SQLITE_CONSTRAINT_CHECK")
expect_error("event creator fk", db, E, (9999, "Abc", "", "Hà Nội", NOW, NOW + 900, "PUBLIC", 0, NOW, NOW), "SQLITE_CONSTRAINT_FOREIGNKEY")

e1 = event(an, "Họp lớp K68", NOW + 3600, 3600, "PUBLIC", 2)
e2 = event(an, "Giảm giá 100% vui", NOW + 7200, 3600, "PRIVATE")
e3 = event(binh, "Đá bóng_giao hữu", NOW - 10000, 5000, "PUBLIC")
expect_error("creator immutable", db, "UPDATE events SET creator_id = ? WHERE event_id = ?", (binh, e1), "SQLITE_CONSTRAINT_TRIGGER")
db.execute("UPDATE events SET title = 'Họp lớp K68 (mới)', updated_at = ? WHERE event_id = ?", (NOW, e1))

# ---- event_participants ----
P = "INSERT INTO event_participants (event_id, user_id, role, status, invited_by, message, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)"
expect_error("organizer must be creator", db, P, (e1, binh, "ORGANIZER", "ACCEPTED", None, "", NOW, NOW), "SQLITE_CONSTRAINT_TRIGGER")
expect_error("organizer must be accepted", db, P, (e1, an, "ORGANIZER", "INVITED", None, "", NOW, NOW), "SQLITE_CONSTRAINT_CHECK")
expect_error("organizer invited_by null", db, P, (e1, an, "ORGANIZER", "ACCEPTED", binh, "", NOW, NOW), "SQLITE_CONSTRAINT_CHECK")
for ev, org in ((e1, an), (e2, an), (e3, binh)):
    db.execute(P, (ev, org, "ORGANIZER", "ACCEPTED", None, "", NOW, NOW))
expect_error("organizer twice", db, P, (e1, an, "ORGANIZER", "ACCEPTED", None, "", NOW, NOW), "SQLITE_CONSTRAINT_PRIMARYKEY")
expect_error("invited needs inviter", db, P, (e1, em, "PARTICIPANT", "INVITED", None, "", NOW, NOW), "SQLITE_CONSTRAINT_CHECK")
expect_error("self invite", db, P, (e1, em, "PARTICIPANT", "INVITED", em, "", NOW, NOW), "SQLITE_CONSTRAINT_CHECK")
expect_error("bad status", db, P, (e1, em, "PARTICIPANT", "UNKNOWN", None, "", NOW, NOW), "SQLITE_CONSTRAINT_CHECK")
expect_error("ep user fk", db, P, (e1, 9999, "PARTICIPANT", "REQUEST_PENDING", None, "", NOW, NOW), "SQLITE_CONSTRAINT_FOREIGNKEY")
expect_error("ep event fk", db, P, (9999, em, "PARTICIPANT", "REQUEST_PENDING", None, "", NOW, NOW), "SQLITE_CONSTRAINT_FOREIGNKEY")
db.execute(P, (e1, binh, "PARTICIPANT", "ACCEPTED", an, "", NOW, NOW))
db.execute(P, (e1, chi, "PARTICIPANT", "REQUEST_PENDING", None, "cho mình tham gia", NOW + 5, NOW + 5))
db.execute(P, (e1, dung, "PARTICIPANT", "INVITED", binh, "", NOW + 6, NOW + 6))
db.execute(P, (e2, binh, "PARTICIPANT", "INVITED", an, "", NOW, NOW))
db.execute(P, (e2, chi, "PARTICIPANT", "DECLINED", an, "", NOW, NOW))
db.execute(P, (e3, an, "PARTICIPANT", "ACCEPTED", binh, "", NOW, NOW))
expect_error("role immutable", db, "UPDATE event_participants SET role = 'ORGANIZER' WHERE event_id = ? AND user_id = ?", (e1, binh), "SQLITE_CONSTRAINT_TRIGGER")
expect_error("user immutable", db, "UPDATE event_participants SET user_id = ? WHERE event_id = ? AND user_id = ?", (em, e1, binh), "SQLITE_CONSTRAINT_TRIGGER")
expect_error("keep organizer row", db, "DELETE FROM event_participants WHERE event_id = ? AND user_id = ?", (e1, an), "SQLITE_CONSTRAINT_TRIGGER")


def q(name, **params):
    return db.execute(queries[name], params).fetchall()


# ---- truy vấn mẫu ----
check("query count", len(queries) == EXPECTED_QUERIES, sorted(queries))
check("q1 pair either order", q("q1_friend_pair", a=an, b=dung) == q("q1_friend_pair", a=dung, b=an) != [])
check("q1 pending dung->an", q("q1_friend_pair", a=an, b=dung)[0][1:] == (dung, an, "PENDING"))
plan = " ".join(str(r) for r in db.execute("EXPLAIN QUERY PLAN " + queries["q1_friend_pair"], {"a": an, "b": dung}))
check("q1 uses ux_friendships_pair", "ux_friendships_pair" in plan, plan)
check("q2 friends of an", [r[1] for r in q("q2_friends", uid=an, keyword_pattern=None)] == ["binh", "chi"])
check("q2 keyword", [r[1] for r in q("q2_friends", uid=an, keyword_pattern="%chi%")] == ["chi"])
check("q3 incoming", [r[2] for r in q("q3_friend_requests_incoming", uid=an, limit=20, offset=0)] == ["dung"])
check("q3 incoming message", q("q3_friend_requests_incoming", uid=an, limit=20, offset=0)[0][4] == "kết bạn nhé")
check("q3 outgoing", [r[2] for r in q("q3_friend_requests_outgoing", uid=an, limit=20, offset=0)] == ["em_le"])

check("q4 stranger private", q("q4_visible_event", uid=dung, event_id=e2) == [])
check("q4 declined private", q("q4_visible_event", uid=chi, event_id=e2) == [])
r = q("q4_visible_event", uid=binh, event_id=e2)
check("q4 invited by organizer", r and r[0][7] == "INVITED" and r[0][8] == r[0][1], r)
r = q("q4_visible_event", uid=dung, event_id=e1)
check("q4 referral", r and r[0][7] == "INVITED" and r[0][8] != r[0][1], r)
r = q("q4_visible_event", uid=em, event_id=e1)
check("q4 public none", r and r[0][6] is None and r[0][7] is None, r)
check("q4 missing event", q("q4_visible_event", uid=an, event_id=9999) == [])

base = dict(scope="ALL", include_finished=0, now=NOW, from_time=None, to_time=None, keyword_pattern=None, limit=50, offset=0)


def ev(uid, **kw):
    return q("q5_events", uid=uid, **{**base, **kw})


check("q5 dung all", [(x[0], x[10]) for x in ev(dung)] == [(e1, "INVITED")])
check("q5 dung finished", [x[0] for x in ev(dung, include_finished=1)] == [e3, e1])
rows = {x[0]: x for x in ev(an)}
check("q5 an sees e1 e2", sorted(rows) == [e1, e2], sorted(rows))
check("q5 an e1 owner counts", rows[e1][10:12] == ("OWNER", 1) and rows[e1][8] == 1, rows[e1])
check("q5 an e2 owner counts", rows[e2][10:12] == ("OWNER", 0) and rows[e2][8] == 0, rows[e2])
r = {x[0]: x for x in ev(an, include_finished=1)}
check("q5 an e3 accepted", r[e3][10] == "ACCEPTED" and r[e3][11] is None, r[e3])
check("q5 binh mine", [x[0] for x in ev(binh, scope="MINE", include_finished=1)] == [e3])
check("q5 binh invited", [x[0] for x in ev(binh, scope="INVITED")] == [e2])
check("q5 binh joined", [x[0] for x in ev(binh, scope="JOINED", include_finished=1)] == [e1])
check("q5 chi requested", [x[0] for x in ev(chi, scope="REQUESTED")] == [e1])
check("q5 keyword ascii", [x[0] for x in ev(an, keyword_pattern="%k68%")] == [e1])
check("q5 escaped percent", [x[0] for x in ev(an, keyword_pattern="%100\\%%")] == [e2])
check("q5 escaped underscore", [x[0] for x in ev(an, include_finished=1, keyword_pattern="%g\\_g%")] == [e3])
check("q5 underscore literal only", [x[0] for x in ev(an, include_finished=1, keyword_pattern="%p\\_l%")] == [])
check("q5 time range", [x[0] for x in ev(an, from_time=NOW + 7000)] == [e2])
check("q5 paging", [x[0] for x in ev(an, limit=1, offset=1)] == [e2])

c12 = q("q12_login_counters", uid=an, now=NOW)[0]
check("q12 an counters", c12 == (1, 0, 1), c12)
c12 = q("q12_login_counters", uid=binh, now=NOW)[0]
check("q12 binh counters", c12 == (0, 1, 0), c12)

m = q("q13_event_members", event_id=e1, status="ACCEPTED", limit=50, offset=0)
check("q13 accepted", [(x[1], x[3]) for x in m] == [("an_nguyen", "ORGANIZER"), ("binh", "PARTICIPANT")], m)
m = q("q13_event_members", event_id=e1, status="REQUEST_PENDING", limit=50, offset=0)
check("q13 pending message", [(x[1], x[6]) for x in m] == [("chi", "cho mình tham gia")], m)

check("q6 e1 not full", q("q6_capacity", event_id=e1)[0] == (2, 1))
# dung chấp nhận lời giới thiệu của binh -> REQUEST_PENDING, giữ invited_by và created_at
db.execute(queries["q7_upsert_participant"], dict(event_id=e1, user_id=dung, new_status="REQUEST_PENDING", invited_by=binh, message="", now=NOW + 100))
row = db.execute("SELECT status, invited_by, created_at, updated_at FROM event_participants WHERE event_id = ? AND user_id = ?", (e1, dung)).fetchone()
check("q7 referral -> pending", row == ("REQUEST_PENDING", binh, NOW + 6, NOW + 100), row)
# người tổ chức duyệt chi -> ACCEPTED, sự kiện e1 đầy chỗ
db.execute(queries["q7_upsert_participant"], dict(event_id=e1, user_id=chi, new_status="ACCEPTED", invited_by=None, message="cho mình tham gia", now=NOW + 101))
check("q6 e1 full", q("q6_capacity", event_id=e1)[0] == (2, 2))
# upsert tạo bản ghi mới khi chưa có
db.execute(queries["q7_upsert_participant"], dict(event_id=e1, user_id=em, new_status="INVITED", invited_by=binh, message="", now=NOW + 102))
db.execute(queries["q7_upsert_participant"], dict(event_id=e1, user_id=giang, new_status="INVITED", invited_by=an, message="", now=NOW + 103))
check("q7 insert", db.execute("SELECT count(*) FROM event_participants WHERE event_id = ?", (e1,)).fetchone()[0] == 6)

# hủy kết bạn an - binh: chỉ thu hồi lời mời giữa hai người; em do binh mời ở e1 phải còn nguyên
rev = sorted(q("q8_revoke_invitations_between", a=an, b=binh))
check("q8 revoke only between an and binh", rev == [(e2, binh)], rev)
check("q8 em still invited", db.execute("SELECT status FROM event_participants WHERE event_id = ? AND user_id = ?", (e1, em)).fetchone() == ("INVITED",))

cl = sorted(q("q9_cleanup_on_private", event_id=e1))
check("q9 cleanup", cl == sorted([(dung, "REQUEST_PENDING"), (em, "INVITED")]), cl)
check("q9 keeps organizer invite", db.execute("SELECT status FROM event_participants WHERE event_id = ? AND user_id = ?", (e1, giang)).fetchone() == ("INVITED",))

rc = sorted(x[0] for x in q("q10a_cancel_recipients", event_id=e1))
check("q10a recipients", rc == sorted([binh, chi, giang]), rc)
db.execute(queries["q10b_delete_event"], {"event_id": e1})
check("q10b cascade", db.execute("SELECT count(*) FROM event_participants WHERE event_id = ?", (e1,)).fetchone()[0] == 0)
e4 = event(an, "Sự kiện mới", NOW + 3600, 3600, "PUBLIC")
check("events autoincrement no reuse", e4 > e3, (e3, e4))

lp = dict(uid=dung, threshold=3, now=NOW, lock_duration=900)
r1 = q("q11_login_failed", **lp)
r2 = q("q11_login_failed", **lp)
r3 = q("q11_login_failed", **lp)
check("q11 lock sequence", (r1, r2, r3) == ([(1, 0)], [(2, 0)], [(0, NOW + 900)]), (r1, r2, r3))
db.close()

# ---- WAL và SQLITE_BUSY: cần tệp thật vì cơ sở dữ liệu trong RAM không có WAL ----
with tempfile.TemporaryDirectory(prefix="eventora-schema-") as tmpdir:
    path = os.path.join(tmpdir, "wal.db")
    c1 = connect(path)
    check("wal mode", c1.execute("PRAGMA journal_mode = WAL").fetchone()[0] == "wal")
    c1.executescript(DDL)
    c1.execute(U, ("walone", H32, S16, 1, "Ab", None, NOW, NOW))
    c2 = connect(path, timeout=0)
    c1.execute("BEGIN IMMEDIATE")
    try:
        c2.execute("BEGIN IMMEDIATE")
        check("second writer busy", False, "no error")
    except sqlite3.OperationalError as e:
        check("second writer busy", e.sqlite_errorname == "SQLITE_BUSY", e.sqlite_errorname)
    c1.execute("COMMIT")
    # giao dịch DEFERRED đọc trước rồi mới ghi sẽ hỏng ngay (không chờ busy_timeout)
    # nếu kết nối khác đã ghi xen vào giữa
    c3 = connect(path, timeout=5)
    c3.execute("BEGIN")
    c3.execute("SELECT count(*) FROM users").fetchone()
    c2.execute(U, ("waltwo", H32, S16, 1, "Ab", None, NOW, NOW))
    t0 = time.monotonic()
    try:
        c3.execute("UPDATE users SET bio = 'x' WHERE username = 'walone'")
        check("deferred upgrade fails", False, "no error")
    except sqlite3.OperationalError as e:
        elapsed = time.monotonic() - t0
        check("deferred upgrade fails", e.sqlite_errorname.startswith("SQLITE_BUSY"), e.sqlite_errorname)
        check("deferred upgrade fails fast", elapsed < 1.0, elapsed)
        print("deferred upgrade error:", e.sqlite_errorname, f"after {elapsed * 1000:.1f} ms")
    c3.execute("ROLLBACK")
    for c in (c1, c2, c3):
        c.close()

print("python", sys.version.split()[0], "| sqlite", sqlite3.sqlite_version, "| queries found:", len(queries))
print(f"passed {passed}, failed {len(failed)}")
for f in failed:
    print("FAIL", f)
sys.exit(1 if failed else 0)
