"""
Skev Language - End-to-End Test Suite (Step 5)
Copyright (c) 2026 AJ. All Rights Reserved. skev.dev | skev.org

Complete Skev programs running through the full pipeline:
  .skev source -> lexer -> parser -> emitter -> exec() -> verified results

8 real-world programs. Every test uses the FULL pipeline.

Run with: python3 test_skev_e2e.py
"""

import sys
from skev_emitter import emit
from skev_runtime import succeed, fail, some, nothing, math, Vector3, SkevPanic

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
        print(f"  ❌ {desc}")
        print(f"     {e}")
    except Exception as e:
        _f += 1
        print(f"  ❌ {desc}")
        print(f"     {type(e).__name__}: {e}")

def section(name):
    print(f"\n{'─'*60}\n  {name}\n{'─'*60}")

def report():
    print(f"\n{'═'*60}")
    status = "ALL PASSED ✅" if _f == 0 else f"{_f} FAILED ❌"
    print(f"  {_p}/{_t} passed — {status}")
    print(f"{'═'*60}\n")
    return _f == 0

def run(source):
    """Run a complete Skev program through the full pipeline."""
    code, errors = emit(source)
    assert len(errors) == 0, f"Pipeline errors:\n" + "\n".join(str(e) for e in errors)
    ns = {}
    exec(code, ns)
    return ns


# ════════════════════════════════════════════════════════════
# PROGRAM 1 — RPG COMBAT ENGINE
# ════════════════════════════════════════════════════════════
# Tests: entity, data, kind, result[T], succeed/fail,
#        if, math.clamp, multiple methods
# ════════════════════════════════════════════════════════════

section("Program 1 — RPG Combat Engine")

RPG_COMBAT = """kind DamageType >>
    physical
    fire
    ice
    poison
<< DamageType

kind CombatResult >>
    killed
    survived
    invalid_damage
<< CombatResult

data DamageEvent >>
    amount    :: float
    type_name :: DamageType
    is_crit   :: bool
<< DamageEvent

entity Fighter >>
    health     :: int   = 100
    max_health :: int   = 100
    armour     :: int   = 10
    alive      :: bool  = true
    kills      :: int   = 0

    take_damage(event: DamageEvent) -> result[CombatResult]
        if event.amount <= 0 >>
            fail CombatResult.invalid_damage
        << event.amount <= 0

        effective :: float = event.amount - armour
        if effective < 1 >>
            effective = 1.0
        << effective < 1

        if event.is_crit >>
            effective = effective * 2.0
        << event.is_crit

        health = math.clamp(health - effective, 0, max_health)

        if health <= 0 >>
            alive = false
            succeed CombatResult.killed
        << health <= 0

        succeed CombatResult.survived
    << take_damage

    heal(amount: int) -> nothing
        if alive >>
            health = math.clamp(health + amount, 0, max_health)
        << alive
    << heal

    register_kill() -> nothing
        kills += 1
    << register_kill

    health_percent() -> float
        result math.clamp(health / max_health, 0.0, 1.0)
    << health_percent

<< Fighter"""

def _ns1():
    return run(RPG_COMBAT)

def t_combat_normal():
    ns = _ns1()
    f = ns["Fighter"]()
    e = ns["DamageEvent"](amount=30.0, type_name=ns["DamageType"].physical, is_crit=False)
    r = f.take_damage(e)
    assert r.is_success
    assert r.value == ns["CombatResult"].survived
    assert f.health == 80   # 30 - 10 armour = 20 damage

def t_combat_crit():
    ns = _ns1()
    f = ns["Fighter"]()
    e = ns["DamageEvent"](amount=30.0, type_name=ns["DamageType"].fire, is_crit=True)
    f.take_damage(e)
    assert f.health == 60   # (30-10)*2 = 40 damage

def t_combat_lethal():
    ns = _ns1()
    f = ns["Fighter"]()
    e = ns["DamageEvent"](amount=200.0, type_name=ns["DamageType"].physical, is_crit=False)
    r = f.take_damage(e)
    assert r.value == ns["CombatResult"].killed
    assert f.health == 0
    assert f.alive == False

def t_combat_invalid():
    ns = _ns1()
    f = ns["Fighter"]()
    e = ns["DamageEvent"](amount=0.0, type_name=ns["DamageType"].physical, is_crit=False)
    r = f.take_damage(e)
    assert r.is_failure
    assert r.error == ns["CombatResult"].invalid_damage

def t_combat_armour_min():
    ns = _ns1()
    f = ns["Fighter"]()
    e = ns["DamageEvent"](amount=5.0, type_name=ns["DamageType"].physical, is_crit=False)
    f.take_damage(e)
    assert f.health == 99   # minimum 1 damage

def t_combat_heal():
    ns = _ns1()
    f = ns["Fighter"]()
    f.health = 50
    f.heal(30)
    assert f.health == 80

def t_combat_heal_capped():
    ns = _ns1()
    f = ns["Fighter"]()
    f.health = 90
    f.heal(50)
    assert f.health == 100

def t_combat_dead_no_heal():
    ns = _ns1()
    f = ns["Fighter"]()
    f.health = 0
    f.alive = False
    f.heal(50)
    assert f.health == 0

def t_combat_percent():
    ns = _ns1()
    f = ns["Fighter"]()
    f.health = 25
    assert abs(f.health_percent() - 0.25) < 1e-9

def t_combat_kills():
    ns = _ns1()
    f = ns["Fighter"]()
    f.register_kill()
    f.register_kill()
    assert f.kills == 2

test("combat: normal hit (armour reduced)",     t_combat_normal)
test("combat: crit hit doubles damage",          t_combat_crit)
test("combat: lethal damage kills",              t_combat_lethal)
test("combat: invalid damage returns fail",      t_combat_invalid)
test("combat: minimum 1 damage through armour",  t_combat_armour_min)
test("combat: heal restores health",             t_combat_heal)
test("combat: heal capped at max_health",        t_combat_heal_capped)
test("combat: dead fighters cannot heal",        t_combat_dead_no_heal)
test("combat: health_percent correct",           t_combat_percent)
test("combat: kill counter increments",          t_combat_kills)


# ════════════════════════════════════════════════════════════
# PROGRAM 2 — INVENTORY SYSTEM
# ════════════════════════════════════════════════════════════
# Tests: entity, data, kind, list ops, loop, if, succeed/fail,
#        method calls with self. prefix (critical test)
# ════════════════════════════════════════════════════════════

section("Program 2 — Inventory System")

INVENTORY = """kind ItemType >>
    weapon
    armour
    potion
    key
<< ItemType

data Item >>
    id     :: int
    name   :: string
    weight :: float
    type_  :: ItemType
<< Item

entity Inventory >>
    items      :: list[Item]
    max_weight :: float = 50.0
    gold       :: int   = 0

    current_weight() -> float
        total :: float = 0.0
        loop item in items >>
            total += item.weight
        << item
        result total
    << current_weight

    can_carry(item: Item) -> bool
        result current_weight() + item.weight <= max_weight
    << can_carry

    add_item(item: Item) -> result[int]
        if not can_carry(item) >>
            fail 0
        << not can_carry(item)
        items.append(item)
        succeed items.__len__()
    << add_item

    count_by_type(target_type: ItemType) -> int
        count :: int = 0
        loop item in items >>
            if item.type_ == target_type >>
                count += 1
            << item.type_ == target_type
        << item
        result count
    << count_by_type

    has_key(key_id: int) -> bool
        loop item in items >>
            if item.type_ == ItemType.key and item.id == key_id >>
                result true
            << item.type_ == ItemType.key and item.id == key_id
        << item
        result false
    << has_key

<< Inventory"""

def _ns2():
    return run(INVENTORY)

def _item(ns, id, name, weight, t):
    return ns["Item"](id=id, name=name, weight=weight,
                      type_=getattr(ns["ItemType"], t))

def t_inv_empty():
    ns = _ns2()
    inv = ns["Inventory"]()
    assert inv.items == []
    assert abs(inv.current_weight()) < 1e-9

def t_inv_add():
    ns = _ns2()
    inv = ns["Inventory"]()
    r = inv.add_item(_item(ns, 1, "Sword", 10.0, "weapon"))
    assert r.is_success
    assert len(inv.items) == 1

def t_inv_weight_limit():
    ns = _ns2()
    inv = ns["Inventory"]()
    r = inv.add_item(_item(ns, 1, "Boulder", 60.0, "weapon"))
    assert r.is_failure

def t_inv_count():
    ns = _ns2()
    inv = ns["Inventory"]()
    inv.add_item(_item(ns, 1, "Sword",  5.0, "weapon"))
    inv.add_item(_item(ns, 2, "Shield", 8.0, "armour"))
    inv.add_item(_item(ns, 3, "Axe",    6.0, "weapon"))
    inv.add_item(_item(ns, 4, "Potion", 1.0, "potion"))
    IT = ns["ItemType"]
    assert inv.count_by_type(IT.weapon) == 2
    assert inv.count_by_type(IT.key)    == 0

def t_inv_has_key():
    ns = _ns2()
    inv = ns["Inventory"]()
    inv.add_item(_item(ns, 99, "Gold Key", 0.1, "key"))
    assert inv.has_key(99) == True
    assert inv.has_key(88) == False

def t_inv_weight():
    ns = _ns2()
    inv = ns["Inventory"]()
    inv.add_item(_item(ns, 1, "A", 10.0, "weapon"))
    inv.add_item(_item(ns, 2, "B", 20.0, "weapon"))
    assert abs(inv.current_weight() - 30.0) < 1e-9

def t_inv_method_calls_self():
    # Critical: can_carry() calls current_weight() — both need self. prefix
    ns = _ns2()
    inv = ns["Inventory"]()
    inv.add_item(_item(ns, 1, "Heavy", 40.0, "weapon"))
    # Now 10kg left. Another 10kg item should fit.
    r = inv.add_item(_item(ns, 2, "Light", 10.0, "potion"))
    assert r.is_success
    # Another 10kg should fail (would exceed 50kg limit)
    r2 = inv.add_item(_item(ns, 3, "Another", 10.0, "potion"))
    assert r2.is_failure

test("inventory: starts empty",              t_inv_empty)
test("inventory: add item succeeds",         t_inv_add)
test("inventory: weight limit enforced",     t_inv_weight_limit)
test("inventory: count by type",             t_inv_count)
test("inventory: has_key finds key",         t_inv_has_key)
test("inventory: weight accumulates",        t_inv_weight)
test("inventory: method calls method (self.)", t_inv_method_calls_self)


# ════════════════════════════════════════════════════════════
# PROGRAM 3 — STATE MACHINE
# ════════════════════════════════════════════════════════════
# Tests: kind, entity, if/else for state logic, guards,
#        state transition, counters
# ════════════════════════════════════════════════════════════

section("Program 3 — State Machine")

STATE_MACHINE = """kind GameState >>
    loading
    menu
    playing
    paused
    game_over
<< GameState

entity GameStateMachine >>
    state            :: GameState = GameState.loading
    score            :: int       = 0
    frames_in_state  :: int       = 0

    transition(new_state: GameState) -> result[GameState]
        if state == new_state >>
            succeed state
        << state == new_state

        if state == GameState.game_over >>
            fail GameState.game_over
        << state == GameState.game_over

        state = new_state
        frames_in_state = 0
        succeed state
    << transition

    update(delta: float) -> nothing
        frames_in_state += 1
        if state == GameState.playing >>
            score += 1
        << state == GameState.playing
    << update

    is_playing() -> bool
        result state == GameState.playing
    << is_playing

    is_over() -> bool
        result state == GameState.game_over
    << is_over

<< GameStateMachine"""

def _ns3():
    return run(STATE_MACHINE)

def t_sm_starts_loading():
    ns = _ns3()
    sm = ns["GameStateMachine"]()
    GS = ns["GameState"]
    assert sm.state == GS.loading

def t_sm_transition():
    ns = _ns3()
    sm = ns["GameStateMachine"]()
    GS = ns["GameState"]
    r = sm.transition(GS.menu)
    assert r.is_success and r.value == GS.menu
    assert sm.state == GS.menu

def t_sm_no_exit_game_over():
    ns = _ns3()
    sm = ns["GameStateMachine"]()
    GS = ns["GameState"]
    sm.transition(GS.game_over)
    r = sm.transition(GS.menu)
    assert r.is_failure

def t_sm_same_state():
    ns = _ns3()
    sm = ns["GameStateMachine"]()
    GS = ns["GameState"]
    sm.transition(GS.playing)
    r = sm.transition(GS.playing)
    assert r.is_success

def t_sm_score_while_playing():
    ns = _ns3()
    sm = ns["GameStateMachine"]()
    GS = ns["GameState"]
    sm.transition(GS.playing)
    sm.update(0.016)
    sm.update(0.016)
    sm.update(0.016)
    assert sm.score == 3

def t_sm_no_score_paused():
    ns = _ns3()
    sm = ns["GameStateMachine"]()
    GS = ns["GameState"]
    sm.transition(GS.paused)
    sm.update(0.016)
    sm.update(0.016)
    assert sm.score == 0

def t_sm_is_playing():
    ns = _ns3()
    sm = ns["GameStateMachine"]()
    GS = ns["GameState"]
    assert sm.is_playing() == False
    sm.transition(GS.playing)
    assert sm.is_playing() == True

def t_sm_is_over():
    ns = _ns3()
    sm = ns["GameStateMachine"]()
    GS = ns["GameState"]
    sm.transition(GS.game_over)
    assert sm.is_over() == True

def t_sm_frames_reset():
    ns = _ns3()
    sm = ns["GameStateMachine"]()
    GS = ns["GameState"]
    sm.update(0.016)
    sm.update(0.016)
    assert sm.frames_in_state == 2
    sm.transition(GS.playing)
    assert sm.frames_in_state == 0

test("state machine: starts in loading",          t_sm_starts_loading)
test("state machine: transition changes state",   t_sm_transition)
test("state machine: no exit from game_over",     t_sm_no_exit_game_over)
test("state machine: same state succeeds",        t_sm_same_state)
test("state machine: score increments playing",   t_sm_score_while_playing)
test("state machine: no score when paused",       t_sm_no_score_paused)
test("state machine: is_playing() correct",       t_sm_is_playing)
test("state machine: is_over() correct",          t_sm_is_over)
test("state machine: frames reset on transition", t_sm_frames_reset)


# ════════════════════════════════════════════════════════════
# PROGRAM 4 — LEADERBOARD
# ════════════════════════════════════════════════════════════
# Tests: entity, data, list, loop range, loop iterate,
#        highest/lowest/average, conditional counting
# ════════════════════════════════════════════════════════════

section("Program 4 — Leaderboard")

LEADERBOARD = """data ScoreEntry >>
    player_name :: string
    score       :: int
    level       :: int
<< ScoreEntry

entity Leaderboard >>
    entries :: list[ScoreEntry]

    add_entry(entry: ScoreEntry) -> result[int]
        if entry.score < 0 >>
            fail 0
        << entry.score < 0
        entries.append(entry)
        succeed entries.__len__()
    << add_entry

    count() -> int
        result entries.__len__()
    << count

    highest_score() -> int
        if entries.__len__() == 0 >>
            result 0
        << entries.__len__() == 0
        best :: int = 0
        loop entry in entries >>
            if entry.score > best >>
                best = entry.score
            << entry.score > best
        << entry
        result best
    << highest_score

    lowest_score() -> int
        if entries.__len__() == 0 >>
            result 0
        << entries.__len__() == 0
        worst :: int = 999999
        loop entry in entries >>
            if entry.score < worst >>
                worst = entry.score
            << entry.score < worst
        << entry
        result worst
    << lowest_score

    count_above(threshold: int) -> int
        count :: int = 0
        loop entry in entries >>
            if entry.score > threshold >>
                count += 1
            << entry.score > threshold
        << entry
        result count
    << count_above

    average_score() -> float
        if entries.__len__() == 0 >>
            result 0.0
        << entries.__len__() == 0
        total :: int = 0
        loop entry in entries >>
            total += entry.score
        << entry
        result total / entries.__len__()
    << average_score

<< Leaderboard"""

def _ns4():
    return run(LEADERBOARD)

def _entry(ns, name, score, level=1):
    return ns["ScoreEntry"](player_name=name, score=score, level=level)

def t_lb_empty():
    ns = _ns4()
    lb = ns["Leaderboard"]()
    assert lb.count() == 0

def t_lb_add():
    ns = _ns4()
    lb = ns["Leaderboard"]()
    r = lb.add_entry(_entry(ns, "AJ", 1000))
    assert r.is_success and r.value == 1

def t_lb_invalid():
    ns = _ns4()
    lb = ns["Leaderboard"]()
    r = lb.add_entry(_entry(ns, "Bad", -1))
    assert r.is_failure

def t_lb_highest():
    ns = _ns4()
    lb = ns["Leaderboard"]()
    lb.add_entry(_entry(ns, "A", 100))
    lb.add_entry(_entry(ns, "B", 500))
    lb.add_entry(_entry(ns, "C", 300))
    assert lb.highest_score() == 500

def t_lb_lowest():
    ns = _ns4()
    lb = ns["Leaderboard"]()
    lb.add_entry(_entry(ns, "A", 100))
    lb.add_entry(_entry(ns, "B", 500))
    lb.add_entry(_entry(ns, "C", 300))
    assert lb.lowest_score() == 100

def t_lb_count_above():
    ns = _ns4()
    lb = ns["Leaderboard"]()
    for s in [100, 200, 300, 400]:
        lb.add_entry(_entry(ns, "P", s))
    assert lb.count_above(200) == 2   # 300 and 400

def t_lb_average():
    ns = _ns4()
    lb = ns["Leaderboard"]()
    lb.add_entry(_entry(ns, "A", 100))
    lb.add_entry(_entry(ns, "B", 300))
    assert abs(lb.average_score() - 200.0) < 1e-9

def t_lb_full():
    ns = _ns4()
    lb = ns["Leaderboard"]()
    for i, s in enumerate([100, 250, 800, 420, 60, 999]):
        lb.add_entry(_entry(ns, f"P{i}", s))
    assert lb.count()        == 6
    assert lb.highest_score() == 999
    assert lb.lowest_score()  == 60
    assert lb.count_above(400) == 3   # 800, 420, 999

test("leaderboard: empty state",             t_lb_empty)
test("leaderboard: add entry",               t_lb_add)
test("leaderboard: invalid score rejected",  t_lb_invalid)
test("leaderboard: highest score",           t_lb_highest)
test("leaderboard: lowest score",            t_lb_lowest)
test("leaderboard: count above threshold",   t_lb_count_above)
test("leaderboard: average score",           t_lb_average)
test("leaderboard: full 6-entry system",     t_lb_full)


# ════════════════════════════════════════════════════════════
# PROGRAM 5 — ERROR HANDLING CHAIN
# ════════════════════════════════════════════════════════════
# Tests: result[T] chaining, multi-step validation,
#        succeed/fail/match, error propagation via if-check
# ════════════════════════════════════════════════════════════

section("Program 5 — Error Handling Chain")

ERROR_CHAIN = """kind ParseError >>
    empty_input
    negative_value
    too_large
    not_a_number
<< ParseError

entity DataProcessor >>
    last_error :: string = ""

    validate_not_empty(raw: string) -> result[string]
        if raw == "" >>
            fail ParseError.empty_input
        << raw == ""
        succeed raw
    << validate_not_empty

    parse_int(raw: string) -> result[int]
        if raw == "bad" >>
            fail ParseError.not_a_number
        << raw == "bad"
        if raw == "42" >>
            succeed 42
        << raw == "42"
        if raw == "100" >>
            succeed 100
        << raw == "100"
        if raw == "9999" >>
            succeed 9999
        << raw == "9999"
        succeed 0
    << parse_int

    validate_range(value: int) -> result[int]
        if value < 0 >>
            fail ParseError.negative_value
        << value < 0
        if value > 9999 >>
            fail ParseError.too_large
        << value > 9999
        succeed value
    << validate_range

    process(raw: string) -> result[int]
        step1 :: result[string] = validate_not_empty(raw)
        if step1.is_failure >>
            fail step1.error
        << step1.is_failure

        step2 :: result[int] = parse_int(step1.value)
        if step2.is_failure >>
            fail step2.error
        << step2.is_failure

        step3 :: result[int] = validate_range(step2.value)
        if step3.is_failure >>
            fail step3.error
        << step3.is_failure

        succeed step3.value
    << process

<< DataProcessor"""

def _ns5():
    return run(ERROR_CHAIN)

def t_err_valid():
    ns = _ns5()
    dp = ns["DataProcessor"]()
    r = dp.process("42")
    assert r.is_success and r.value == 42

def t_err_empty():
    ns = _ns5()
    dp = ns["DataProcessor"]()
    PE = ns["ParseError"]
    r = dp.process("")
    assert r.is_failure and r.error == PE.empty_input

def t_err_not_a_number():
    ns = _ns5()
    dp = ns["DataProcessor"]()
    PE = ns["ParseError"]
    r = dp.process("bad")
    assert r.is_failure and r.error == PE.not_a_number

def t_err_too_large():
    ns = _ns5()
    dp = ns["DataProcessor"]()
    PE = ns["ParseError"]
    r = dp.validate_range(10000)
    assert r.is_failure and r.error == PE.too_large

def t_err_all_pass():
    ns = _ns5()
    dp = ns["DataProcessor"]()
    r = dp.process("9999")
    assert r.is_success and r.value == 9999

def t_err_direct_validate():
    ns = _ns5()
    dp = ns["DataProcessor"]()
    PE = ns["ParseError"]
    r = dp.validate_not_empty("")
    assert r.is_failure and r.error == PE.empty_input
    r2 = dp.validate_not_empty("hello")
    assert r2.is_success

def t_err_chained_pipeline():
    ns = _ns5()
    dp = ns["DataProcessor"]()
    PE = ns["ParseError"]
    # All four paths through the pipeline
    assert dp.process("42").is_success
    assert dp.process("").error == PE.empty_input
    assert dp.process("bad").error == PE.not_a_number
    assert dp.validate_range(-1).error == PE.negative_value

test("error chain: valid input → succeed",      t_err_valid)
test("error chain: empty → fail stage 1",       t_err_empty)
test("error chain: non-number → fail stage 2",  t_err_not_a_number)
test("error chain: too large → fail stage 3",   t_err_too_large)
test("error chain: all stages pass",            t_err_all_pass)
test("error chain: direct validate_not_empty",  t_err_direct_validate)
test("error chain: all four paths verified",    t_err_chained_pipeline)


# ════════════════════════════════════════════════════════════
# PROGRAM 6 — PHYSICS AND MATH
# ════════════════════════════════════════════════════════════
# Tests: Vector3! game-native types, math operations,
#        physics simulation, loop with math
# ════════════════════════════════════════════════════════════

section("Program 6 — Physics and Math")

PHYSICS = """entity PhysicsBody >>
    pos_x :: float = 0.0
    pos_y :: float = 0.0
    pos_z :: float = 0.0
    vel_x :: float = 0.0
    vel_y :: float = 0.0
    vel_z :: float = 0.0
    mass  :: float = 1.0
    drag  :: float = 0.1

    update(delta: float) -> nothing
        pos_x = pos_x + vel_x * delta
        pos_y = pos_y + vel_y * delta
        pos_z = pos_z + vel_z * delta
        vel_x = vel_x * (1.0 - drag * delta)
        vel_y = vel_y * (1.0 - drag * delta)
        vel_z = vel_z * (1.0 - drag * delta)
    << update

    apply_force(fx: float, fy: float, fz: float) -> nothing
        vel_x += fx / mass
        vel_y += fy / mass
        vel_z += fz / mass
    << apply_force

    speed() -> float
        result math.sqrt(vel_x * vel_x + vel_y * vel_y + vel_z * vel_z)
    << speed

    distance_to(ox: float, oy: float, oz: float) -> float
        dx :: float = pos_x - ox
        dy :: float = pos_y - oy
        dz :: float = pos_z - oz
        result math.sqrt(dx * dx + dy * dy + dz * dz)
    << distance_to

    halt() -> nothing
        vel_x = 0.0
        vel_y = 0.0
        vel_z = 0.0
    << halt

    kinetic_energy() -> float
        s :: float = speed()
        result 0.5 * mass * s * s
    << kinetic_energy

<< PhysicsBody"""

def _ns6():
    return run(PHYSICS)

def t_phys_origin():
    ns = _ns6()
    body = ns["PhysicsBody"]()
    assert abs(body.pos_x) < 1e-9
    assert abs(body.speed()) < 1e-9

def t_phys_moves():
    ns = _ns6()
    body = ns["PhysicsBody"]()
    body.vel_x = 10.0
    body.drag = 0.0
    body.update(1.0)
    assert abs(body.pos_x - 10.0) < 0.01

def t_phys_force():
    ns = _ns6()
    body = ns["PhysicsBody"]()
    body.apply_force(10.0, 0.0, 0.0)
    assert abs(body.vel_x - 10.0) < 1e-6

def t_phys_speed():
    ns = _ns6()
    body = ns["PhysicsBody"]()
    body.vel_x = 3.0
    body.vel_y = 4.0
    assert abs(body.speed() - 5.0) < 1e-6   # 3-4-5 triangle

def t_phys_distance():
    ns = _ns6()
    body = ns["PhysicsBody"]()
    d = body.distance_to(3.0, 4.0, 0.0)
    assert abs(d - 5.0) < 1e-6

def t_phys_halt():
    ns = _ns6()
    body = ns["PhysicsBody"]()
    body.vel_x = 100.0
    body.vel_y = 50.0
    body.halt()
    assert abs(body.speed()) < 1e-9

def t_phys_drag():
    ns = _ns6()
    body = ns["PhysicsBody"]()
    body.vel_x = 10.0
    body.drag = 0.5
    body.update(1.0)
    assert abs(body.vel_x - 5.0) < 0.01   # 10 * (1 - 0.5) = 5

def t_phys_kinetic():
    ns = _ns6()
    body = ns["PhysicsBody"]()
    body.vel_x = 10.0
    body.drag = 0.0
    ke = body.kinetic_energy()
    assert abs(ke - 50.0) < 1e-6   # 0.5 * 1 * 100 = 50

test("physics: starts at origin",        t_phys_origin)
test("physics: moves with velocity",     t_phys_moves)
test("physics: force changes velocity",  t_phys_force)
test("physics: speed() 3-4-5 triangle",  t_phys_speed)
test("physics: distance_to correct",     t_phys_distance)
test("physics: halt() zeroes velocity",  t_phys_halt)
test("physics: drag slows body",         t_phys_drag)
test("physics: kinetic energy",          t_phys_kinetic)


# ════════════════════════════════════════════════════════════
# PROGRAM 7 — ACHIEVEMENT SYSTEM
# ════════════════════════════════════════════════════════════
# Tests: nested if, loop+if combo, result[T],
#        double-trigger prevention, multiple entity instances
# ════════════════════════════════════════════════════════════

section("Program 7 — Achievement System")

ACHIEVEMENT = """kind AchievementStatus >>
    locked
    unlocked
<< AchievementStatus

data Achievement >>
    id        :: int
    name      :: string
    threshold :: int
    status    :: AchievementStatus
    progress  :: int
<< Achievement

entity AchievementTracker >>
    achievements   :: list[Achievement]
    total_unlocked :: int = 0

    add_achievement(ach: Achievement) -> nothing
        achievements.append(ach)
    << add_achievement

    update_progress(ach_id: int, amount: int) -> result[int]
        loop ach in achievements >>
            if ach.id == ach_id >>
                ach.progress += amount
                if ach.progress >= ach.threshold >>
                    if ach.status == AchievementStatus.locked >>
                        ach.status = AchievementStatus.unlocked
                        total_unlocked += 1
                    << ach.status == AchievementStatus.locked
                << ach.progress >= ach.threshold
                succeed ach.progress
            << ach.id == ach_id
        << ach
        fail 0
    << update_progress

    is_unlocked(ach_id: int) -> bool
        loop ach in achievements >>
            if ach.id == ach_id >>
                result ach.status == AchievementStatus.unlocked
            << ach.id == ach_id
        << ach
        result false
    << is_unlocked

    get_progress(ach_id: int) -> int
        loop ach in achievements >>
            if ach.id == ach_id >>
                result ach.progress
            << ach.id == ach_id
        << ach
        result 0
    << get_progress

<< AchievementTracker"""

def _ns7():
    return run(ACHIEVEMENT)

def _ach(ns, id, name, threshold):
    A  = ns["Achievement"]
    AS = ns["AchievementStatus"]
    return A(id=id, name=name, threshold=threshold,
             status=AS.locked, progress=0)

def t_ach_locked():
    ns = _ns7()
    tracker = ns["AchievementTracker"]()
    tracker.add_achievement(_ach(ns, 1, "First Blood", 1))
    assert tracker.is_unlocked(1) == False

def t_ach_unlocks():
    ns = _ns7()
    tracker = ns["AchievementTracker"]()
    tracker.add_achievement(_ach(ns, 1, "First Blood", 1))
    tracker.update_progress(1, 1)
    assert tracker.is_unlocked(1) == True
    assert tracker.total_unlocked == 1

def t_ach_partial():
    ns = _ns7()
    tracker = ns["AchievementTracker"]()
    tracker.add_achievement(_ach(ns, 1, "Veteran", 10))
    tracker.update_progress(1, 5)
    assert tracker.is_unlocked(1) == False
    assert tracker.get_progress(1) == 5

def t_ach_incremental():
    ns = _ns7()
    tracker = ns["AchievementTracker"]()
    tracker.add_achievement(_ach(ns, 1, "Veteran", 10))
    for _ in range(10):
        tracker.update_progress(1, 1)
    assert tracker.is_unlocked(1) == True

def t_ach_multiple():
    ns = _ns7()
    tracker = ns["AchievementTracker"]()
    tracker.add_achievement(_ach(ns, 1, "First Kill", 1))
    tracker.add_achievement(_ach(ns, 2, "10 Kills",  10))
    tracker.add_achievement(_ach(ns, 3, "100 Kills", 100))
    tracker.update_progress(1, 1)
    tracker.update_progress(2, 10)
    tracker.update_progress(3, 50)
    assert tracker.total_unlocked == 2
    assert tracker.is_unlocked(3) == False

def t_ach_no_double():
    ns = _ns7()
    tracker = ns["AchievementTracker"]()
    tracker.add_achievement(_ach(ns, 1, "First Kill", 1))
    tracker.update_progress(1, 1)
    tracker.update_progress(1, 1)  # again — already unlocked
    assert tracker.total_unlocked == 1

def t_ach_unknown_fails():
    ns = _ns7()
    tracker = ns["AchievementTracker"]()
    r = tracker.update_progress(999, 1)
    assert r.is_failure

test("achievement: starts locked",              t_ach_locked)
test("achievement: unlocks at threshold",       t_ach_unlocks)
test("achievement: partial progress",           t_ach_partial)
test("achievement: incremental unlock",         t_ach_incremental)
test("achievement: multiple independent",       t_ach_multiple)
test("achievement: no double-count unlock",     t_ach_no_double)
test("achievement: unknown id fails",           t_ach_unknown_fails)


# ════════════════════════════════════════════════════════════
# PROGRAM 8 — DATA PIPELINE (VALIDATION + TRANSFORM)
# ════════════════════════════════════════════════════════════
# Tests: multi-step result[T] chaining, kind errors,
#        grade computation, score display, complete transform
# ════════════════════════════════════════════════════════════

section("Program 8 — Data Pipeline")

DATA_PIPELINE = """kind PipelineError >>
    empty_name
    name_too_long
    negative_score
    score_overflow
    invalid_level
<< PipelineError

data RawInput >>
    name  :: string
    score :: int
    level :: int
<< RawInput

entity PlayerPipeline >>
    last_grade    :: string = ""
    last_display  :: string = ""

    validate_name(raw: RawInput) -> result[RawInput]
        if raw.name == "" >>
            fail PipelineError.empty_name
        << raw.name == ""
        if raw.name.__len__() > 20 >>
            fail PipelineError.name_too_long
        << raw.name.__len__() > 20
        succeed raw
    << validate_name

    validate_score(raw: RawInput) -> result[RawInput]
        if raw.score < 0 >>
            fail PipelineError.negative_score
        << raw.score < 0
        if raw.score > 999999 >>
            fail PipelineError.score_overflow
        << raw.score > 999999
        succeed raw
    << validate_score

    validate_level(raw: RawInput) -> result[RawInput]
        if raw.level < 1 >>
            fail PipelineError.invalid_level
        << raw.level < 1
        if raw.level > 99 >>
            fail PipelineError.invalid_level
        << raw.level > 99
        succeed raw
    << validate_level

    compute_grade(score: int) -> string
        if score >= 900000 >>
            result "S"
        << score >= 900000
        if score >= 700000 >>
            result "A"
        << score >= 700000
        if score >= 500000 >>
            result "B"
        << score >= 500000
        if score >= 300000 >>
            result "C"
        << score >= 300000
        result "D"
    << compute_grade

    process(raw: RawInput) -> result[int]
        step1 :: result[RawInput] = validate_name(raw)
        if step1.is_failure >>
            fail step1.error
        << step1.is_failure

        step2 :: result[RawInput] = validate_score(step1.value)
        if step2.is_failure >>
            fail step2.error
        << step2.is_failure

        step3 :: result[RawInput] = validate_level(step2.value)
        if step3.is_failure >>
            fail step3.error
        << step3.is_failure

        validated :: RawInput = step3.value
        last_grade = compute_grade(validated.score)

        if validated.score >= 1000 >>
            last_display = "High Score!"
        << validated.score >= 1000
        else >>
            last_display = "Keep trying!"
        << else

        succeed validated.score
    << process

<< PlayerPipeline"""

def _ns8():
    return run(DATA_PIPELINE)

def _raw(ns, name="Player", score=500, level=1):
    return ns["RawInput"](name=name, score=score, level=level)

def t_pipe_valid():
    ns = _ns8()
    pp = ns["PlayerPipeline"]()
    r = pp.process(_raw(ns, "AJ", 5000, 10))
    assert r.is_success and r.value == 5000

def t_pipe_empty_name():
    ns = _ns8()
    pp = ns["PlayerPipeline"]()
    PE = ns["PipelineError"]
    r = pp.process(_raw(ns, name=""))
    assert r.is_failure and r.error == PE.empty_name

def t_pipe_long_name():
    ns = _ns8()
    pp = ns["PlayerPipeline"]()
    PE = ns["PipelineError"]
    r = pp.process(_raw(ns, name="A" * 21))
    assert r.is_failure and r.error == PE.name_too_long

def t_pipe_neg_score():
    ns = _ns8()
    pp = ns["PlayerPipeline"]()
    PE = ns["PipelineError"]
    r = pp.process(_raw(ns, score=-1))
    assert r.is_failure and r.error == PE.negative_score

def t_pipe_overflow():
    ns = _ns8()
    pp = ns["PlayerPipeline"]()
    PE = ns["PipelineError"]
    r = pp.process(_raw(ns, score=1000000))
    assert r.is_failure and r.error == PE.score_overflow

def t_pipe_bad_level():
    ns = _ns8()
    pp = ns["PlayerPipeline"]()
    PE = ns["PipelineError"]
    assert pp.process(_raw(ns, level=0)).error   == PE.invalid_level
    assert pp.process(_raw(ns, level=100)).error == PE.invalid_level

def t_pipe_grade_s():
    ns = _ns8()
    pp = ns["PlayerPipeline"]()
    pp.process(_raw(ns, score=950000))
    assert pp.last_grade == "S"

def t_pipe_grade_d():
    ns = _ns8()
    pp = ns["PlayerPipeline"]()
    pp.process(_raw(ns, score=100))
    assert pp.last_grade == "D"

def t_pipe_display_high():
    ns = _ns8()
    pp = ns["PlayerPipeline"]()
    pp.process(_raw(ns, score=5000))
    assert pp.last_display == "High Score!"

def t_pipe_display_low():
    ns = _ns8()
    pp = ns["PlayerPipeline"]()
    pp.process(_raw(ns, score=500))
    assert pp.last_display == "Keep trying!"

def t_pipe_all_grades():
    ns = _ns8()
    pp = ns["PlayerPipeline"]()
    cases = [(950000,"S"), (750000,"A"), (550000,"B"), (350000,"C"), (100,"D")]
    for score, expected_grade in cases:
        pp.process(_raw(ns, score=score))
        assert pp.last_grade == expected_grade, f"score={score}: expected {expected_grade}, got {pp.last_grade}"

test("pipeline: valid data succeeds",       t_pipe_valid)
test("pipeline: empty name fails",          t_pipe_empty_name)
test("pipeline: name too long fails",       t_pipe_long_name)
test("pipeline: negative score fails",      t_pipe_neg_score)
test("pipeline: score overflow fails",      t_pipe_overflow)
test("pipeline: invalid level fails",       t_pipe_bad_level)
test("pipeline: grade S at 950000",        t_pipe_grade_s)
test("pipeline: grade D at 100",           t_pipe_grade_d)
test("pipeline: display 'High Score!'",    t_pipe_display_high)
test("pipeline: display 'Keep trying!'",   t_pipe_display_low)
test("pipeline: all 5 grades correct",     t_pipe_all_grades)


# ════════════════════════════════════════════════════════════
print()
success = report()
sys.exit(0 if success else 1)
