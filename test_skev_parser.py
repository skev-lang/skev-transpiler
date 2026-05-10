"""
Skev Language - Parser Test Suite
Copyright (c) 2026 AJ. All Rights Reserved. skev.dev | skev.org

Tests every construct the parser handles.
Each test feeds Skev source into the parser and verifies
the resulting AST has the correct structure.

Run with: python3 test_skev_parser.py
"""

import sys
from skev_parser import (
    parse,
    Program, EntityDecl, DataDecl, KindDecl, AliasDecl, ImportDecl,
    PropertyDecl, ComponentDecl, EventHandler, FunctionDecl,
    IfStmt, MatchStmt, MatchArm, LoopStmt, AssignStmt, VarDecl,
    ReturnStmt, AssertStmt, ExprStmt,
    IntLiteral, FloatLiteral, StringLiteral, BoolLiteral, NothingLiteral,
    Identifier, MemberAccess, CallExpr, BinaryExpr, UnaryExpr,
    TypeExpr, PropagateExpr,
)

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
        print(f"     Assert: {e}")
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

def parse_ok(source):
    """Parse source, assert no errors, return program."""
    prog, errors = parse(source)
    assert len(errors) == 0, f"Unexpected errors: {[str(e) for e in errors]}"
    return prog

def first_decl(source):
    """Get the first declaration from source."""
    prog = parse_ok(source)
    assert len(prog.declarations) > 0, "No declarations found"
    return prog.declarations[0]

def first_body_item(source):
    """Get the first item in the first declaration's body."""
    decl = first_decl(source)
    assert hasattr(decl, 'body'), "Declaration has no body"
    assert len(decl.body) > 0, "Body is empty"
    return decl.body[0]


# ════════════════════════════════════════════════════════════
section("Import Declarations")
# ════════════════════════════════════════════════════════════

def t_import_simple():
    d = first_decl("import skev")
    assert isinstance(d, ImportDecl)
    assert d.path == "skev"

def t_import_dotted():
    d = first_decl("import skev.math")
    assert isinstance(d, ImportDecl)
    assert d.path == "skev.math"

def t_import_deep():
    d = first_decl("import skev.network.http")
    assert isinstance(d, ImportDecl)
    assert d.path == "skev.network.http"

test("import skev",              t_import_simple)
test("import skev.math",         t_import_dotted)
test("import skev.network.http", t_import_deep)


# ════════════════════════════════════════════════════════════
section("Alias Declarations")
# ════════════════════════════════════════════════════════════

def t_alias_simple():
    d = first_decl("alias EntityID = uint32")
    assert isinstance(d, AliasDecl)
    assert d.name == "EntityID"
    assert "uint32" in d.target

def t_alias_generic():
    d = first_decl("alias Grid[T] = list[list[T]]")
    assert isinstance(d, AliasDecl)
    assert d.name == "Grid"
    assert "T" in d.generic_params

test("alias EntityID = uint32",    t_alias_simple)
test("alias Grid[T] = list[list]", t_alias_generic)


# ════════════════════════════════════════════════════════════
section("Kind Declarations")
# ════════════════════════════════════════════════════════════

def t_kind_basic():
    d = first_decl("""kind GameState >>
    menu
    playing
    paused
<< GameState""")
    assert isinstance(d, KindDecl)
    assert d.name == "GameState"
    assert "menu" in d.variants
    assert "playing" in d.variants
    assert "paused" in d.variants

def t_kind_single():
    d = first_decl("""kind Color >>
    red
<< Color""")
    assert isinstance(d, KindDecl)
    assert len(d.variants) == 1
    assert d.variants[0] == "red"

def t_kind_many():
    d = first_decl("""kind DamageType >>
    physical
    fire
    ice
    poison
    magic
<< DamageType""")
    assert isinstance(d, KindDecl)
    assert len(d.variants) == 5

test("kind with 3 variants",  t_kind_basic)
test("kind with 1 variant",   t_kind_single)
test("kind with 5 variants",  t_kind_many)


# ════════════════════════════════════════════════════════════
section("Data Declarations")
# ════════════════════════════════════════════════════════════

def t_data_simple():
    d = first_decl("""data DamageEvent >>
    amount :: float
    critical :: bool
<< DamageEvent""")
    assert isinstance(d, DataDecl)
    assert d.name == "DamageEvent"
    assert len(d.body) == 2
    assert isinstance(d.body[0], PropertyDecl)
    assert d.body[0].name == "amount"

def t_data_with_defaults():
    d = first_decl("""data PlayerData >>
    name   :: string
    health :: int = 100
    level  :: int = 1
<< PlayerData""")
    assert isinstance(d, DataDecl)
    assert len(d.body) == 3
    health_prop = d.body[1]
    assert health_prop.name == "health"
    assert isinstance(health_prop.value, IntLiteral)
    assert health_prop.value.value == 100

def t_data_generic():
    d = first_decl("""data Pair[A, B] >>
    first  :: A
    second :: B
<< Pair""")
    assert isinstance(d, DataDecl)
    assert d.name == "Pair"
    assert "A" in d.generic_params
    assert "B" in d.generic_params

test("data with 2 fields",       t_data_simple)
test("data with default values",  t_data_with_defaults)
test("data with generic params",  t_data_generic)


# ════════════════════════════════════════════════════════════
section("Entity Declarations")
# ════════════════════════════════════════════════════════════

def t_entity_empty():
    d = first_decl("entity Player >>\n<< Player")
    assert isinstance(d, EntityDecl)
    assert d.name == "Player"
    assert d.body == []

def t_entity_with_property():
    d = first_decl("""entity Player >>
    health :: int = 100
<< Player""")
    assert isinstance(d, EntityDecl)
    assert len(d.body) == 1
    assert isinstance(d.body[0], PropertyDecl)
    assert d.body[0].name == "health"

def t_entity_with_component():
    d = first_decl("""entity Player >>
    has Physics
<< Player""")
    assert isinstance(d, EntityDecl)
    assert len(d.body) == 1
    assert isinstance(d.body[0], ComponentDecl)
    assert d.body[0].component_name == "Physics"

def t_entity_with_multiple_components():
    d = first_decl("""entity Player >>
    has Physics
    has AudioSource
    has NetworkSync
<< Player""")
    assert isinstance(d, EntityDecl)
    comps = [b for b in d.body if isinstance(b, ComponentDecl)]
    assert len(comps) == 3

def t_entity_with_event():
    d = first_decl("""entity Player >>
    when update(delta)
        health = 100
    << update
<< Player""")
    assert isinstance(d, EntityDecl)
    when = d.body[0]
    assert isinstance(when, EventHandler)
    assert when.event_name == "update"

def t_entity_name_preserved():
    d = first_decl("""entity DragonBoss >>
    attack_power :: int = 999
<< DragonBoss""")
    assert d.name == "DragonBoss"

test("entity empty body",             t_entity_empty)
test("entity with property",          t_entity_with_property)
test("entity with component",         t_entity_with_component)
test("entity with 3 components",      t_entity_with_multiple_components)
test("entity with event handler",     t_entity_with_event)
test("entity PascalCase name kept",   t_entity_name_preserved)


# ════════════════════════════════════════════════════════════
section("Property Declarations")
# ════════════════════════════════════════════════════════════

def t_prop_int():
    d = first_decl("entity E >>\n    health :: int\n<< E")
    p = d.body[0]
    assert isinstance(p, PropertyDecl)
    assert p.name == "health"
    assert p.type_expr.name == "int"
    assert p.value is None

def t_prop_with_default():
    d = first_decl("entity E >>\n    speed :: float = 5.0\n<< E")
    p = d.body[0]
    assert p.name == "speed"
    assert isinstance(p.value, FloatLiteral)
    assert abs(p.value.value - 5.0) < 1e-9

def t_prop_bool_default():
    d = first_decl("entity E >>\n    alive :: bool = true\n<< E")
    p = d.body[0]
    assert isinstance(p.value, BoolLiteral)
    assert p.value.value == True

def t_prop_string_default():
    d = first_decl('entity E >>\n    name :: string = "Dragon"\n<< E')
    p = d.body[0]
    assert isinstance(p.value, StringLiteral)
    assert p.value.value == "Dragon"

def t_prop_fixed_modifier():
    d = first_decl("entity E >>\n    fixed MAX :: int = 100\n<< E")
    p = d.body[0]
    assert "fixed" in p.modifiers

def t_prop_shared_modifier():
    d = first_decl("entity E >>\n    shared score :: int = 0\n<< E")
    p = d.body[0]
    assert "shared" in p.modifiers

def t_prop_maybe_type():
    d = first_decl("entity E >>\n    target :: maybe Enemy\n<< E")
    p = d.body[0]
    assert p.type_expr.name == "maybe"

def t_prop_generic_type():
    d = first_decl("entity E >>\n    items :: list[Item]\n<< E")
    p = d.body[0]
    assert p.type_expr.name == "list"
    assert len(p.type_expr.params) == 1
    assert p.type_expr.params[0].name == "Item"

def t_prop_game_native():
    d = first_decl("entity E >>\n    pos :: Vector3!\n<< E")
    p = d.body[0]
    assert p.type_expr.name == "Vector3!"

test("property: int type, no default",  t_prop_int)
test("property: float with default",    t_prop_with_default)
test("property: bool = true",           t_prop_bool_default)
test('property: string = "Dragon"',     t_prop_string_default)
test("property: fixed modifier",        t_prop_fixed_modifier)
test("property: shared modifier",       t_prop_shared_modifier)
test("property: maybe type",            t_prop_maybe_type)
test("property: list[Item] type",       t_prop_generic_type)
test("property: Vector3! game-native",  t_prop_game_native)


# ════════════════════════════════════════════════════════════
section("Event Handlers")
# ════════════════════════════════════════════════════════════

def t_when_no_params():
    d = first_decl("""entity E >>
    when destroyed
        cleanup()
    << destroyed
<< E""")
    w = d.body[0]
    assert isinstance(w, EventHandler)
    assert w.event_name == "destroyed"
    assert w.params == []

def t_when_one_param():
    d = first_decl("""entity E >>
    when update(delta)
        move(delta)
    << update
<< E""")
    w = d.body[0]
    assert w.event_name == "update"
    assert len(w.params) == 1
    assert w.params[0][0] == "delta"

def t_when_typed_param():
    d = first_decl("""entity E >>
    when collision(other: Enemy)
        take_damage(10)
    << collision: Enemy
<< E""")
    w = d.body[0]
    assert w.event_name == "collision"
    assert w.params[0][0] == "other"
    assert w.params[0][1] == "Enemy"
    assert w.close_type == "Enemy"

def t_when_body_has_statements():
    d = first_decl("""entity E >>
    when update(delta)
        health = 100
        speed = 5.0
    << update
<< E""")
    w = d.body[0]
    assert len(w.body) == 2

test("when: no params",         t_when_no_params)
test("when: one param",         t_when_one_param)
test("when: typed param + close_type", t_when_typed_param)
test("when: body has 2 stmts",  t_when_body_has_statements)


# ════════════════════════════════════════════════════════════
section("Function Declarations")
# ════════════════════════════════════════════════════════════

def t_fn_simple():
    d = first_decl("""entity E >>
    take_damage(amount: int) -> nothing
        health = 0
    << take_damage
<< E""")
    fn = d.body[0]
    assert isinstance(fn, FunctionDecl)
    assert fn.name == "take_damage"
    assert fn.params[0][0] == "amount"
    assert fn.params[0][1] == "int"
    assert fn.return_type.name == "nothing"

def t_fn_result_return():
    d = first_decl("""entity E >>
    validate(v: int) -> result[int]
        succeed v
    << validate
<< E""")
    fn = d.body[0]
    assert fn.return_type.name == "result"

def t_fn_top_level():
    # Standalone function at top level
    prog = parse_ok("""identity(value: int) -> int
    result value
<< identity""")
    assert len(prog.declarations) == 1
    assert isinstance(prog.declarations[0], FunctionDecl)
    assert prog.declarations[0].name == "identity"

test("function with return type",     t_fn_simple)
test("function returning result[T]",  t_fn_result_return)
test("top-level standalone function", t_fn_top_level)


# ════════════════════════════════════════════════════════════
section("If Statements")
# ════════════════════════════════════════════════════════════

def t_if_basic():
    d = first_decl("""entity E >>
    when update(delta)
        if health < 0 >>
            die()
        << health < 0
    << update
<< E""")
    w = d.body[0]
    stmt = w.body[0]
    assert isinstance(stmt, IfStmt)
    assert isinstance(stmt.condition, BinaryExpr)
    assert stmt.condition.operator == "<"
    assert len(stmt.then_body) == 1

def t_if_else():
    d = first_decl("""entity E >>
    when update(delta)
        if alive >>
            move()
        << alive
        else >>
            die()
        << else
    << update
<< E""")
    w = d.body[0]
    stmt = w.body[0]
    assert isinstance(stmt, IfStmt)
    assert len(stmt.then_body) == 1
    assert len(stmt.else_body) == 1

def t_if_condition_is_binary():
    d = first_decl("""entity E >>
    when update(delta)
        if health < 100 >>
            heal()
        << health < 100
    << update
<< E""")
    stmt = d.body[0].body[0]
    cond = stmt.condition
    assert isinstance(cond, BinaryExpr)
    assert cond.operator == "<"
    assert isinstance(cond.left, Identifier)
    assert cond.left.name == "health"
    assert isinstance(cond.right, IntLiteral)
    assert cond.right.value == 100

test("if: basic with then body",  t_if_basic)
test("if: with else branch",      t_if_else)
test("if: condition is BinaryExpr", t_if_condition_is_binary)


# ════════════════════════════════════════════════════════════
section("Match Statements")
# ════════════════════════════════════════════════════════════

def t_match_inline_arms():
    d = first_decl("""entity E >>
    when update(delta)
        match state >>
            menu    -> show_menu()
            playing -> run_game()
        << state
    << update
<< E""")
    stmt = d.body[0].body[0]
    assert isinstance(stmt, MatchStmt)
    assert len(stmt.arms) == 2
    assert stmt.arms[0].is_inline == True
    assert stmt.arms[1].is_inline == True

def t_match_value_is_identifier():
    d = first_decl("""entity E >>
    when update(delta)
        match state >>
            menu -> show_menu()
        << state
    << update
<< E""")
    stmt = d.body[0].body[0]
    assert isinstance(stmt.value, Identifier)
    assert stmt.value.name == "state"

def t_match_arm_patterns():
    d = first_decl("""entity E >>
    when update(delta)
        match state >>
            menu    -> show_menu()
            playing -> run_game()
        << state
    << update
<< E""")
    stmt = d.body[0].body[0]
    patterns = [arm.pattern for arm in stmt.arms]
    assert isinstance(patterns[0], Identifier)
    assert patterns[0].name == "menu"

test("match: inline arms (->)",      t_match_inline_arms)
test("match: value is identifier",   t_match_value_is_identifier)
test("match: arm patterns correct",  t_match_arm_patterns)


# ════════════════════════════════════════════════════════════
section("Loop Statements")
# ════════════════════════════════════════════════════════════

def t_loop_iterate():
    d = first_decl("""entity E >>
    when update(delta)
        loop item in enemies >>
            item.damage()
        << item
    << update
<< E""")
    stmt = d.body[0].body[0]
    assert isinstance(stmt, LoopStmt)
    assert stmt.kind == "iterate"
    assert stmt.var_name == "item"
    assert isinstance(stmt.iterable, Identifier)
    assert stmt.iterable.name == "enemies"

def t_loop_range():
    d = first_decl("""entity E >>
    when update(delta)
        loop i from 0 to 10 >>
            tick(i)
        << i
    << update
<< E""")
    stmt = d.body[0].body[0]
    assert isinstance(stmt, LoopStmt)
    assert stmt.kind == "range"
    assert stmt.var_name == "i"
    assert isinstance(stmt.from_expr, IntLiteral)
    assert stmt.from_expr.value == 0
    assert isinstance(stmt.to_expr, IntLiteral)
    assert stmt.to_expr.value == 10

def t_loop_while():
    d = first_decl("""entity E >>
    when update(delta)
        loop while alive >>
            move()
        << while alive
    << update
<< E""")
    stmt = d.body[0].body[0]
    assert isinstance(stmt, LoopStmt)
    assert stmt.kind == "while"
    assert isinstance(stmt.condition, Identifier)
    assert stmt.condition.name == "alive"

def t_loop_body():
    d = first_decl("""entity E >>
    when update(delta)
        loop item in items >>
            use(item)
            discard(item)
        << item
    << update
<< E""")
    stmt = d.body[0].body[0]
    assert len(stmt.body) == 2

test("loop: iterate over collection", t_loop_iterate)
test("loop: range from 0 to 10",      t_loop_range)
test("loop: while condition",          t_loop_while)
test("loop: body has statements",      t_loop_body)


# ════════════════════════════════════════════════════════════
section("Assignment Statements")
# ════════════════════════════════════════════════════════════

def t_assign_simple():
    d = first_decl("""entity E >>
    when update(delta)
        health = 100
    << update
<< E""")
    stmt = d.body[0].body[0]
    assert isinstance(stmt, AssignStmt)
    assert isinstance(stmt.target, Identifier)
    assert stmt.target.name == "health"
    assert isinstance(stmt.value, IntLiteral)
    assert stmt.value.value == 100
    assert stmt.operator == "="

def t_assign_augmented_plus():
    d = first_decl("""entity E >>
    when update(delta)
        health += 10
    << update
<< E""")
    stmt = d.body[0].body[0]
    assert isinstance(stmt, AssignStmt)
    assert stmt.operator == "+="

def t_assign_augmented_minus():
    d = first_decl("""entity E >>
    when update(delta)
        health -= damage
    << update
<< E""")
    stmt = d.body[0].body[0]
    assert isinstance(stmt, AssignStmt)
    assert stmt.operator == "-="

test("assignment: simple = ",    t_assign_simple)
test("assignment: += augmented", t_assign_augmented_plus)
test("assignment: -= augmented", t_assign_augmented_minus)


# ════════════════════════════════════════════════════════════
section("Return Statements")
# ════════════════════════════════════════════════════════════

def t_succeed_int():
    d = first_decl("""entity E >>
    validate() -> result[int]
        succeed 42
    << validate
<< E""")
    fn = d.body[0]
    stmt = fn.body[0]
    assert isinstance(stmt, ReturnStmt)
    assert stmt.kind == "succeed"
    assert isinstance(stmt.value, IntLiteral)
    assert stmt.value.value == 42

def t_fail_error():
    d = first_decl("""entity E >>
    validate(v: int) -> result[int]
        fail MyError.invalid
    << validate
<< E""")
    fn = d.body[0]
    stmt = fn.body[0]
    assert isinstance(stmt, ReturnStmt)
    assert stmt.kind == "fail"

def t_result_value():
    d = first_decl("""entity E >>
    get_health() -> int
        result health
    << get_health
<< E""")
    fn = d.body[0]
    stmt = fn.body[0]
    assert isinstance(stmt, ReturnStmt)
    assert stmt.kind == "result"

test("succeed 42",          t_succeed_int)
test("fail ErrorType",      t_fail_error)
test("result value",        t_result_value)


# ════════════════════════════════════════════════════════════
section("Expressions")
# ════════════════════════════════════════════════════════════

def t_int_literal():
    d = first_decl("entity E >>\n    x :: int = 42\n<< E")
    assert isinstance(d.body[0].value, IntLiteral)
    assert d.body[0].value.value == 42

def t_float_literal():
    d = first_decl("entity E >>\n    x :: float = 3.14\n<< E")
    assert isinstance(d.body[0].value, FloatLiteral)
    assert abs(d.body[0].value.value - 3.14) < 1e-9

def t_string_literal():
    d = first_decl('entity E >>\n    x :: string = "hello"\n<< E')
    assert isinstance(d.body[0].value, StringLiteral)
    assert d.body[0].value.value == "hello"

def t_true_literal():
    d = first_decl("entity E >>\n    x :: bool = true\n<< E")
    assert isinstance(d.body[0].value, BoolLiteral)
    assert d.body[0].value.value == True

def t_false_literal():
    d = first_decl("entity E >>\n    x :: bool = false\n<< E")
    assert isinstance(d.body[0].value, BoolLiteral)
    assert d.body[0].value.value == False

def t_nothing_literal():
    d = first_decl("entity E >>\n    x :: maybe int = nothing\n<< E")
    assert isinstance(d.body[0].value, NothingLiteral)

def t_binary_add():
    d = first_decl("""entity E >>
    when update(delta)
        x = a + b
    << update
<< E""")
    stmt = d.body[0].body[0]
    assert isinstance(stmt.value, BinaryExpr)
    assert stmt.value.operator == "+"

def t_binary_compare():
    d = first_decl("""entity E >>
    when update(delta)
        if health == 0 >>
            die()
        << health == 0
    << update
<< E""")
    if_stmt = d.body[0].body[0]
    assert isinstance(if_stmt.condition, BinaryExpr)
    assert if_stmt.condition.operator == "=="

def t_member_access():
    d = first_decl("""entity E >>
    when update(delta)
        x = player.health
    << update
<< E""")
    stmt = d.body[0].body[0]
    assert isinstance(stmt.value, MemberAccess)
    assert isinstance(stmt.value.obj, Identifier)
    assert stmt.value.obj.name == "player"
    assert stmt.value.member == "health"

def t_function_call():
    d = first_decl("""entity E >>
    when update(delta)
        take_damage(50)
    << update
<< E""")
    stmt = d.body[0].body[0]
    assert isinstance(stmt, ExprStmt)
    assert isinstance(stmt.expr, CallExpr)
    assert isinstance(stmt.expr.callee, Identifier)
    assert stmt.expr.callee.name == "take_damage"
    assert len(stmt.expr.args) == 1
    assert isinstance(stmt.expr.args[0], IntLiteral)
    assert stmt.expr.args[0].value == 50

def t_chained_member_call():
    d = first_decl("""entity E >>
    when update(delta)
        math.clamp(health, 0, 100)
    << update
<< E""")
    stmt = d.body[0].body[0]
    assert isinstance(stmt.expr, CallExpr)
    callee = stmt.expr.callee
    assert isinstance(callee, MemberAccess)
    assert callee.member == "clamp"

test("int literal 42",          t_int_literal)
test("float literal 3.14",      t_float_literal)
test("string literal 'hello'",  t_string_literal)
test("bool literal true",       t_true_literal)
test("bool literal false",      t_false_literal)
test("nothing literal",         t_nothing_literal)
test("binary expression a + b", t_binary_add)
test("binary compare ==",       t_binary_compare)
test("member access player.health", t_member_access)
test("function call take_damage(50)", t_function_call)
test("chained math.clamp()",    t_chained_member_call)


# ════════════════════════════════════════════════════════════
section("Assert Statements")
# ════════════════════════════════════════════════════════════

def t_assert_with_message():
    d = first_decl("""entity E >>
    validate(v: int) -> nothing
        assert v >= 0 "Value cannot be negative"
    << validate
<< E""")
    fn = d.body[0]
    stmt = fn.body[0]
    assert isinstance(stmt, AssertStmt)
    assert isinstance(stmt.condition, BinaryExpr)
    assert stmt.message == "Value cannot be negative"

test("assert with message", t_assert_with_message)


# ════════════════════════════════════════════════════════════
section("Full Entity — complete real Skev programs")
# ════════════════════════════════════════════════════════════

PLAYER_ENTITY = """entity Player >>
    health    :: int   = 100
    max_health :: int  = 100
    move_speed :: float = 5.0
    alive     :: bool  = true

    has Physics
    has AudioSource

    when update(delta)
        if alive >>
            move(move_speed * delta)
        << alive
    << update

    when collision(other: Enemy)
        health -= 10
        if health <= 0 >>
            alive = false
        << health <= 0
    << collision: Enemy

    take_damage(amount: int) -> nothing
        health = health - amount
    << take_damage

<< Player"""

def t_full_player_no_errors():
    prog, errors = parse(PLAYER_ENTITY)
    assert len(errors) == 0, f"Errors: {errors}"

def t_full_player_is_entity():
    prog = parse_ok(PLAYER_ENTITY)
    assert len(prog.declarations) == 1
    assert isinstance(prog.declarations[0], EntityDecl)
    assert prog.declarations[0].name == "Player"

def t_full_player_has_4_properties():
    prog = parse_ok(PLAYER_ENTITY)
    entity = prog.declarations[0]
    props = [b for b in entity.body if isinstance(b, PropertyDecl)]
    assert len(props) == 4, f"Expected 4 properties, got {len(props)}"

def t_full_player_has_2_components():
    prog = parse_ok(PLAYER_ENTITY)
    entity = prog.declarations[0]
    comps = [b for b in entity.body if isinstance(b, ComponentDecl)]
    assert len(comps) == 2

def t_full_player_has_2_events():
    prog = parse_ok(PLAYER_ENTITY)
    entity = prog.declarations[0]
    events = [b for b in entity.body if isinstance(b, EventHandler)]
    assert len(events) == 2

def t_full_player_has_1_function():
    prog = parse_ok(PLAYER_ENTITY)
    entity = prog.declarations[0]
    fns = [b for b in entity.body if isinstance(b, FunctionDecl)]
    assert len(fns) == 1
    assert fns[0].name == "take_damage"

def t_full_player_if_inside_event():
    prog = parse_ok(PLAYER_ENTITY)
    entity = prog.declarations[0]
    update_event = next(b for b in entity.body
                       if isinstance(b, EventHandler) and b.event_name == "update")
    assert len(update_event.body) == 1
    assert isinstance(update_event.body[0], IfStmt)

test("full Player: no parse errors",   t_full_player_no_errors)
test("full Player: is EntityDecl",     t_full_player_is_entity)
test("full Player: 4 properties",      t_full_player_has_4_properties)
test("full Player: 2 components",      t_full_player_has_2_components)
test("full Player: 2 event handlers",  t_full_player_has_2_events)
test("full Player: 1 function",        t_full_player_has_1_function)
test("full Player: if inside event",   t_full_player_if_inside_event)


# --- Combat system ---

COMBAT_SYSTEM = """kind DamageType >>
    physical
    fire
    ice
<< DamageType

data DamageEvent >>
    amount :: float
    type   :: DamageType
<< DamageEvent

entity CombatSystem >>
    damage_multiplier :: float = 1.0

    apply_damage(event: DamageEvent, target_health: int) -> result[int]
        if event.amount <= 0 >>
            fail CombatError.invalid_damage
        << event.amount <= 0
        new_health :: int = target_health - event.amount
        succeed new_health
    << apply_damage

<< CombatSystem"""

def t_combat_no_errors():
    prog, errors = parse(COMBAT_SYSTEM)
    assert len(errors) == 0, f"Errors: {[str(e) for e in errors]}"

def t_combat_3_declarations():
    prog = parse_ok(COMBAT_SYSTEM)
    assert len(prog.declarations) == 3

def t_combat_kind_first():
    prog = parse_ok(COMBAT_SYSTEM)
    assert isinstance(prog.declarations[0], KindDecl)
    assert prog.declarations[0].name == "DamageType"

def t_combat_data_second():
    prog = parse_ok(COMBAT_SYSTEM)
    assert isinstance(prog.declarations[1], DataDecl)
    assert prog.declarations[1].name == "DamageEvent"

def t_combat_entity_third():
    prog = parse_ok(COMBAT_SYSTEM)
    assert isinstance(prog.declarations[2], EntityDecl)
    assert prog.declarations[2].name == "CombatSystem"

test("combat system: no errors",       t_combat_no_errors)
test("combat system: 3 declarations",  t_combat_3_declarations)
test("combat system: kind first",      t_combat_kind_first)
test("combat system: data second",     t_combat_data_second)
test("combat system: entity third",    t_combat_entity_third)


# ════════════════════════════════════════════════════════════
section("Line Numbers")
# ════════════════════════════════════════════════════════════

def t_entity_line_number():
    prog = parse_ok("""entity Player >>
    health :: int = 100
<< Player""")
    assert prog.declarations[0].line == 1

def t_property_line_number():
    prog = parse_ok("""entity Player >>
    health :: int = 100
<< Player""")
    prop = prog.declarations[0].body[0]
    assert prop.line == 2

test("entity declaration on line 1",  t_entity_line_number)
test("property declaration on line 2", t_property_line_number)


# ════════════════════════════════════════════════════════════
print()
success = report()
sys.exit(0 if success else 1)
