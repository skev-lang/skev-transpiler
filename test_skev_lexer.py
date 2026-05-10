"""
╔══════════════════════════════════════════════════════════════╗
║           SKEV LANGUAGE — LEXER TEST SUITE                  ║
║                                                              ║
║  Copyright © 2026 AJ. All Rights Reserved.                   ║
║  skev.dev | skev.org                                         ║
╚══════════════════════════════════════════════════════════════╝

WHAT IS THIS FILE?
──────────────────
Tests for the Skev Lexer (skev_lexer.py).
Verifies that every kind of Skev source code is
correctly tokenised into the right token types.

HOW TO READ THE TESTS:
───────────────────────
Each test feeds a small piece of Skev source code
into the lexer, then checks:
  → Did it produce the right number of tokens?
  → Are the token types correct?
  → Are the token values correct?
  → Are error cases reported properly?

WHY THESE TESTS MATTER:
────────────────────────
If the lexer gets a token wrong, the parser will
misunderstand the program structure. Every future
step depends on the lexer being correct.

These tests cover EVERY token type in the spec.

Run with:  python3 test_skev_lexer.py
"""

import sys
from skev_lexer import tokenise, TokenType, Token, LexError

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

# ── Helpers ─────────────────────────────────────────────────

def lex(source):
    """Tokenise source, return (non-EOF tokens, errors)."""
    tokens, errors = tokenise(source)
    non_eof = [t for t in tokens if t.type != TokenType.EOF]
    return non_eof, errors

def types_of(tokens):
    """Extract just the token types from a list of tokens."""
    return [t.type for t in tokens]

def values_of(tokens):
    """Extract just the token values from a list of tokens."""
    return [t.value for t in tokens]

def first_type(source):
    """Get the type of the first token."""
    tokens, _ = lex(source)
    return tokens[0].type if tokens else None

def first_value(source):
    """Get the value of the first token."""
    tokens, _ = lex(source)
    return tokens[0].value if tokens else None

def has_errors(source):
    """True if lexing produced any errors."""
    _, errors = lex(source)
    return len(errors) > 0

def no_errors(source):
    """True if lexing produced no errors."""
    return not has_errors(source)


# ════════════════════════════════════════════════════════════
section("Keywords — entity, data, kind, when, has, if, match, loop")
# ════════════════════════════════════════════════════════════
# Keywords are reserved words with special meaning.
# They must be recognised correctly — not as identifiers.

def t_entity():    assert first_type("entity")  == TokenType.ENTITY
def t_data():      assert first_type("data")    == TokenType.DATA
def t_kind():      assert first_type("kind")    == TokenType.KIND
def t_alias():     assert first_type("alias")   == TokenType.ALIAS
def t_when():      assert first_type("when")    == TokenType.WHEN
def t_has():       assert first_type("has")     == TokenType.HAS
def t_if():        assert first_type("if")      == TokenType.IF
def t_else():      assert first_type("else")    == TokenType.ELSE
def t_match():     assert first_type("match")   == TokenType.MATCH
def t_loop():      assert first_type("loop")    == TokenType.LOOP
def t_stop():      assert first_type("stop")    == TokenType.STOP
def t_skip():      assert first_type("skip")    == TokenType.SKIP
def t_async():     assert first_type("async")   == TokenType.ASYNC
def t_await():     assert first_type("await")   == TokenType.AWAIT
def t_succeed():   assert first_type("succeed") == TokenType.SUCCEED
def t_fail():      assert first_type("fail")    == TokenType.FAIL
def t_result():    assert first_type("result")  == TokenType.RESULT
def t_assert():    assert first_type("assert")  == TokenType.ASSERT
def t_and():       assert first_type("and")     == TokenType.AND
def t_or():        assert first_type("or")      == TokenType.OR
def t_not():       assert first_type("not")     == TokenType.NOT
def t_is():        assert first_type("is")      == TokenType.IS
def t_exists():    assert first_type("exists")  == TokenType.EXISTS
def t_contains():  assert first_type("contains")== TokenType.CONTAINS
def t_import():    assert first_type("import")  == TokenType.IMPORT
def t_extern():    assert first_type("extern")  == TokenType.EXTERN
def t_unsafe():    assert first_type("unsafe")  == TokenType.UNSAFE
def t_sandbox():   assert first_type("sandbox") == TokenType.SANDBOX
def t_test():      assert first_type("test")    == TokenType.TEST
def t_mock():      assert first_type("mock")    == TokenType.MOCK
def t_where():     assert first_type("where")   == TokenType.WHERE

test("entity keyword",   t_entity)
test("data keyword",     t_data)
test("kind keyword",     t_kind)
test("alias keyword",    t_alias)
test("when keyword",     t_when)
test("has keyword",      t_has)
test("if keyword",       t_if)
test("else keyword",     t_else)
test("match keyword",    t_match)
test("loop keyword",     t_loop)
test("stop keyword",     t_stop)
test("skip keyword",     t_skip)
test("async keyword",    t_async)
test("await keyword",    t_await)
test("succeed keyword",  t_succeed)
test("fail keyword",     t_fail)
test("result keyword",   t_result)
test("assert keyword",   t_assert)
test("and keyword",      t_and)
test("or keyword",       t_or)
test("not keyword",      t_not)
test("is keyword",       t_is)
test("exists keyword",   t_exists)
test("contains keyword", t_contains)
test("import keyword",   t_import)
test("extern keyword",   t_extern)
test("unsafe keyword",   t_unsafe)
test("sandbox keyword",  t_sandbox)
test("test keyword",     t_test)
test("mock keyword",     t_mock)
test("where keyword",    t_where)


# ════════════════════════════════════════════════════════════
section("Literals — integers, floats, strings, booleans, nothing")
# ════════════════════════════════════════════════════════════
# Literal values written directly in source code.

def t_int_simple():
    assert first_type("42") == TokenType.INT
    assert first_value("42") == "42"

def t_int_zero():
    assert first_type("0") == TokenType.INT

def t_int_large():
    assert first_type("1000000") == TokenType.INT
    assert first_value("1000000") == "1000000"

def t_int_underscores():
    # 1_000_000 is valid Skev (underscores for readability)
    tokens, _ = lex("1_000_000")
    assert tokens[0].type == TokenType.INT
    assert "1_000_000" in tokens[0].value

def t_float_simple():
    assert first_type("3.14") == TokenType.FLOAT
    assert first_value("3.14") == "3.14"

def t_float_zero():
    assert first_type("0.0") == TokenType.FLOAT

def t_float_whole():
    assert first_type("2.0") == TokenType.FLOAT

def t_string_simple():
    tokens, errors = lex('"hello"')
    assert len(errors) == 0
    assert tokens[0].type == TokenType.STRING
    assert "hello" in tokens[0].value

def t_string_empty():
    tokens, errors = lex('""')
    assert len(errors) == 0
    assert tokens[0].type == TokenType.STRING

def t_string_with_spaces():
    tokens, errors = lex('"hello world"')
    assert len(errors) == 0
    assert tokens[0].type == TokenType.STRING

def t_string_with_interpolation():
    # {expression} inside strings — spec Chapter 2
    tokens, errors = lex('"Hello {name}!"')
    assert len(errors) == 0
    assert tokens[0].type == TokenType.STRING

def t_true_literal():
    assert first_type("true") == TokenType.TRUE

def t_false_literal():
    assert first_type("false") == TokenType.FALSE

def t_nothing_literal():
    assert first_type("nothing") == TokenType.NOTHING

test("integer: simple",      t_int_simple)
test("integer: zero",        t_int_zero)
test("integer: large",       t_int_large)
test("integer: underscores", t_int_underscores)
test("float: simple",        t_float_simple)
test("float: zero",          t_float_zero)
test("float: whole",         t_float_whole)
test("string: simple",       t_string_simple)
test("string: empty",        t_string_empty)
test("string: with spaces",  t_string_with_spaces)
test("string: interpolation",t_string_with_interpolation)
test("true literal",         t_true_literal)
test("false literal",        t_false_literal)
test("nothing literal",      t_nothing_literal)


# ════════════════════════════════════════════════════════════
section("Identifiers and Game-Native Types")
# ════════════════════════════════════════════════════════════
# Identifiers: variable names, function names, type names.
# Game-native: any identifier ending with ! (Vector3!, Color!)

def t_ident_snake_case():
    # snake_case identifiers (properties, functions)
    tokens, _ = lex("health_points")
    assert tokens[0].type == TokenType.IDENT
    assert tokens[0].value == "health_points"

def t_ident_pascal_case():
    # PascalCase identifiers (entity names, type names)
    tokens, _ = lex("DragonBoss")
    assert tokens[0].type == TokenType.IDENT
    assert tokens[0].value == "DragonBoss"

def t_ident_single_letter():
    tokens, _ = lex("x")
    assert tokens[0].type == TokenType.IDENT

def t_ident_with_numbers():
    tokens, _ = lex("player2")
    assert tokens[0].type == TokenType.IDENT

def t_ident_not_keyword():
    # 'entity_count' is NOT a keyword — it starts with 'entity' but isn't
    tokens, _ = lex("entity_count")
    assert tokens[0].type == TokenType.IDENT
    assert tokens[0].value == "entity_count"

def t_game_native_vector3():
    # Vector3! — the ! makes it game-native
    tokens, _ = lex("Vector3!")
    assert tokens[0].type == TokenType.GAME_NATIVE
    assert tokens[0].value == "Vector3!"

def t_game_native_color():
    tokens, _ = lex("Color!")
    assert tokens[0].type == TokenType.GAME_NATIVE
    assert tokens[0].value == "Color!"

def t_game_native_transform():
    tokens, _ = lex("Transform!")
    assert tokens[0].type == TokenType.GAME_NATIVE

def t_game_native_custom():
    # Any identifier + ! is a game-native type
    tokens, _ = lex("MyGameType!")
    assert tokens[0].type == TokenType.GAME_NATIVE
    assert tokens[0].value == "MyGameType!"

test("identifier: snake_case",       t_ident_snake_case)
test("identifier: PascalCase",       t_ident_pascal_case)
test("identifier: single letter",    t_ident_single_letter)
test("identifier: with numbers",     t_ident_with_numbers)
test("identifier: starts like keyword but isnt", t_ident_not_keyword)
test("game-native: Vector3!",        t_game_native_vector3)
test("game-native: Color!",          t_game_native_color)
test("game-native: Transform!",      t_game_native_transform)
test("game-native: custom type",     t_game_native_custom)


# ════════════════════════════════════════════════════════════
section("Operators — >>, <<, ::, ->, =, ==, !=, <, >, <=, >=")
# ════════════════════════════════════════════════════════════
# Skev's operators. The lexer must always take the LONGEST match.
# '>>' is ONE token (BLOCK_OPEN), not two '>' tokens.

def t_block_open():
    assert first_type(">>") == TokenType.BLOCK_OPEN
    assert first_value(">>") == ">>"

def t_block_close():
    assert first_type("<<") == TokenType.BLOCK_CLOSE
    assert first_value("<<") == "<<"

def t_prop():
    assert first_type("::") == TokenType.PROP
    assert first_value("::") == "::"

def t_arrow():
    assert first_type("->") == TokenType.ARROW
    assert first_value("->") == "->"

def t_assign():
    assert first_type("=") == TokenType.ASSIGN

def t_eq_eq():
    assert first_type("==") == TokenType.EQ_EQ

def t_not_eq():
    assert first_type("!=") == TokenType.NOT_EQ

def t_lt():
    assert first_type("<") == TokenType.LT

def t_gt():
    assert first_type(">") == TokenType.GT

def t_lt_eq():
    assert first_type("<=") == TokenType.LT_EQ

def t_gt_eq():
    assert first_type(">=") == TokenType.GT_EQ

def t_plus():      assert first_type("+")  == TokenType.PLUS
def t_minus():     assert first_type("-")  == TokenType.MINUS
def t_star():      assert first_type("*")  == TokenType.STAR
def t_slash():     assert first_type("/")  == TokenType.SLASH
def t_percent():   assert first_type("%")  == TokenType.PERCENT
def t_plus_eq():   assert first_type("+=") == TokenType.PLUS_EQ
def t_minus_eq():  assert first_type("-=") == TokenType.MINUS_EQ
def t_star_eq():   assert first_type("*=") == TokenType.STAR_EQ
def t_slash_eq():  assert first_type("/=") == TokenType.SLASH_EQ
def t_lparen():    assert first_type("(")  == TokenType.LPAREN
def t_rparen():    assert first_type(")")  == TokenType.RPAREN
def t_lbracket():  assert first_type("[")  == TokenType.LBRACKET
def t_rbracket():  assert first_type("]")  == TokenType.RBRACKET
def t_comma():     assert first_type(",")  == TokenType.COMMA
def t_dot():       assert first_type(".")  == TokenType.DOT
def t_colon():     assert first_type(":")  == TokenType.COLON

def t_no_confusion_gt_vs_block_open():
    # '>' alone should be GT, not part of '>>'
    tokens, _ = lex("> x")
    assert tokens[0].type == TokenType.GT

def t_no_confusion_lt_vs_block_close():
    # '<' alone should be LT
    tokens, _ = lex("< x")
    assert tokens[0].type == TokenType.LT

def t_no_confusion_assign_vs_eq():
    # '=' alone is ASSIGN, '==' is EQ_EQ
    tokens, _ = lex("= ==")
    assert tokens[0].type == TokenType.ASSIGN
    assert tokens[1].type == TokenType.EQ_EQ

test(">> (BLOCK_OPEN)",    t_block_open)
test("<< (BLOCK_CLOSE)",   t_block_close)
test(":: (PROP)",          t_prop)
test("-> (ARROW)",         t_arrow)
test("= (ASSIGN)",         t_assign)
test("== (EQ_EQ)",         t_eq_eq)
test("!= (NOT_EQ)",        t_not_eq)
test("< (LT)",             t_lt)
test("> (GT)",             t_gt)
test("<= (LT_EQ)",         t_lt_eq)
test(">= (GT_EQ)",         t_gt_eq)
test("+ (PLUS)",           t_plus)
test("- (MINUS)",          t_minus)
test("* (STAR)",           t_star)
test("/ (SLASH)",          t_slash)
test("% (PERCENT)",        t_percent)
test("+= (PLUS_EQ)",       t_plus_eq)
test("-= (MINUS_EQ)",      t_minus_eq)
test("*= (STAR_EQ)",       t_star_eq)
test("/= (SLASH_EQ)",      t_slash_eq)
test("( (LPAREN)",         t_lparen)
test(") (RPAREN)",         t_rparen)
test("[ (LBRACKET)",       t_lbracket)
test("] (RBRACKET)",       t_rbracket)
test(", (COMMA)",          t_comma)
test(". (DOT)",            t_dot)
test(": (COLON)",          t_colon)
test("> vs >> distinction",t_no_confusion_gt_vs_block_open)
test("< vs << distinction",t_no_confusion_lt_vs_block_close)
test("= vs == distinction",t_no_confusion_assign_vs_eq)


# ════════════════════════════════════════════════════════════
section("Comments — #, #!, #{ }#")
# ════════════════════════════════════════════════════════════

def t_line_comment():
    tokens, errors = lex("# this is a comment")
    assert len(errors) == 0
    assert tokens[0].type == TokenType.COMMENT
    assert "this is a comment" in tokens[0].value

def t_doc_comment():
    tokens, errors = lex("#! this is documentation")
    assert len(errors) == 0
    assert tokens[0].type == TokenType.DOC_COMMENT

def t_block_comment():
    tokens, errors = lex("#{ block comment }#")
    assert len(errors) == 0
    assert tokens[0].type == TokenType.BLOCK_COMMENT

def t_block_comment_multiline():
    tokens, errors = lex("#{\nline one\nline two\n}#")
    assert len(errors) == 0
    assert tokens[0].type == TokenType.BLOCK_COMMENT

def t_comment_then_code():
    # Comment then newline then real code
    tokens, errors = lex("# comment\nhealth")
    assert len(errors) == 0
    ident = [t for t in tokens if t.type == TokenType.IDENT]
    assert len(ident) > 0
    assert ident[0].value == "health"

def t_unclosed_block_comment():
    # #{ without }# should produce an error
    _, errors = lex("#{ not closed")
    assert len(errors) > 0

def t_unclosed_string():
    # " without closing " should produce an error
    _, errors = lex('"not closed')
    assert len(errors) > 0

test("line comment #",           t_line_comment)
test("doc comment #!",           t_doc_comment)
test("block comment #{ }#",      t_block_comment)
test("block comment multiline",  t_block_comment_multiline)
test("comment then code",        t_comment_then_code)
test("unclosed block comment → error", t_unclosed_block_comment)
test("unclosed string → error",  t_unclosed_string)


# ════════════════════════════════════════════════════════════
section("Full Skev Statements — real code from the spec")
# ════════════════════════════════════════════════════════════
# Tests real Skev source code that appears in the spec.
# This is the most important section — it proves the lexer
# handles complete statements correctly.

def t_property_declaration():
    # health :: int = 100
    tokens, errors = lex("health :: int = 100")
    assert len(errors) == 0
    tt = types_of(tokens)
    assert TokenType.IDENT      in tt   # health
    assert TokenType.PROP       in tt   # ::
    assert TokenType.IDENT      in tt   # int
    assert TokenType.ASSIGN     in tt   # =
    assert TokenType.INT        in tt   # 100

def t_entity_declaration():
    # entity Player >>
    tokens, errors = lex("entity Player >>")
    assert len(errors) == 0
    tt = types_of(tokens)
    assert tt[0] == TokenType.ENTITY
    assert tt[1] == TokenType.IDENT
    assert tokens[1].value == "Player"
    assert tt[2] == TokenType.BLOCK_OPEN

def t_when_handler():
    # when update(delta)
    tokens, errors = lex("when update(delta)")
    assert len(errors) == 0
    tt = types_of(tokens)
    assert tt[0] == TokenType.WHEN
    assert tt[1] == TokenType.IDENT       # update
    assert tt[2] == TokenType.LPAREN      # (
    assert tt[3] == TokenType.IDENT       # delta
    assert tt[4] == TokenType.RPAREN      # )

def t_block_close_with_label():
    # << Player
    tokens, errors = lex("<< Player")
    assert len(errors) == 0
    assert tokens[0].type == TokenType.BLOCK_CLOSE
    assert tokens[1].type == TokenType.IDENT
    assert tokens[1].value == "Player"

def t_if_condition():
    # if health < 0 >>
    tokens, errors = lex("if health < 0 >>")
    assert len(errors) == 0
    tt = types_of(tokens)
    assert tt[0] == TokenType.IF
    assert tt[1] == TokenType.IDENT
    assert tt[2] == TokenType.LT
    assert tt[3] == TokenType.INT
    assert tt[4] == TokenType.BLOCK_OPEN

def t_function_signature():
    # take_damage(amount: int) -> nothing
    tokens, errors = lex("take_damage(amount: int) -> nothing")
    assert len(errors) == 0
    tt = types_of(tokens)
    assert tt[0] == TokenType.IDENT      # take_damage
    assert tt[1] == TokenType.LPAREN     # (
    assert tt[2] == TokenType.IDENT      # amount
    assert tt[3] == TokenType.COLON      # :
    assert tt[4] == TokenType.IDENT      # int
    assert tt[5] == TokenType.RPAREN     # )
    assert tt[6] == TokenType.ARROW      # ->
    assert tt[7] == TokenType.NOTHING    # nothing

def t_generic_type():
    # list[int]
    tokens, errors = lex("list[int]")
    assert len(errors) == 0
    tt = types_of(tokens)
    assert tt[0] == TokenType.IDENT      # list
    assert tt[1] == TokenType.LBRACKET   # [
    assert tt[2] == TokenType.IDENT      # int
    assert tt[3] == TokenType.RBRACKET   # ]

def t_result_type():
    # result[PlayerData]
    tokens, errors = lex("result[PlayerData]")
    assert len(errors) == 0
    assert tokens[0].type == TokenType.RESULT
    assert tokens[1].type == TokenType.LBRACKET

def t_has_component():
    # has Physics3D
    tokens, errors = lex("has Physics3D")
    assert len(errors) == 0
    assert tokens[0].type == TokenType.HAS
    assert tokens[1].type == TokenType.IDENT
    assert tokens[1].value == "Physics3D"

def t_game_native_in_context():
    # position :: Vector3! = Vector3!(0.0, 0.0, 0.0)
    tokens, errors = lex("position :: Vector3!")
    assert len(errors) == 0
    assert tokens[0].type == TokenType.IDENT
    assert tokens[1].type == TokenType.PROP
    assert tokens[2].type == TokenType.GAME_NATIVE
    assert tokens[2].value == "Vector3!"

def t_succeed_fail():
    # succeed value   fail ErrorType.variant
    tokens1, _ = lex("succeed 42")
    tokens2, _ = lex("fail MyError.not_found")
    assert tokens1[0].type == TokenType.SUCCEED
    assert tokens2[0].type == TokenType.FAIL

def t_import_statement():
    # import skev.math
    tokens, errors = lex("import skev.math")
    assert len(errors) == 0
    assert tokens[0].type == TokenType.IMPORT
    assert tokens[1].type == TokenType.IDENT  # skev
    assert tokens[2].type == TokenType.DOT
    assert tokens[3].type == TokenType.IDENT  # math

def t_match_arm():
    # playing -> run_game()
    tokens, errors = lex("playing -> run_game()")
    assert len(errors) == 0
    tt = types_of(tokens)
    assert tt[0] == TokenType.IDENT      # playing
    assert tt[1] == TokenType.ARROW      # ->
    assert tt[2] == TokenType.IDENT      # run_game
    assert tt[3] == TokenType.LPAREN
    assert tt[4] == TokenType.RPAREN

def t_loop_range():
    # loop i from 0 to 10 >>
    tokens, errors = lex("loop i from 0 to 10 >>")
    assert len(errors) == 0
    tt = types_of(tokens)
    assert tt[0] == TokenType.LOOP
    assert tt[1] == TokenType.IDENT      # i
    assert tt[2] == TokenType.FROM
    assert tt[3] == TokenType.INT        # 0
    assert tt[4] == TokenType.TO
    assert tt[5] == TokenType.INT        # 10
    assert tt[6] == TokenType.BLOCK_OPEN

def t_type_qualified_close():
    # << collision: Enemy
    tokens, errors = lex("<< collision: Enemy")
    assert len(errors) == 0
    assert tokens[0].type == TokenType.BLOCK_CLOSE
    assert tokens[1].type == TokenType.IDENT       # collision
    assert tokens[2].type == TokenType.COLON
    assert tokens[3].type == TokenType.IDENT       # Enemy

def t_augmented_assign():
    # health -= damage
    tokens, errors = lex("health -= damage")
    assert len(errors) == 0
    tt = types_of(tokens)
    assert tt[0] == TokenType.IDENT
    assert tt[1] == TokenType.MINUS_EQ
    assert tt[2] == TokenType.IDENT

def t_line_numbers():
    # Verify line numbers are tracked correctly
    source = "entity Player >>\n    health :: int = 100\n<< Player"
    tokens, _ = tokenise(source)
    entity_tok = next(t for t in tokens if t.type == TokenType.ENTITY)
    health_tok = next(t for t in tokens if t.value == "health")
    close_tok  = next(t for t in tokens if t.type == TokenType.BLOCK_CLOSE)
    assert entity_tok.line == 1, f"entity should be on line 1, got {entity_tok.line}"
    assert health_tok.line == 2, f"health should be on line 2, got {health_tok.line}"
    assert close_tok.line  == 3, f"<< should be on line 3, got {close_tok.line}"

test("property declaration: health :: int = 100",  t_property_declaration)
test("entity declaration: entity Player >>",        t_entity_declaration)
test("when handler: when update(delta)",            t_when_handler)
test("block close with label: << Player",           t_block_close_with_label)
test("if condition: if health < 0 >>",              t_if_condition)
test("function signature with -> nothing",          t_function_signature)
test("generic type: list[int]",                     t_generic_type)
test("result type: result[PlayerData]",             t_result_type)
test("component: has Physics3D",                    t_has_component)
test("game-native in context: position :: Vector3!",t_game_native_in_context)
test("succeed and fail keywords",                   t_succeed_fail)
test("import statement",                            t_import_statement)
test("match arm: playing -> run_game()",            t_match_arm)
test("loop range: loop i from 0 to 10 >>",          t_loop_range)
test("type-qualified close: << collision: Enemy",   t_type_qualified_close)
test("augmented assign: health -= damage",          t_augmented_assign)
test("line numbers tracked correctly",              t_line_numbers)


# ════════════════════════════════════════════════════════════
section("Complete Entity — full real Skev source")
# ════════════════════════════════════════════════════════════
# The ultimate test: a complete entity from the spec.
# This proves the lexer handles real code end-to-end.

FULL_ENTITY = """entity Player >>
    health    :: int   = 100
    max_health :: int  = 100
    move_speed :: float = 5.0
    position  :: Vector3! = Vector3!(0.0, 0.0, 0.0)

    has Physics3D
    has AudioSource

    when update(delta)
        position += Vector3!(move_speed * delta, 0.0, 0.0)
    << update

    when collision(other: Enemy)
        health -= other.damage
        if health <= 0 >>
            scene.destroy(self)
        << health <= 0
    << collision: Enemy

<< Player"""

def t_full_entity_no_errors():
    tokens, errors = tokenise(FULL_ENTITY)
    assert len(errors) == 0, f"Unexpected errors: {errors}"

def t_full_entity_has_entity_keyword():
    tokens, _ = tokenise(FULL_ENTITY)
    assert any(t.type == TokenType.ENTITY for t in tokens)

def t_full_entity_has_when_keywords():
    tokens, _ = tokenise(FULL_ENTITY)
    when_tokens = [t for t in tokens if t.type == TokenType.WHEN]
    assert len(when_tokens) >= 2, "Expected at least 2 when handlers"

def t_full_entity_has_game_native():
    tokens, _ = tokenise(FULL_ENTITY)
    game_native = [t for t in tokens if t.type == TokenType.GAME_NATIVE]
    assert len(game_native) >= 2, "Expected Vector3! tokens"
    assert any(t.value == "Vector3!" for t in game_native)

def t_full_entity_has_has_keyword():
    tokens, _ = tokenise(FULL_ENTITY)
    has_tokens = [t for t in tokens if t.type == TokenType.HAS]
    assert len(has_tokens) == 2, "Expected 2 has statements"

def t_full_entity_token_count():
    tokens, _ = tokenise(FULL_ENTITY)
    # Should have a substantial number of tokens
    non_eof = [t for t in tokens if t.type != TokenType.EOF]
    assert len(non_eof) > 30, f"Expected >30 tokens, got {len(non_eof)}"

test("full entity: no lex errors",           t_full_entity_no_errors)
test("full entity: entity keyword present",  t_full_entity_has_entity_keyword)
test("full entity: when keywords present",   t_full_entity_has_when_keywords)
test("full entity: Vector3! tokens present", t_full_entity_has_game_native)
test("full entity: has keywords present",    t_full_entity_has_has_keyword)
test("full entity: token count > 30",        t_full_entity_token_count)


# ════════════════════════════════════════════════════════════
section("Error Cases — tabs, bad characters, unclosed")
# ════════════════════════════════════════════════════════════
# The spec is strict about some things. These tests verify
# the lexer catches them.

def t_tab_produces_error():
    # Spec: "Indentation: 4 spaces exactly — tabs illegal"
    _, errors = lex("\thealth :: int = 100")
    assert len(errors) > 0, "Tab should produce a lex error"

def t_valid_code_no_errors():
    # Simple valid Skev — no errors
    _, errors = lex("health :: int = 100")
    assert len(errors) == 0

def t_numbers_no_errors():
    _, errors = lex("42 3.14 0 1_000_000")
    assert len(errors) == 0

def t_operators_no_errors():
    _, errors = lex(">> << :: -> = == != < > <= >=")
    assert len(errors) == 0

def t_keywords_no_errors():
    _, errors = lex("entity data kind when has if match loop")
    assert len(errors) == 0

test("tab character → lex error",    t_tab_produces_error)
test("valid code → no errors",       t_valid_code_no_errors)
test("numbers → no errors",          t_numbers_no_errors)
test("operators → no errors",        t_operators_no_errors)
test("keywords → no errors",         t_keywords_no_errors)


# ════════════════════════════════════════════════════════════
section("Negative Numbers and Edge Cases")
# ════════════════════════════════════════════════════════════

def t_negative_int():
    tokens, errors = lex("-42")
    assert len(errors) == 0
    num_tok = [t for t in tokens if t.type == TokenType.INT]
    assert len(num_tok) > 0
    assert "-42" in num_tok[0].value

def t_negative_float():
    tokens, errors = lex("-3.14")
    assert len(errors) == 0
    float_tok = [t for t in tokens if t.type == TokenType.FLOAT]
    assert len(float_tok) > 0

def t_empty_source():
    tokens, errors = tokenise("")
    assert len(errors) == 0
    assert tokens[-1].type == TokenType.EOF

def t_only_comment():
    tokens, errors = tokenise("# just a comment")
    assert len(errors) == 0
    assert any(t.type == TokenType.COMMENT for t in tokens)

def t_only_whitespace():
    tokens, errors = tokenise("   ")
    assert len(errors) == 0

test("negative integer: -42",  t_negative_int)
test("negative float: -3.14",  t_negative_float)
test("empty source",           t_empty_source)
test("only a comment",         t_only_comment)
test("only whitespace",        t_only_whitespace)


# ════════════════════════════════════════════════════════════
print()
success = report()
sys.exit(0 if success else 1)
