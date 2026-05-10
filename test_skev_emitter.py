"""
Skev Language - Emitter Test Suite
Copyright (c) 2026 AJ. All Rights Reserved. skev.dev | skev.org

Tests that Skev source code:
  1. Emits correct Python code (structure tests)
  2. Actually RUNS and produces correct results (execution tests)

This is the most important test file so far — it proves
Skev programs execute correctly, not just parse correctly.

Run with: python3 test_skev_emitter.py
"""
import sys
from skev_emitter import emit
from skev_runtime import succeed, fail, some, nothing, math, Entity, SkevData, Maybe

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

# ── Helpers ──────────────────────────────────────────────────

def emit_ok(source):
    """Emit source, assert no errors, return Python code."""
    code, errors = emit(source)
    assert len(errors) == 0, f"Emit errors: {[str(e) for e in errors]}"
    assert len(code) > 0, "Empty output"
    return code

def run(source):
    """
    Emit Skev source, execute it, and return the local namespace.
    This lets tests inspect classes and values after execution.
    """
    code = emit_ok(source)
    namespace = {}
    exec(code, namespace)
    return namespace


# ════════════════════════════════════════════════════════════
section("Emit Structure — code generation correctness")
# ════════════════════════════════════════════════════════════

def t_emit_header():
    code = emit_ok("import skev.math")
    assert "from skev_runtime import" in code
    assert "from enum import Enum" in code

def t_emit_kind():
    code = emit_ok("kind GameState >>\n    menu\n    playing\n<< GameState")
    assert "class GameState(Enum):" in code
    assert 'menu = "menu"' in code
    assert 'playing = "playing"' in code

def t_emit_data():
    code = emit_ok("data Point >>\n    x :: float\n    y :: float\n<< Point")
    assert "class Point(SkevData):" in code
    assert "self.x = x" in code
    assert "self.y = y" in code

def t_emit_entity_class():
    code = emit_ok("entity Player >>\n    health :: int = 100\n<< Player")
    assert "class Player(Entity):" in code
    assert "def __init__(self):" in code
    assert "self.health = 100" in code

def t_emit_component():
    code = emit_ok("""entity Player >>
    has Physics
<< Player""")
    assert "self.attach(Physics())" in code

def t_emit_event_handler():
    code = emit_ok("""entity Player >>
    health :: int = 100
    when update(delta)
        health = 50
    << update
<< Player""")
    assert "def on_update(self, delta):" in code
    assert "self.health = 50" in code

def t_emit_self_prefix():
    # Properties used inside methods get self. prefix
    code = emit_ok("""entity Player >>
    health :: int = 100
    when update(delta)
        health = 0
    << update
<< Player""")
    assert "self.health = 0" in code

def t_emit_no_self_for_params():
    # Parameters should NOT get self. prefix
    code = emit_ok("""entity Player >>
    health :: int = 100
    when collision(damage: int)
        health -= damage
    << collision
<< Player""")
    assert "self.health -= damage" in code
    # 'damage' is a param, should not be self.damage
    assert "self.damage" not in code

def t_emit_method():
    code = emit_ok("""entity Player >>
    health :: int = 100
    take_damage(amount: int) -> nothing
        health -= amount
    << take_damage
<< Player""")
    assert "def take_damage(self, amount):" in code
    assert "self.health -= amount" in code

def t_emit_succeed():
    code = emit_ok("""entity Player >>
    get_health() -> result[int]
        succeed health
    << get_health
    health :: int = 100
<< Player""")
    assert "return succeed(self.health)" in code

def t_emit_fail():
    code = emit_ok("""entity Player >>
    health :: int = 0
    validate() -> result[int]
        fail ValidationError.negative
    << validate
<< Player""")
    assert "return fail(ValidationError.negative)" in code

def t_emit_if():
    code = emit_ok("""entity Player >>
    health :: int = 100
    when update(delta)
        if health < 0 >>
            health = 0
        << health < 0
    << update
<< Player""")
    assert "if (self.health < 0):" in code
    assert "self.health = 0" in code

def t_emit_match():
    code = emit_ok("""kind State >>
    menu
    playing
<< State

entity Game >>
    state :: State
    when update(delta)
        match state >>
            menu -> show_menu()
            playing -> run_game()
        << state
    << update
<< Game""")
    assert "_m" in code  # match temp var
    assert "show_menu()" in code

def t_emit_loop_iterate():
    code = emit_ok("""entity Game >>
    items :: list[int]
    when update(delta)
        loop item in items >>
            process(item)
        << item
    << update
<< Game""")
    assert "for item in self.items:" in code

def t_emit_loop_range():
    code = emit_ok("""entity Game >>
    when update(delta)
        loop i from 0 to 10 >>
            tick(i)
        << i
    << update
<< Game""")
    assert "for i in range(0, 10):" in code

def t_emit_loop_while():
    code = emit_ok("""entity Game >>
    running :: bool = true
    when update(delta)
        loop while running >>
            step()
        << while running
    << update
<< Game""")
    assert "while self.running:" in code

def t_emit_standalone_function():
    code = emit_ok("""clamp_val(v: int, lo: int, hi: int) -> int
    result v
<< clamp_val""")
    assert "def clamp_val(v, lo, hi):" in code
    assert "return v" in code

test("header imports present",         t_emit_header)
test("kind emits as Enum",             t_emit_kind)
test("data emits as SkevData class",   t_emit_data)
test("entity emits as Entity class",   t_emit_entity_class)
test("has → self.attach()",            t_emit_component)
test("when → def on_event()",          t_emit_event_handler)
test("self. prefix on properties",     t_emit_self_prefix)
test("params: no self. prefix",        t_emit_no_self_for_params)
test("function → def method(self)",    t_emit_method)
test("succeed → return succeed()",     t_emit_succeed)
test("fail → return fail()",           t_emit_fail)
test("if → Python if:",                t_emit_if)
test("match → if/elif chain",          t_emit_match)
test("loop iterate → for in",          t_emit_loop_iterate)
test("loop range → for in range()",    t_emit_loop_range)
test("loop while → while",             t_emit_loop_while)
test("standalone function",            t_emit_standalone_function)


# ════════════════════════════════════════════════════════════
section("Execution — Skev programs that actually RUN")
# ════════════════════════════════════════════════════════════

def t_run_kind():
    """kind declarations create usable Python Enums."""
    ns = run("""kind GameState >>
    menu
    playing
    paused
<< GameState""")
    GS = ns["GameState"]
    assert GS.menu.value == "menu"
    assert GS.playing.value == "playing"
    assert GS.paused.value == "paused"
    # Enum members are distinct
    assert GS.menu != GS.playing

def t_run_data():
    """data declarations create instantiatable classes."""
    ns = run("""data DamageEvent >>
    amount :: float
    critical :: bool
<< DamageEvent""")
    DE = ns["DamageEvent"]
    event = DE(amount=50.0, critical=True)
    assert event.amount == 50.0
    assert event.critical == True

def t_run_data_defaults():
    """data type defaults work correctly."""
    ns = run("""data PlayerData >>
    health :: int
    name :: string
<< PlayerData""")
    PD = ns["PlayerData"]
    p = PD()   # use defaults
    assert p.health == 0
    assert p.name == ""

def t_run_entity_properties():
    """Entity properties are accessible and have correct defaults."""
    ns = run("""entity Player >>
    health    :: int   = 100
    max_health :: int  = 100
    alive     :: bool  = true
    speed     :: float = 5.0
<< Player""")
    Player = ns["Player"]
    p = Player()
    assert p.health == 100
    assert p.max_health == 100
    assert p.alive == True
    assert abs(p.speed - 5.0) < 1e-9

def t_run_entity_method():
    """Entity methods execute correctly and access self properties."""
    ns = run("""entity Player >>
    health :: int = 100
    take_damage(amount: int) -> nothing
        health -= amount
    << take_damage
<< Player""")
    Player = ns["Player"]
    p = Player()
    assert p.health == 100
    p.take_damage(30)
    assert p.health == 70

def t_run_entity_method_clamp():
    """Entity method using math.clamp."""
    ns = run("""entity Player >>
    health :: int = 100
    take_damage(amount: int) -> nothing
        health = math.clamp(health - amount, 0, 100)
    << take_damage
<< Player""")
    Player = ns["Player"]
    p = Player()
    p.take_damage(150)
    assert p.health == 0   # clamped at 0

def t_run_event_handler():
    """Event handlers run correctly when called."""
    ns = run("""entity Counter >>
    count :: int = 0
    when update(delta)
        count += 1
    << update
<< Counter""")
    Counter = ns["Counter"]
    c = Counter()
    assert c.count == 0
    c.on_update(0.016)
    assert c.count == 1
    c.on_update(0.016)
    assert c.count == 2

def t_run_if_statement():
    """If statement branches correctly."""
    ns = run("""entity Player >>
    health :: int = 100
    alive  :: bool = true
    check_alive() -> nothing
        if health <= 0 >>
            alive = false
        << health <= 0
    << check_alive
<< Player""")
    Player = ns["Player"]
    p = Player()
    assert p.alive == True
    p.health = 0
    p.check_alive()
    assert p.alive == False

def t_run_if_else():
    """If/else branches correctly."""
    ns = run("""entity Spawner >>
    count :: int = 0
    label :: string = ""
    spawn(is_player: bool) -> nothing
        if is_player >>
            label = "player"
        << is_player
        else >>
            label = "enemy"
        << else
        count += 1
    << spawn
<< Spawner""")
    Spawner = ns["Spawner"]
    s = Spawner()
    s.spawn(True)
    assert s.label == "player"
    assert s.count == 1
    s.spawn(False)
    assert s.label == "enemy"
    assert s.count == 2

def t_run_succeed():
    """succeed returns a Result with success."""
    ns = run("""entity Validator >>
    validate(v: int) -> result[int]
        succeed v
    << validate
<< Validator""")
    Validator = ns["Validator"]
    v = Validator()
    r = v.validate(42)
    assert r.is_success
    assert r.value == 42

def t_run_fail():
    """fail returns a Result with failure."""
    ns = run("""kind ValidationError >>
    negative
    too_large
<< ValidationError

entity Validator >>
    validate(v: int) -> result[int]
        if v < 0 >>
            fail ValidationError.negative
        << v < 0
        succeed v
    << validate
<< Validator""")
    Validator  = ns["Validator"]
    VE = ns["ValidationError"]
    v = Validator()
    r = v.validate(-5)
    assert r.is_failure
    assert r.error == VE.negative
    r2 = v.validate(42)
    assert r2.is_success
    assert r2.value == 42

def t_run_loop_range():
    """Range loop executes the right number of times."""
    ns = run("""entity Counter >>
    total :: int = 0
    run_loop() -> nothing
        loop i from 0 to 5 >>
            total += i
        << i
    << run_loop
<< Counter""")
    Counter = ns["Counter"]
    c = Counter()
    c.run_loop()
    assert c.total == 0+1+2+3+4   # sum of 0..4

def t_run_loop_while():
    """While loop stops at the right condition."""
    ns = run("""entity Counter >>
    count :: int = 10
    run_loop() -> nothing
        loop while count > 0 >>
            count -= 1
        << while count > 0
    << run_loop
<< Counter""")
    Counter = ns["Counter"]
    c = Counter()
    c.run_loop()
    assert c.count == 0

def t_run_standalone_function():
    """Standalone functions work correctly."""
    ns = run("""double(v: int) -> int
    result v + v
<< double""")
    assert ns["double"](21) == 42

def t_run_assert_passes():
    """Assert that passes does nothing."""
    ns = run("""entity Player >>
    health :: int = 100
    check() -> nothing
        assert health >= 0 "Health must be non-negative"
    << check
<< Player""")
    Player = ns["Player"]
    p = Player()
    p.check()  # should not raise

def t_run_assert_fails():
    """Assert that fails raises SkevPanic."""
    from skev_runtime import SkevPanic
    ns = run("""entity Player >>
    health :: int = -1
    check() -> nothing
        assert health >= 0 "Health must be non-negative"
    << check
<< Player""")
    Player = ns["Player"]
    p = Player()
    try:
        p.check()
        assert False, "Should have raised SkevPanic"
    except SkevPanic as e:
        assert "Health must be non-negative" in str(e)


# ════════════════════════════════════════════════════════════
section("Full Programs — complete real-world Skev logic")
# ════════════════════════════════════════════════════════════

HEALTH_SYSTEM = """kind DamageType >>
    physical
    fire
    poison
<< DamageType

data DamageEvent >>
    amount :: float
    type   :: DamageType
<< DamageEvent

entity HealthSystem >>
    health     :: int = 100
    max_health :: int = 100
    alive      :: bool = true

    take_damage(event: DamageEvent) -> nothing
        health = math.clamp(health - event.amount, 0, max_health)
        if health <= 0 >>
            alive = false
        << health <= 0
    << take_damage

    heal(amount: int) -> nothing
        health = math.clamp(health + amount, 0, max_health)
    << heal

    get_health_percent() -> float
        result math.clamp(health / max_health, 0.0, 1.0)
    << get_health_percent

<< HealthSystem"""

def t_health_system_runs():
    ns = run(HEALTH_SYSTEM)
    HS = ns["HealthSystem"]
    DE = ns["DamageEvent"]
    DT = ns["DamageType"]
    hs = HS()
    assert hs.health == 100
    assert hs.alive == True

def t_health_system_take_damage():
    ns = run(HEALTH_SYSTEM)
    HS = ns["HealthSystem"]
    DE = ns["DamageEvent"]
    DT = ns["DamageType"]
    hs = HS()
    event = DE(amount=30.0, type_=DT.fire)
    hs.take_damage(event)
    assert hs.health == 70

def t_health_system_lethal_damage():
    ns = run(HEALTH_SYSTEM)
    HS = ns["HealthSystem"]
    DE = ns["DamageEvent"]
    DT = ns["DamageType"]
    hs = HS()
    event = DE(amount=200.0, type_=DT.physical)
    hs.take_damage(event)
    assert hs.health == 0
    assert hs.alive == False

def t_health_system_heal():
    ns = run(HEALTH_SYSTEM)
    HS = ns["HealthSystem"]
    hs = HS()
    hs.health = 50
    hs.heal(30)
    assert hs.health == 80

def t_health_system_heal_capped():
    ns = run(HEALTH_SYSTEM)
    HS = ns["HealthSystem"]
    hs = HS()
    hs.health = 90
    hs.heal(100)
    assert hs.health == 100   # clamped at max_health

def t_health_system_percent():
    ns = run(HEALTH_SYSTEM)
    HS = ns["HealthSystem"]
    hs = HS()
    hs.health = 50
    pct = hs.get_health_percent()
    assert abs(pct - 0.5) < 1e-9

test("health system: runs without error",       t_health_system_runs)
test("health system: take_damage reduces health", t_health_system_take_damage)
test("health system: lethal damage → alive=false", t_health_system_lethal_damage)
test("health system: heal increases health",    t_health_system_heal)
test("health system: heal capped at max",       t_health_system_heal_capped)
test("health system: get_health_percent()",     t_health_system_percent)


SCORE_SYSTEM = """entity ScoreSystem >>
    score       :: int = 0
    high_score  :: int = 0
    multiplier  :: int = 1

    add_score(points: int) -> nothing
        score += points * multiplier
        if score > high_score >>
            high_score = score
        << score > high_score
    << add_score

    reset() -> nothing
        score = 0
        multiplier = 1
    << reset

    set_multiplier(m: int) -> nothing
        multiplier = m
    << set_multiplier

    get_score() -> int
        result score
    << get_score

<< ScoreSystem"""

def t_score_basic():
    ns = run(SCORE_SYSTEM)
    SS = ns["ScoreSystem"]
    s = SS()
    s.add_score(100)
    assert s.score == 100

def t_score_multiplier():
    ns = run(SCORE_SYSTEM)
    SS = ns["ScoreSystem"]
    s = SS()
    s.set_multiplier(3)
    s.add_score(100)
    assert s.score == 300

def t_score_high_score():
    ns = run(SCORE_SYSTEM)
    SS = ns["ScoreSystem"]
    s = SS()
    s.add_score(500)
    s.add_score(200)   # score is now 700
    s.reset()
    assert s.score == 0
    assert s.high_score == 700   # preserved

def t_score_get():
    ns = run(SCORE_SYSTEM)
    SS = ns["ScoreSystem"]
    s = SS()
    s.add_score(42)
    assert s.get_score() == 42

test("score system: basic add_score",          t_score_basic)
test("score system: multiplier applied",       t_score_multiplier)
test("score system: high_score preserved",     t_score_high_score)
test("score system: get_score() returns int",  t_score_get)


ALGORITHM_TEST = """entity MathHelper >>
    clamp_health(health: int, max_hp: int) -> int
        result math.clamp(health, 0, max_hp)
    << clamp_health

    in_range(value: float, lo: float, hi: float) -> bool
        result value >= lo and value <= hi
    << in_range

    sum_range(n: int) -> int
        total :: int = 0
        loop i from 0 to n >>
            total += i
        << i
        result total
    << sum_range

    count_matching(threshold: int) -> int
        values :: list[int]
        count :: int = 0
        loop i from 0 to 5 >>
            if i > threshold >>
                count += 1
            << i > threshold
        << i
        result count
    << count_matching

<< MathHelper"""

def t_algo_clamp():
    ns = run(ALGORITHM_TEST)
    MH = ns["MathHelper"]
    m = MH()
    assert m.clamp_health(150, 100) == 100
    assert m.clamp_health(-5, 100) == 0
    assert m.clamp_health(50, 100) == 50

def t_algo_in_range():
    ns = run(ALGORITHM_TEST)
    MH = ns["MathHelper"]
    m = MH()
    assert m.in_range(5.0, 0.0, 10.0) == True
    assert m.in_range(15.0, 0.0, 10.0) == False

def t_algo_sum_range():
    ns = run(ALGORITHM_TEST)
    MH = ns["MathHelper"]
    m = MH()
    assert m.sum_range(5) == 0+1+2+3+4
    assert m.sum_range(0) == 0

def t_algo_count_matching():
    ns = run(ALGORITHM_TEST)
    MH = ns["MathHelper"]
    m = MH()
    # values 0,1,2,3,4 — how many > 2? → 3,4 = 2
    assert m.count_matching(2) == 2

test("algorithm: clamp_health",         t_algo_clamp)
test("algorithm: in_range check",       t_algo_in_range)
test("algorithm: sum_range loop",       t_algo_sum_range)
test("algorithm: count_matching loop",  t_algo_count_matching)


# Full entity tests
test("run kind → usable Enum",               t_run_kind)
test("run data → instantiatable class",      t_run_data)
test("run data → defaults work",             t_run_data_defaults)
test("run entity → properties correct",      t_run_entity_properties)
test("run entity method → mutates self",     t_run_entity_method)
test("run entity method → uses math.clamp",  t_run_entity_method_clamp)
test("run event handler → fires correctly",  t_run_event_handler)
test("run if statement → correct branch",    t_run_if_statement)
test("run if/else → both branches work",     t_run_if_else)
test("run succeed → Result.is_success",      t_run_succeed)
test("run fail → Result.is_failure + error", t_run_fail)
test("run loop range → correct iterations",  t_run_loop_range)
test("run loop while → stops correctly",     t_run_loop_while)
test("run standalone function",              t_run_standalone_function)
test("run assert → passes silently",         t_run_assert_passes)
test("run assert → panics correctly",        t_run_assert_fails)

print()
success = report()
sys.exit(0 if success else 1)
