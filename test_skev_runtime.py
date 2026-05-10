"""
╔══════════════════════════════════════════════════════════════╗
║           SKEV LANGUAGE — RUNTIME TEST SUITE                ║
║                                                              ║
║  Copyright © 2026 AJ. All Rights Reserved.                   ║
║  skev.dev | skev.org                                         ║
╚══════════════════════════════════════════════════════════════╝

WHAT IS THIS FILE?
──────────────────
This is the test suite for skev_runtime.py.
It proves that every part of the Skev language runtime
works correctly — matching what the spec says it should do.

HOW THESE TESTS WORK:
──────────────────────
Each test() call:
  1. Runs a small function
  2. If it passes (no assertion error) → ✅
  3. If it fails (assertion error)     → ❌ with explanation

The tests are organised by spec chapter:
  Chapter 3   — result[T], maybe T, Vector3!, Color!, Transform!
  Chapter 3.5 — Generics: Pair, Range, find_max, find_first, pipe
  Chapter 4   — ARC: retain, release, weak references
  Chapter 6   — result[T], succeed/fail/propagate, panic, assert
  Chapter 7   — skev.math: clamp, lerp, smoothstep, map
  + Real-world logic from Chapters 9, 10
  + Game algorithms: damage, camera follow, attack range

WHY THESE SPECIFIC TESTS?
──────────────────────────
Each test validates a DECISION from the Skev specification.
If a test fails, it means the runtime does not match the spec.

When the real Rust/LLVM compiler is built later:
→ It must pass ALL of these same tests
→ These tests become the COMPLIANCE TEST SUITE
→ 'The Rust compiler is correct when it matches the
   Python transpiler on all test cases'

This is a standard technique in compiler engineering called
'reference implementation testing.'

HOW TO RUN:
───────────
  python3 test_skev_runtime.py
  → Shows ✅ for each passing test
  → Shows ❌ for each failing test
  → Prints final count at the end

Target: 104/104 passed ✅
"""

import sys
from skev_runtime import (
    Result, succeed, fail, _PropagateFailure,
    Maybe, some, nothing,
    skev_panic, skev_assert, SkevPanic,
    Vector3, Color, Transform,
    math, ARCObject, WeakRef, Entity,
    Pair, Range, identity, find_max, find_min, find_first, pipe,
)
from enum import Enum

# ── Test framework ──────────────────────────────────────────
_p = _f = _t = 0

def test(desc, fn):
    global _p, _f, _t
    _t += 1
    try:
        fn()
        _p += 1
        print(f"  ✅ {desc}")
    except AssertionError as e:
        _f += 1
        print(f"  ❌ {desc}  →  {e}")
    except Exception as e:
        _f += 1
        print(f"  ❌ {desc}  →  {type(e).__name__}: {e}")

def section(name):
    print(f"\n{'─'*60}\n  {name}\n{'─'*60}")

def report():
    print(f"\n{'═'*60}")
    status = "ALL PASSED ✅" if _f == 0 else f"{_f} FAILED ❌"
    print(f"  {_p}/{_t} passed — {status}")
    print(f"{'═'*60}\n")
    return _f == 0

# ── Error types ─────────────────────────────────────────────
class ValidationError(Enum):
    negative = "negative"
    too_large = "too_large"
    not_a_number = "not_a_number"

class ParseError(Enum):
    negative_value = "negative_value"
    value_too_large = "value_too_large"
    not_a_number = "not_a_number"

class SandboxError(Enum):
    item_restricted = "item_restricted"

# ════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════
# CHAPTER 6 TESTS — result[T]
# ══════════════════════════════════════════════════════════════
# Tests the core error handling type.
# result[T] is either succeed(value) or fail(error).
# These tests verify every way to create and handle results.
# Spec reference: Chapter 6
section("Chapter 6 — result[T]")

def t_succeed():
    r = succeed(42)
    assert r.is_success and r.value == 42

def t_fail():
    r = fail(ValidationError.negative)
    assert r.is_failure and r.error == ValidationError.negative

def t_succeed_none():
    assert succeed(None).is_success

def t_or_else_success():
    assert succeed(42).or_else(0) == 42

def t_or_else_fail():
    assert fail(ValidationError.negative).or_else(0) == 0

def t_or_else_callable():
    assert fail(ValidationError.negative).or_else(lambda: 99) == 99

def t_match_succeed():
    r = succeed(10).match(on_succeed=lambda v: v*2, on_fail=lambda e: -1)
    assert r == 20

def t_match_fail():
    r = fail(ValidationError.negative).match(on_succeed=lambda v: v*2, on_fail=lambda e: -1)
    assert r == -1

def t_propagate_success():
    assert succeed(42).propagate() == 42

def t_propagate_fail():
    try:
        fail(ValidationError.negative).propagate()
        assert False, "should raise"
    except _PropagateFailure as e:
        assert e.error == ValidationError.negative

def validate_health(v):
    if v < 0: return fail(ValidationError.negative)
    if v > 9999: return fail(ValidationError.too_large)
    return succeed(v)

def t_vh_valid():
    r = validate_health(100)
    assert r.is_success and r.value == 100

def t_vh_neg():
    r = validate_health(-5)
    assert r.is_failure and r.error == ValidationError.negative

def t_vh_large():
    r = validate_health(10000)
    assert r.is_failure and r.error == ValidationError.too_large

def t_vh_zero():  assert validate_health(0).is_success
def t_vh_max():   assert validate_health(9999).is_success

test("succeed wraps value",               t_succeed)
test("fail wraps error",                  t_fail)
test("succeed(None) for result[nothing]", t_succeed_none)
test("or_else: returns value on success", t_or_else_success)
test("or_else: returns fallback on fail", t_or_else_fail)
test("or_else: callable fallback",        t_or_else_callable)
test("match: routes succeed",             t_match_succeed)
test("match: routes fail",                t_match_fail)
test("propagate: unwraps success",        t_propagate_success)
test("propagate: raises on fail",         t_propagate_fail)
test("validate_health: 100 succeeds",     t_vh_valid)
test("validate_health: -5 fails",         t_vh_neg)
test("validate_health: 10000 fails",      t_vh_large)
test("validate_health: 0 is valid",       t_vh_zero)
test("validate_health: 9999 is valid",    t_vh_max)

# ════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════
# CHAPTER 3 TESTS — maybe T
# ══════════════════════════════════════════════════════════════
# Tests the nullable-safety type.
# maybe T is either some(value) or nothing().
# Tests verify: creation, existence check, unwrapping, fallbacks.
# Spec reference: Chapter 3
section("Chapter 3 — maybe T")

def t_some():
    m = some(42)
    assert m.exists and m.value == 42

def t_nothing():
    assert not nothing().exists

def t_bool_some():    assert bool(some(1)) == True
def t_bool_nothing(): assert bool(nothing()) == False

def t_maybe_or_val(): assert some(42).or_else(0) == 42
def t_maybe_or_fb():  assert nothing().or_else(0) == 0
def t_maybe_or_fn():  assert nothing().or_else(lambda: 99) == 99

def t_some_none_panics():
    try:
        some(None)
        assert False
    except SkevPanic:
        pass

test("some wraps value",                t_some)
test("nothing is empty",               t_nothing)
test("some is truthy",                 t_bool_some)
test("nothing is falsy",               t_bool_nothing)
test("or_else returns value",          t_maybe_or_val)
test("or_else returns fallback",       t_maybe_or_fb)
test("or_else callable fallback",      t_maybe_or_fn)
test("some(None) causes panic",        t_some_none_panics)

# ════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════
# CHAPTER 6 TESTS — panic and assert
# ══════════════════════════════════════════════════════════════
# Tests unrecoverable error handling.
# These should NEVER happen in correct code — they are bugs.
# Spec reference: Chapter 6, Section 6.7
section("Chapter 6 — panic and assert")

def t_assert_passes(): skev_assert(True, "ok")

def t_assert_fails():
    try:
        skev_assert(False, "boom")
        assert False
    except SkevPanic as e:
        assert "boom" in str(e)

def t_panic():
    try:
        skev_panic("test")
        assert False
    except SkevPanic as e:
        assert "test" in str(e)

test("assert(True) passes",   t_assert_passes)
test("assert(False) panics",  t_assert_fails)
test("panic raises SkevPanic",t_panic)

# ════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════
# CHAPTER 3 TESTS — Game-Native Types
# ══════════════════════════════════════════════════════════════
# Tests the built-in game types (! suffix).
# Verifies: arithmetic, length, normalisation, lerp, etc.
# Spec reference: Chapter 3, Section 3.3
section("Chapter 3 — Vector3!, Color!, Transform!")

def t_vec3_add():
    assert Vector3(1,2,3) + Vector3(4,5,6) == Vector3(5,7,9)

def t_vec3_sub():
    assert Vector3(5,7,9) - Vector3(1,2,3) == Vector3(4,5,6)

def t_vec3_mul():
    assert Vector3(1,2,3) * 2.0 == Vector3(2,4,6)

def t_vec3_len():
    assert abs(Vector3(3,4,0).length() - 5.0) < 1e-6

def t_vec3_norm():
    assert Vector3(3,0,0).normalised() == Vector3(1,0,0)

def t_vec3_dot():
    assert abs(Vector3(1,0,0).dot(Vector3(0,1,0))) < 1e-6

def t_vec3_cross():
    assert Vector3(1,0,0).cross(Vector3(0,1,0)) == Vector3(0,0,1)

def t_vec3_dist():
    assert abs(Vector3(0,0,0).distance_to(Vector3(3,4,0)) - 5.0) < 1e-6

def t_vec3_lerp():
    assert Vector3(0,0,0).lerp(Vector3(10,10,10), 0.5) == Vector3(5,5,5)

def t_color_white():
    c = Color.white()
    assert c.r == 1.0 and c.g == 1.0 and c.b == 1.0

def t_color_lerp():
    grey = Color.black().lerp(Color.white(), 0.5)
    assert abs(grey.r - 0.5) < 1e-6

def t_color_hex():
    c = Color.from_hex("#FF0000")
    assert abs(c.r - 1.0) < 1e-6 and abs(c.g) < 1e-6

def t_transform_defaults():
    t = Transform()
    assert t.position == Vector3(0,0,0) and t.scale == Vector3(1,1,1)

test("Vector3 add",          t_vec3_add)
test("Vector3 subtract",     t_vec3_sub)
test("Vector3 multiply",     t_vec3_mul)
test("Vector3 length",       t_vec3_len)
test("Vector3 normalised",   t_vec3_norm)
test("Vector3 dot product",  t_vec3_dot)
test("Vector3 cross product",t_vec3_cross)
test("Vector3 distance",     t_vec3_dist)
test("Vector3 lerp",         t_vec3_lerp)
test("Color white",          t_color_white)
test("Color lerp",           t_color_lerp)
test("Color from hex",       t_color_hex)
test("Transform defaults",   t_transform_defaults)

# ════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════
# CHAPTER 7 TESTS — skev.math library
# ══════════════════════════════════════════════════════════════
# Tests the standard math functions.
# Every function used in game development is tested.
# Spec reference: Chapter 7, Layer 1 (always available)
section("Chapter 7 — skev.math")

def t_clamp_in():    assert math.clamp(5.0, 0.0, 10.0) == 5.0
def t_clamp_low():   assert math.clamp(-5.0, 0.0, 10.0) == 0.0
def t_clamp_high():  assert math.clamp(15.0, 0.0, 10.0) == 10.0
def t_lerp_mid():    assert abs(math.lerp(0.0, 10.0, 0.5) - 5.0) < 1e-6
def t_lerp_0():      assert abs(math.lerp(0.0, 10.0, 0.0)) < 1e-6
def t_lerp_1():      assert abs(math.lerp(0.0, 10.0, 1.0) - 10.0) < 1e-6
def t_smooth_mid():  assert abs(math.smoothstep(0.0, 1.0, 0.5) - 0.5) < 1e-6
def t_smooth_0():    assert abs(math.smoothstep(0.0, 1.0, 0.0)) < 1e-6
def t_smooth_1():    assert abs(math.smoothstep(0.0, 1.0, 1.0) - 1.0) < 1e-6
def t_map():         assert abs(math.map(5.0, 0.0, 10.0, 0.0, 100.0) - 50.0) < 1e-6
def t_sqrt():        assert abs(math.sqrt(4.0) - 2.0) < 1e-6
def t_sqrt_panic():
    try:
        math.sqrt(-1.0)
        assert False
    except SkevPanic:
        pass
def t_abs():         assert math.abs(-5.0) == 5.0
def t_floor():       assert math.floor(3.7) == 3
def t_ceil():        assert math.ceil(3.2) == 4
def t_sign_pos():    assert math.sign(5.0) == 1.0
def t_sign_neg():    assert math.sign(-5.0) == -1.0
def t_sign_zero():   assert math.sign(0.0) == 0.0
def t_max():         assert math.max(3.0, 7.0, 1.0) == 7.0
def t_min():         assert math.min(3.0, 7.0, 1.0) == 1.0
def t_deg_rad():     assert abs(math.deg_to_rad(180.0) - 3.14159) < 1e-4
def t_rad_deg():     assert abs(math.rad_to_deg(3.14159) - 180.0) < 0.01

test("clamp within range",      t_clamp_in)
test("clamp below min",         t_clamp_low)
test("clamp above max",         t_clamp_high)
test("lerp midpoint",           t_lerp_mid)
test("lerp at 0",               t_lerp_0)
test("lerp at 1",               t_lerp_1)
test("smoothstep midpoint",     t_smooth_mid)
test("smoothstep at 0",         t_smooth_0)
test("smoothstep at 1",         t_smooth_1)
test("map midpoint",            t_map)
test("sqrt(4) == 2",            t_sqrt)
test("sqrt(-1) panics",         t_sqrt_panic)
test("abs(-5) == 5",            t_abs)
test("floor(3.7) == 3",         t_floor)
test("ceil(3.2) == 4",          t_ceil)
test("sign positive",           t_sign_pos)
test("sign negative",           t_sign_neg)
test("sign zero",               t_sign_zero)
test("max of three",            t_max)
test("min of three",            t_min)
test("deg_to_rad(180)",         t_deg_rad)
test("rad_to_deg(pi)",          t_rad_deg)

# ════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════
# CHAPTER 3.5 TESTS — Generics
# ══════════════════════════════════════════════════════════════
# Tests generic types and algorithms.
# Verifies: Pair[A,B], Range[T], identity[T], find_max[T],
#           find_first[T], pipe[T,U] pipeline combinator.
# Spec reference: Chapter 3.5
section("Chapter 3.5 — Generics")

def t_id_int():     assert identity(42) == 42
def t_id_str():     assert identity("Dragon") == "Dragon"

def t_pair():
    p = Pair(first="Gold", second=500)
    assert p.first == "Gold" and p.second == 500

def t_range_in():
    assert Range(min_val=0.0, max_val=100.0).contains(50.0)

def t_range_out_low():
    assert not Range(min_val=0.0, max_val=100.0).contains(-1.0)

def t_range_out_high():
    assert not Range(min_val=0.0, max_val=100.0).contains(101.0)

def t_range_boundary():
    r = Range(min_val=0.0, max_val=100.0)
    assert r.contains(0.0) and r.contains(100.0)

def t_find_max_ints():
    r = find_max([3,1,4,1,5,9,2,6])
    assert r.exists and r.value == 9

def t_find_max_strings():
    r = find_max(["banana","apple","cherry"])
    assert r.exists and r.value == "cherry"

def t_find_max_empty():
    assert not find_max([]).exists

def t_find_first_found():
    r = find_first([1,2,3,4,5], lambda x: x > 3)
    assert r.exists and r.value == 4

def t_find_first_none():
    assert not find_first([1,2,3], lambda x: x > 100).exists

def t_pipe_success():
    r = pipe(succeed(10), lambda v: succeed(v * 2))
    assert r.is_success and r.value == 20

def t_pipe_fail():
    r = pipe(fail(ValidationError.negative), lambda v: succeed(v * 2))
    assert r.is_failure and r.error == ValidationError.negative

def t_pipe_chain():
    r = pipe(pipe(pipe(succeed(1),
        lambda v: succeed(v+1)),
        lambda v: succeed(v*10)),
        lambda v: succeed(v+5))
    assert r.is_success and r.value == 25

test("identity[int]",           t_id_int)
test("identity[str]",           t_id_str)
test("Pair stores values",      t_pair)
test("Range: contains",         t_range_in)
test("Range: below min",        t_range_out_low)
test("Range: above max",        t_range_out_high)
test("Range: boundaries",       t_range_boundary)
test("find_max ints",           t_find_max_ints)
test("find_max strings",        t_find_max_strings)
test("find_max empty list",     t_find_max_empty)
test("find_first: found",       t_find_first_found)
test("find_first: not found",   t_find_first_none)
test("pipe: success",           t_pipe_success)
test("pipe: propagates fail",   t_pipe_fail)
test("pipe: 3-stage chain",     t_pipe_chain)

# ════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════
# CHAPTER 4 TESTS — ARC Memory Management
# ══════════════════════════════════════════════════════════════
# Tests automatic reference counting simulation.
# Verifies: retain/release, destruction at count 0, weak refs.
# NOTE: Python GC handles actual memory — we test ARC semantics.
# Spec reference: Chapter 4
section("Chapter 4 — ARC simulation")

def t_arc_starts():
    e = Entity(); assert e.arc_count == 1

def t_arc_retain():
    e = Entity(); e._arc_retain()
    assert e.arc_count == 2; e._arc_release()

def t_arc_destroy():
    e = Entity(); e._arc_release()
    assert e._is_destroyed

def t_weak_alive():
    e = Entity(); w = WeakRef(e)
    assert w.exists

def t_weak_dead():
    e = Entity(); w = WeakRef(e)
    e._arc_release(); assert not w.exists

def t_weak_value_alive():
    e = Entity(); w = WeakRef(e)
    assert w.value.exists

def t_weak_value_dead():
    e = Entity(); w = WeakRef(e)
    e._arc_release(); assert not w.value.exists

test("ARC starts at 1",              t_arc_starts)
test("ARC retain increments",        t_arc_retain)
test("ARC release to 0 destroys",    t_arc_destroy)
test("weak ref exists when alive",   t_weak_alive)
test("weak ref clears when dead",    t_weak_dead)
test("weak ref value: alive = some", t_weak_value_alive)
test("weak ref value: dead = nothing",t_weak_value_dead)

# ════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════
# REAL-WORLD LOGIC TESTS — Examples directly from the spec
# ══════════════════════════════════════════════════════════════
# These tests validate actual examples used in spec chapters:
#   parse_health   → Chapter 6 (validate and parse user input)
#   migrate_v1     → Chapter 9 (save file upgrade with defaults)
#   give_item      → Chapter 10 (sandbox capability checking)
#   EventBus       → Chapter 3.5 (generic event routing)
# If these fail, the spec example itself is wrong.
section("Real-World Logic — spec examples")

# parse_health (Chapter 6)
def parse_health(raw):
    try: value = int(raw)
    except ValueError: return fail(ParseError.not_a_number)
    if value < 0:    return fail(ParseError.negative_value)
    if value > 9999: return fail(ParseError.value_too_large)
    return succeed(value)

def t_ph_valid():
    r = parse_health("100")
    assert r.is_success and r.value == 100

def t_ph_neg():
    r = parse_health("-5")
    assert r.is_failure and r.error == ParseError.negative_value

def t_ph_large():
    r = parse_health("10000")
    assert r.is_failure and r.error == ParseError.value_too_large

def t_ph_nan():
    r = parse_health("abc")
    assert r.is_failure and r.error == ParseError.not_a_number

test("parse_health: valid",      t_ph_valid)
test("parse_health: negative",   t_ph_neg)
test("parse_health: too large",  t_ph_large)
test("parse_health: not number", t_ph_nan)

# Save file migration (Chapter 9)
class PlayerV1:
    def __init__(self, name, level, pos):
        self.name, self.level, self.pos = name, level, pos

class PlayerV3:
    def __init__(self, name, level, pos, health=100, abilities=None):
        self.name = name; self.level = level; self.pos = pos
        self.health = health; self.abilities = abilities or []

def migrate_v1(old):
    return PlayerV3(old.name, old.level, old.pos, health=100, abilities=[])

def t_mig_name():
    assert migrate_v1(PlayerV1("AJ", 42, Vector3(0,0,0))).name == "AJ"

def t_mig_level():
    assert migrate_v1(PlayerV1("AJ", 42, Vector3(0,0,0))).level == 42

def t_mig_health():
    assert migrate_v1(PlayerV1("AJ", 1, Vector3(0,0,0))).health == 100

def t_mig_abilities():
    assert migrate_v1(PlayerV1("AJ", 1, Vector3(0,0,0))).abilities == []

test("migration: name preserved",    t_mig_name)
test("migration: level preserved",   t_mig_level)
test("migration: default health 100",t_mig_health)
test("migration: empty abilities",   t_mig_abilities)

# Sandbox (Chapter 10)
def give_item(item_id):
    if item_id >= 1000: return fail(SandboxError.item_restricted)
    return succeed(f"item_{item_id}")

def t_sandbox_ok():   assert give_item(42).is_success
def t_sandbox_boss(): assert give_item(1000).is_failure
def t_sandbox_999():  assert give_item(999).is_success
def t_sandbox_1000(): assert give_item(1000).is_failure

test("sandbox: item 42 allowed",    t_sandbox_ok)
test("sandbox: item 1000 blocked",  t_sandbox_boss)
test("sandbox: item 999 allowed",   t_sandbox_999)
test("sandbox: boundary 999/1000",  t_sandbox_1000)

# ════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════
# GAME ALGORITHM TESTS — Real game logic
# ══════════════════════════════════════════════════════════════
# These test the kind of logic that appears in real games.
# apply_damage:   health clamping (uses math.clamp)
# smooth_cam:     camera follow (uses Vector3.lerp + math.clamp)
# in_range:       attack range check (uses Vector3.distance_to)
# All validate that the underlying math is correct.
section("Game Algorithms — damage, camera, attack range")

def apply_damage(health, damage, max_hp):
    return math.clamp(health - damage, 0, max_hp)

def t_dmg_normal(): assert apply_damage(100, 30, 100) == 70
def t_dmg_lethal(): assert apply_damage(100, 150, 100) == 0
def t_dmg_zero():   assert apply_damage(100, 0, 100) == 100
def t_dmg_exact():  assert apply_damage(50, 50, 100) == 0

def smooth_cam(cam, target, speed, delta):
    t = math.clamp(speed * delta, 0.0, 1.0)
    return cam.lerp(target, t)

def t_cam_moves():
    new = smooth_cam(Vector3(0,0,0), Vector3(10,0,0), 5.0, 0.016)
    assert 0.0 < new.x < 10.0

def t_cam_fast():
    new = smooth_cam(Vector3(0,0,0), Vector3(10,0,0), 100.0, 1.0)
    assert new == Vector3(10,0,0)

def in_range(a, b, r):
    return a.distance_to(b) <= r

def t_in_range():   assert in_range(Vector3(0,0,0), Vector3(3,4,0), 6.0)
def t_out_range():  assert not in_range(Vector3(0,0,0), Vector3(3,4,0), 4.0)
def t_exact_range():assert in_range(Vector3(0,0,0), Vector3(3,4,0), 5.0)

test("apply_damage: normal hit",      t_dmg_normal)
test("apply_damage: lethal → 0",      t_dmg_lethal)
test("apply_damage: zero damage",     t_dmg_zero)
test("apply_damage: exact lethal",    t_dmg_exact)
test("camera: moves toward target",   t_cam_moves)
test("camera: reaches at high speed", t_cam_fast)
test("attack range: in range",        t_in_range)
test("attack range: out of range",    t_out_range)
test("attack range: exact boundary",  t_exact_range)

# ════════════════════════════════════════════════════════════
print()
success = report()
sys.exit(0 if success else 1)
