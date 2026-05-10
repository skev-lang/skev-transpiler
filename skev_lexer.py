"""
╔══════════════════════════════════════════════════════════════╗
║           SKEV LANGUAGE — LEXER (TOKENISER)                 ║
║                                                              ║
║  Copyright © 2026 AJ. All Rights Reserved.                   ║
║  skev.dev | skev.org                                         ║
╚══════════════════════════════════════════════════════════════╝

WHAT IS A LEXER?
────────────────
A lexer (also called a tokeniser) reads raw source code text
and breaks it into a list of TOKENS — the meaningful "words"
of the programming language.

This is the FIRST step in compiling any program:

  Source text  →  [LEXER]  →  Token stream  →  [PARSER]  →  AST

Think of it like this:
  Source text: "entity Player >> health :: int = 100"
  Tokens:      [ENTITY] [IDENT:Player] [BLOCK_OPEN] [IDENT:health]
               [PROP] [IDENT:int] [ASSIGN] [INT:100]

The parser (Step 3) then reads the token stream and figures out
the STRUCTURE of the program. But it cannot do that without
the lexer first identifying all the meaningful pieces.

WHAT THE SKEV LEXER RECOGNISES:
──────────────────────────────────
  Keywords:     entity, data, kind, when, has, if, match, loop...
  Operators:    >>, <<, ::, ->, =, +=, ==, !=, <, >, <=, >=...
  Literals:     42, 3.14, "hello", true, false
  Identifiers:  player, DragonBoss, health_points
  Game-native:  Vector3!, Color! (identifier ending with !)
  Comments:     # single line,  #{ multi-line }#,  #! doc comment
  Strings:      "text with {interpolation}"
  Whitespace:   tracked for indentation (4 spaces = 1 level)

SPEC REFERENCE:
───────────────
  Chapter 2: Syntax & Structure
  "The lexer performs a single-pass tokenisation producing
   a flat token stream consumed by a recursive descent parser.
   Grammar is LL(1) compatible — no backtracking required."
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Optional
import re


# ══════════════════════════════════════════════════════════════
# SECTION 1 — TOKEN TYPES
# ══════════════════════════════════════════════════════════════
#
# A TokenType is the CATEGORY of a token.
# Every piece of Skev source code belongs to one category.
#
# Think of it like parts of speech in English:
#   "The quick brown fox" → Article, Adjective, Adjective, Noun
#   "entity Player >>"   → Keyword, Identifier, BlockOpen
# ══════════════════════════════════════════════════════════════

class TokenType(Enum):
    """All possible token categories in Skev."""

    # ── Literals (actual values written in source code) ─────────────
    INT         = auto()   # 42, 100, -5, 1_000_000
    FLOAT       = auto()   # 3.14, 2.0, -0.5
    STRING      = auto()   # "hello world"
    TRUE        = auto()   # true
    FALSE       = auto()   # false
    NOTHING     = auto()   # nothing (the empty maybe value)

    # ── Identifiers (names the developer writes) ──────────────────────
    IDENT       = auto()   # player, health, DragonBoss (any name)
    GAME_NATIVE = auto()   # Vector3!, Color!, Transform! (name + !)

    # ── Keywords (reserved words with special meaning) ────────────────
    # Type declarations
    ENTITY      = auto()   # entity Player >>
    DATA        = auto()   # data DamageEvent >>
    KIND        = auto()   # kind GameState >>
    ALIAS       = auto()   # alias EntityID = uint32
    COMPONENT   = auto()   # component Physics >>
    IMPORT      = auto()   # import skev.math

    # Property modifiers
    FIXED       = auto()   # fixed MAX_HEALTH :: 100
    SHARED      = auto()   # shared score :: int
    HIDDEN      = auto()   # hidden internal_count :: int
    WEAK        = auto()   # weak target :: Enemy
    MAYBE       = auto()   # maybe Enemy

    # Event / component attachment
    WHEN        = auto()   # when update(delta)
    HAS         = auto()   # has Physics

    # Control flow
    IF          = auto()   # if health < 0 >>
    ELSE        = auto()   # else >>
    MATCH       = auto()   # match state >>
    LOOP        = auto()   # loop item in list >>
    STOP        = auto()   # stop  (break loop)
    SKIP        = auto()   # skip  (continue loop)
    FROM        = auto()   # loop i from 0 to 10 >>
    TO          = auto()   # loop i from 0 to 10 >>
    WHILE       = auto()   # loop while condition >>
    IN          = auto()   # loop item in list >>

    # Error handling (Chapter 6)
    RESULT      = auto()   # result value  (return from function)
    SUCCEED     = auto()   # succeed value
    FAIL        = auto()   # fail ErrorType
    OR_ELSE     = auto()   # value or_else fallback
    ASSERT      = auto()   # assert condition "message"

    # Logic operators
    AND         = auto()   # condition and other_condition
    OR          = auto()   # condition or other_condition
    NOT         = auto()   # not condition
    IS          = auto()   # value is Type
    CONTAINS    = auto()   # list contains item
    EXISTS      = auto()   # if value exists >>

    # Concurrency (Chapter 5)
    ASYNC       = auto()   # async function_name()
    AWAIT       = auto()   # await operation()
    TASK        = auto()   # task load_assets >>
    CANCEL      = auto()   # cancel load_task
    REALTIME    = auto()   # realtime motor_control >>

    # Interoperability (Chapter 8)
    EXTERN      = auto()   # extern "C" PhysicsLib >>
    UNSAFE      = auto()   # unsafe >>
    EXPORT      = auto()   # export "C" function_name
    CDATA       = auto()   # cdata PxVec3 >>
    CALLBACK    = auto()   # callback on_collision >>
    SANDBOX     = auto()   # sandbox CombatPlugin >>
    MOCK        = auto()   # mock AudioSystem >>

    # Testing (Chapter 11)
    TEST        = auto()   # test "description" >>
    BENCH       = auto()   # bench "description" >>
    BENCH_RUN   = auto()   # bench_run >>
    TEST_SETUP  = auto()   # test_setup >>

    # Type system
    WHERE       = auto()   # [T where T: Comparable]
    WITH        = auto()   # fail Error.x with key: value
    MIGRATION   = auto()   # migration PlayerData >>

    # ── Operators (symbols with special meaning) ───────────────────────
    BLOCK_OPEN  = auto()   # >>   (opens any block)
    BLOCK_CLOSE = auto()   # <<   (closes a block — followed by label)
    PROP        = auto()   # ::   (property declaration)
    ARROW       = auto()   # ->   (return type, propagation, match arm)
    ASSIGN      = auto()   # =    (assignment)
    PLUS_EQ     = auto()   # +=
    MINUS_EQ    = auto()   # -=
    STAR_EQ     = auto()   # *=
    SLASH_EQ    = auto()   # /=
    PLUS        = auto()   # +
    MINUS       = auto()   # -
    STAR        = auto()   # *
    SLASH       = auto()   # /
    PERCENT     = auto()   # %
    EQ_EQ       = auto()   # ==
    NOT_EQ      = auto()   # !=
    LT          = auto()   # <
    GT          = auto()   # >
    LT_EQ       = auto()   # <=
    GT_EQ       = auto()   # >=
    LPAREN      = auto()   # (
    RPAREN      = auto()   # )
    LBRACKET    = auto()   # [
    RBRACKET    = auto()   # ]
    COMMA       = auto()   # ,
    DOT         = auto()   # .
    COLON       = auto()   # :  (used in type-qualified event labels)
    BANG        = auto()   # !  (standalone, not part of game-native)

    # ── Comments ──────────────────────────────────────────────────────
    COMMENT     = auto()   # # this is a comment
    DOC_COMMENT = auto()   # #! this is a doc comment
    BLOCK_COMMENT = auto() # #{ this is a block comment }#

    # ── Special ───────────────────────────────────────────────────────
    NEWLINE     = auto()   # end of line (meaningful in Skev)
    INDENT      = auto()   # 4-space indentation level increase
    DEDENT      = auto()   # indentation level decrease
    EOF         = auto()   # end of file
    ERROR       = auto()   # unrecognised character (for error reporting)


# ══════════════════════════════════════════════════════════════
# SECTION 2 — THE TOKEN DATA STRUCTURE
# ══════════════════════════════════════════════════════════════
#
# A Token is one meaningful piece of source code.
# It has:
#   type:   WHAT kind of thing it is (keyword, number, operator...)
#   value:  the ACTUAL text from the source code
#   line:   which LINE it appears on (for error messages)
#   column: which COLUMN it appears on (for error messages)
#
# Example:
#   Source: "health :: int = 100"
#   Tokens:
#     Token(IDENT,  "health", line=1, col=1)
#     Token(PROP,   "::",     line=1, col=8)
#     Token(IDENT,  "int",    line=1, col=11)
#     Token(ASSIGN, "=",      line=1, col=15)
#     Token(INT,    "100",    line=1, col=17)
# ══════════════════════════════════════════════════════════════

@dataclass
class Token:
    """
    One meaningful unit of Skev source code.

    Every piece of text in a .skev file becomes a Token.
    The parser reads Tokens to understand the program structure.
    """
    type:   TokenType     # WHAT this token is
    value:  str           # the actual text from source
    line:   int = 1       # line number (starts at 1)
    column: int = 1       # column number (starts at 1)

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, L{self.line}:C{self.column})"

    def is_keyword(self) -> bool:
        """True if this token is a reserved keyword."""
        return self.type in KEYWORD_TYPES

    def is_literal(self) -> bool:
        """True if this token is a literal value (number, string, bool)."""
        return self.type in {TokenType.INT, TokenType.FLOAT,
                             TokenType.STRING, TokenType.TRUE,
                             TokenType.FALSE, TokenType.NOTHING}

    def is_operator(self) -> bool:
        """True if this token is an operator."""
        return self.type in OPERATOR_TYPES


# ══════════════════════════════════════════════════════════════
# SECTION 3 — KEYWORD MAPPING
# ══════════════════════════════════════════════════════════════
#
# Keywords are reserved words that have special meaning in Skev.
# They cannot be used as variable or function names.
#
# The lexer checks every identifier against this table.
# If it matches a keyword → TokenType.ENTITY (for example).
# If it doesn't match → TokenType.IDENT (just a name).
#
# Spec source: Chapter 11, TextMate Grammar, KEYWORDS section
# ══════════════════════════════════════════════════════════════

KEYWORDS: dict[str, TokenType] = {
    # Type declarations
    "entity":       TokenType.ENTITY,
    "data":         TokenType.DATA,
    "kind":         TokenType.KIND,
    "alias":        TokenType.ALIAS,
    "component":    TokenType.COMPONENT,
    "import":       TokenType.IMPORT,

    # Property modifiers
    "fixed":        TokenType.FIXED,
    "shared":       TokenType.SHARED,
    "hidden":       TokenType.HIDDEN,
    "weak":         TokenType.WEAK,
    "maybe":        TokenType.MAYBE,

    # Event / component
    "when":         TokenType.WHEN,
    "has":          TokenType.HAS,

    # Control flow
    "if":           TokenType.IF,
    "else":         TokenType.ELSE,
    "match":        TokenType.MATCH,
    "loop":         TokenType.LOOP,
    "stop":         TokenType.STOP,
    "skip":         TokenType.SKIP,
    "from":         TokenType.FROM,
    "to":           TokenType.TO,
    "while":        TokenType.WHILE,
    "in":           TokenType.IN,

    # Boolean / null literals
    "true":         TokenType.TRUE,
    "false":        TokenType.FALSE,
    "nothing":      TokenType.NOTHING,

    # Error handling
    "result":       TokenType.RESULT,
    "succeed":      TokenType.SUCCEED,
    "fail":         TokenType.FAIL,
    "or_else":      TokenType.OR_ELSE,
    "assert":       TokenType.ASSERT,

    # Logic
    "and":          TokenType.AND,
    "or":           TokenType.OR,
    "not":          TokenType.NOT,
    "is":           TokenType.IS,
    "contains":     TokenType.CONTAINS,
    "exists":       TokenType.EXISTS,

    # Concurrency
    "async":        TokenType.ASYNC,
    "await":        TokenType.AWAIT,
    "task":         TokenType.TASK,
    "cancel":       TokenType.CANCEL,
    "realtime":     TokenType.REALTIME,

    # Interop / safety
    "extern":       TokenType.EXTERN,
    "unsafe":       TokenType.UNSAFE,
    "export":       TokenType.EXPORT,
    "cdata":        TokenType.CDATA,
    "callback":     TokenType.CALLBACK,
    "sandbox":      TokenType.SANDBOX,
    "mock":         TokenType.MOCK,

    # Testing
    "test":         TokenType.TEST,
    "bench":        TokenType.BENCH,
    "bench_run":    TokenType.BENCH_RUN,
    "test_setup":   TokenType.TEST_SETUP,

    # Other
    "where":        TokenType.WHERE,
    "with":         TokenType.WITH,
    "migration":    TokenType.MIGRATION,
}

# Sets for quick membership testing
KEYWORD_TYPES = set(KEYWORDS.values())
OPERATOR_TYPES = {
    TokenType.BLOCK_OPEN, TokenType.BLOCK_CLOSE, TokenType.PROP,
    TokenType.ARROW, TokenType.ASSIGN, TokenType.PLUS_EQ,
    TokenType.MINUS_EQ, TokenType.STAR_EQ, TokenType.SLASH_EQ,
    TokenType.PLUS, TokenType.MINUS, TokenType.STAR, TokenType.SLASH,
    TokenType.PERCENT, TokenType.EQ_EQ, TokenType.NOT_EQ,
    TokenType.LT, TokenType.GT, TokenType.LT_EQ, TokenType.GT_EQ,
    TokenType.LPAREN, TokenType.RPAREN, TokenType.LBRACKET,
    TokenType.RBRACKET, TokenType.COMMA, TokenType.DOT, TokenType.COLON,
}


# ══════════════════════════════════════════════════════════════
# SECTION 4 — LEXER ERROR
# ══════════════════════════════════════════════════════════════

@dataclass
class LexError:
    """
    Describes a problem found during lexing.

    Skev's design principle: error messages must be clear.
    Every LexError has a line, column, and plain English message.
    """
    message: str    # plain English description of the problem
    line:    int    # which line the error is on
    column:  int    # which column the error is on

    def __repr__(self) -> str:
        return f"LexError at L{self.line}:C{self.column} — {self.message}"


# ══════════════════════════════════════════════════════════════
# SECTION 5 — THE LEXER CLASS
# ══════════════════════════════════════════════════════════════
#
# The Lexer class reads source code character by character
# and produces a list of Tokens.
#
# HOW IT WORKS — SINGLE PASS:
# ────────────────────────────
# The spec says: "single-pass tokenisation"
# This means we read each character exactly ONCE, left to right.
#
# At each position, the lexer asks:
#   "What does this character (or sequence) mean?"
#
# If it sees '#'  → start of a comment
# If it sees '"'  → start of a string literal
# If it sees '>'  → might be '>' or '>>' (block open)
# If it sees a digit → start of a number
# If it sees a letter → start of an identifier or keyword
#
# This is called a "maximal munch" lexer:
# Always take the LONGEST possible match.
# '>>' is ONE token (BLOCK_OPEN), not two '>' tokens.
# '>=' is ONE token (GT_EQ), not '>' then '='.
# ══════════════════════════════════════════════════════════════

class Lexer:
    """
    Skev lexer — converts source code text into a token stream.

    Usage:
        lexer = Lexer(source_code, filename="player.skev")
        tokens, errors = lexer.tokenise()

    Returns:
        tokens: list[Token]   — the token stream
        errors: list[LexError] — any problems found

    Spec: Chapter 2, Section 2.1
    "The lexer performs single-pass tokenisation producing
     a flat token stream."
    """

    def __init__(self, source: str, filename: str = "<source>"):
        self.source   = source      # the complete source code
        self.filename = filename    # for error messages
        self.pos      = 0           # current position in source
        self.line     = 1           # current line number
        self.column   = 1           # current column number
        self.tokens: List[Token]    = []
        self.errors: List[LexError] = []

    # ── Navigation helpers ─────────────────────────────────────────────

    def _current(self) -> str:
        """The character at the current position. '' if past end."""
        if self.pos >= len(self.source):
            return ''
        return self.source[self.pos]

    def _peek(self, offset: int = 1) -> str:
        """Look ahead by 'offset' characters without consuming. '' if past end."""
        pos = self.pos + offset
        if pos >= len(self.source):
            return ''
        return self.source[pos]

    def _advance(self) -> str:
        """
        Consume the current character and move forward.
        Updates line and column numbers automatically.
        Returns the character that was consumed.
        """
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line   += 1
            self.column  = 1
        else:
            self.column += 1
        return ch

    def _match(self, expected: str) -> bool:
        """
        Consume the current character only if it matches 'expected'.
        Returns True if it matched, False otherwise.
        Used for two-character operators like >=, ==, >>.
        """
        if self.pos < len(self.source) and self.source[self.pos] == expected:
            self._advance()
            return True
        return False

    def _add_token(self, type: TokenType, value: str,
                   line: int = None, col: int = None) -> None:
        """Add a completed token to the token list."""
        self.tokens.append(Token(
            type=type,
            value=value,
            line=line if line is not None else self.line,
            column=col if col is not None else self.column
        ))

    def _error(self, message: str) -> None:
        """Record a lex error with location information."""
        self.errors.append(LexError(message, self.line, self.column))
        # Also emit an ERROR token so parsing can continue
        self._add_token(TokenType.ERROR, self._current())

    # ── Main tokenise loop ─────────────────────────────────────────────

    def tokenise(self) -> tuple[List[Token], List[LexError]]:
        """
        Main entry point. Reads source and produces token stream.

        Returns (tokens, errors).
        errors is empty if source was valid Skev.
        """
        while self.pos < len(self.source):
            self._scan_token()

        # Always end with EOF token
        self._add_token(TokenType.EOF, "", self.line, self.column)
        return self.tokens, self.errors

    def _scan_token(self) -> None:
        """
        Scan one token starting at current position.
        Called repeatedly until source is exhausted.
        """
        start_line = self.line
        start_col  = self.column
        ch = self._advance()

        # ── Whitespace ────────────────────────────────────────────────
        if ch == ' ':
            # Spaces are significant for indentation but we handle
            # that at the line level. Inside a line, spaces are ignored.
            pass

        elif ch == '\t':
            # Spec: "Indentation: 4 spaces exactly — tabs illegal"
            self._error(
                "Tabs are not allowed in Skev. "
                "Use 4 spaces for indentation."
            )

        elif ch == '\r':
            # Windows line ending \r\n — skip the \r
            pass

        elif ch == '\n':
            # Newlines are meaningful in Skev (mark end of statements)
            self._add_token(TokenType.NEWLINE, "\\n", start_line, start_col)

        # ── Comments ──────────────────────────────────────────────────
        elif ch == '#':
            if self._current() == '!':
                # Doc comment: #! documentation text
                self._advance()  # consume '!'
                text = self._read_to_end_of_line()
                self._add_token(
                    TokenType.DOC_COMMENT,
                    '#!' + text,
                    start_line, start_col
                )
            elif self._current() == '{':
                # Block comment: #{ ... }#
                self._advance()  # consume '{'
                comment = self._read_block_comment(start_line, start_col)
                self._add_token(
                    TokenType.BLOCK_COMMENT,
                    comment,
                    start_line, start_col
                )
            else:
                # Single-line comment: # comment text
                text = self._read_to_end_of_line()
                self._add_token(
                    TokenType.COMMENT,
                    '#' + text,
                    start_line, start_col
                )

        # ── String literals ────────────────────────────────────────────
        elif ch == '"':
            # Read the string content up to closing "
            # Supports {expression} interpolation
            string_val = self._read_string(start_line, start_col)
            self._add_token(
                TokenType.STRING,
                string_val,
                start_line, start_col
            )

        # ── Numbers ────────────────────────────────────────────────────
        elif ch.isdigit():
            # Could be int (42) or float (3.14)
            num_val, num_type = self._read_number(ch, start_line, start_col)
            self._add_token(num_type, num_val, start_line, start_col)

        # ── Identifiers and Keywords ───────────────────────────────────
        elif ch.isalpha() or ch == '_':
            # Read the full identifier (letters, digits, underscores)
            name = ch + self._read_while(lambda c: c.isalnum() or c == '_')

            # Check if it ends with '!' → game-native type
            if self._current() == '!':
                self._advance()  # consume '!'
                self._add_token(
                    TokenType.GAME_NATIVE,
                    name + '!',
                    start_line, start_col
                )
            # Check if it's a reserved keyword
            elif name in KEYWORDS:
                self._add_token(KEYWORDS[name], name, start_line, start_col)
            # Otherwise it's just an identifier (variable/type name)
            else:
                self._add_token(TokenType.IDENT, name, start_line, start_col)

        # ── Two-character operators (check longest match first) ────────

        elif ch == '>':
            if self._match('>'):
                # '>>' = BLOCK_OPEN (opens a block)
                self._add_token(TokenType.BLOCK_OPEN, '>>', start_line, start_col)
            elif self._match('='):
                # '>=' = GTE
                self._add_token(TokenType.GT_EQ, '>=', start_line, start_col)
            else:
                # '>' alone = GT
                self._add_token(TokenType.GT, '>', start_line, start_col)

        elif ch == '<':
            if self._match('<'):
                # '<<' = BLOCK_CLOSE (closes a block)
                # The label that follows is captured separately by the parser
                self._add_token(TokenType.BLOCK_CLOSE, '<<', start_line, start_col)
            elif self._match('='):
                # '<=' = LTE
                self._add_token(TokenType.LT_EQ, '<=', start_line, start_col)
            else:
                # '<' alone = LT
                self._add_token(TokenType.LT, '<', start_line, start_col)

        elif ch == ':':
            if self._match(':'):
                # '::' = PROP (property declaration)
                self._add_token(TokenType.PROP, '::', start_line, start_col)
            else:
                # ':' alone = COLON (used in type-qualified labels)
                self._add_token(TokenType.COLON, ':', start_line, start_col)

        elif ch == '-':
            if self._match('>'):
                # '->' = ARROW (return type, propagation, match arm)
                self._add_token(TokenType.ARROW, '->', start_line, start_col)
            elif self._match('='):
                # '-=' = MINUS_EQ
                self._add_token(TokenType.MINUS_EQ, '-=', start_line, start_col)
            elif self._current().isdigit():
                # Negative number: -42 or -3.14
                num_val, num_type = self._read_number(
                    '-' + self._advance(), start_line, start_col
                )
                self._add_token(num_type, num_val, start_line, start_col)
            else:
                # '-' alone = MINUS
                self._add_token(TokenType.MINUS, '-', start_line, start_col)

        elif ch == '=':
            if self._match('='):
                # '==' = EQ_EQ (equality comparison)
                self._add_token(TokenType.EQ_EQ, '==', start_line, start_col)
            else:
                # '=' alone = ASSIGN
                self._add_token(TokenType.ASSIGN, '=', start_line, start_col)

        elif ch == '!':
            if self._match('='):
                # '!=' = NOT_EQ
                self._add_token(TokenType.NOT_EQ, '!=', start_line, start_col)
            else:
                # '!' alone = BANG (used in game-native type suffix)
                self._add_token(TokenType.BANG, '!', start_line, start_col)

        elif ch == '+':
            if self._match('='):
                self._add_token(TokenType.PLUS_EQ, '+=', start_line, start_col)
            else:
                self._add_token(TokenType.PLUS, '+', start_line, start_col)

        elif ch == '*':
            if self._match('='):
                self._add_token(TokenType.STAR_EQ, '*=', start_line, start_col)
            else:
                self._add_token(TokenType.STAR, '*', start_line, start_col)

        elif ch == '/':
            if self._match('='):
                self._add_token(TokenType.SLASH_EQ, '/=', start_line, start_col)
            else:
                self._add_token(TokenType.SLASH, '/', start_line, start_col)

        # ── Single-character operators ─────────────────────────────────
        elif ch == '%':
            self._add_token(TokenType.PERCENT, '%', start_line, start_col)
        elif ch == '(':
            self._add_token(TokenType.LPAREN, '(', start_line, start_col)
        elif ch == ')':
            self._add_token(TokenType.RPAREN, ')', start_line, start_col)
        elif ch == '[':
            self._add_token(TokenType.LBRACKET, '[', start_line, start_col)
        elif ch == ']':
            self._add_token(TokenType.RBRACKET, ']', start_line, start_col)
        elif ch == ',':
            self._add_token(TokenType.COMMA, ',', start_line, start_col)
        elif ch == '.':
            self._add_token(TokenType.DOT, '.', start_line, start_col)

        # ── Unrecognised character ─────────────────────────────────────
        else:
            self._error(
                f"Unexpected character: {ch!r}\n"
                f"  Skev source files must be UTF-8 text.\n"
                f"  All Skev operators and keywords use ASCII characters."
            )

    # ── Helper: read characters while condition holds ──────────────────

    def _read_while(self, condition) -> str:
        """
        Consume characters while condition(char) is True.
        Returns the consumed text.
        Used for: reading identifier names, number digits, etc.
        """
        result = []
        while self.pos < len(self.source) and condition(self._current()):
            result.append(self._advance())
        return ''.join(result)

    # ── Helper: read to end of line ────────────────────────────────────

    def _read_to_end_of_line(self) -> str:
        """
        Consume everything up to (but not including) the newline.
        Used for single-line comments: # comment text
        """
        result = []
        while self.pos < len(self.source) and self._current() != '\n':
            result.append(self._advance())
        return ''.join(result)

    # ── Helper: read block comment ─────────────────────────────────────

    def _read_block_comment(self, start_line: int, start_col: int) -> str:
        """
        Read a block comment: #{ ... }#

        Block comments can span multiple lines.
        Must be closed with }# before end of file.

        Spec: "Nesting supported safely" — nested #{ }# is allowed.
        """
        result = ['#{']
        depth = 1  # nesting depth (allows nested block comments)

        while self.pos < len(self.source):
            ch = self._advance()

            if ch == '#' and self._current() == '{':
                # Nested block comment opens
                self._advance()
                result.append('#{')
                depth += 1

            elif ch == '}' and self._current() == '#':
                # Block comment closes
                self._advance()
                result.append('}#')
                depth -= 1
                if depth == 0:
                    break  # outermost comment closed — done
            else:
                result.append(ch)

        if depth > 0:
            # Reached end of file without closing the comment
            self._error(
                f"Block comment opened at L{start_line}:C{start_col} "
                f"was never closed.\n"
                f"  Close block comments with: }}#"
            )

        return ''.join(result)

    # ── Helper: read string literal ────────────────────────────────────

    def _read_string(self, start_line: int, start_col: int) -> str:
        """
        Read a string literal: "text content"

        Supports:
          Escape sequences: \n \t \\ \"
          Interpolation:    "Hello {name}!"
          Literal brace:    "Use {{ for a literal brace"

        Spec: "String interpolation: {expression}  Literal brace: {{"
        """
        result = ['"']

        while self.pos < len(self.source):
            ch = self._advance()

            if ch == '"':
                # Closing quote — string is complete
                result.append('"')
                break

            elif ch == '\\':
                # Escape sequence
                if self.pos >= len(self.source):
                    self._error("Unterminated escape sequence at end of file.")
                    break
                esc = self._advance()
                if   esc == 'n':  result.append('\\n')
                elif esc == 't':  result.append('\\t')
                elif esc == '\\': result.append('\\\\')
                elif esc == '"':  result.append('\\"')
                elif esc == '{':  result.append('\\{')
                else:
                    self._error(
                        f"Unknown escape sequence: \\{esc}\n"
                        f"  Skev supports: \\n \\t \\\\ \\\""
                    )
                    result.append(f'\\{esc}')

            elif ch == '\n':
                # Strings cannot span multiple lines (use \n for newline)
                self._error(
                    f"String literal opened at L{start_line}:C{start_col} "
                    f"spans multiple lines.\n"
                    f"  Skev strings must be on one line.\n"
                    f"  Use \\n for a newline character inside a string."
                )
                break

            else:
                result.append(ch)

        else:
            # Reached end of file without closing the string
            self._error(
                f"String literal opened at L{start_line}:C{start_col} "
                f"was never closed.\n"
                f"  All strings must be closed with a double quote: \""
            )

        return ''.join(result)

    # ── Helper: read number literal ────────────────────────────────────

    def _read_number(self, first_char: str,
                     start_line: int, start_col: int) -> tuple[str, TokenType]:
        """
        Read a number literal: integer or float.

        Integers: 42, 100, 1_000_000 (underscores for readability)
        Floats:   3.14, 2.0, -0.5
        Negative: handled when '-' precedes a digit

        Returns (text_value, TokenType.INT or TokenType.FLOAT)
        """
        result = [first_char]
        is_float = False

        # Read digits and underscores (underscores for readability: 1_000_000)
        while self.pos < len(self.source):
            ch = self._current()
            if ch.isdigit():
                result.append(self._advance())
            elif ch == '_' and self._peek().isdigit():
                # Underscore separator (like 1_000_000) — consume but include
                result.append(self._advance())
            elif ch == '.' and self._peek().isdigit() and not is_float:
                # Decimal point → this is a float
                result.append(self._advance())  # consume '.'
                is_float = True
            else:
                break

        return ''.join(result), TokenType.FLOAT if is_float else TokenType.INT


# ══════════════════════════════════════════════════════════════
# SECTION 6 — CONVENIENCE FUNCTION
# ══════════════════════════════════════════════════════════════

def tokenise(source: str, filename: str = "<source>") -> tuple[List[Token], List[LexError]]:
    """
    Tokenise Skev source code.

    This is the main entry point for the lexer.

    Args:
        source:   the complete source code as a string
        filename: filename for error messages (optional)

    Returns:
        (tokens, errors)
        tokens: list of all tokens found
        errors: list of lex errors (empty if source is valid)

    Example:
        tokens, errors = tokenise('entity Player >> health :: int = 100\\n<< Player')
        if errors:
            for e in errors: print(e)
        else:
            for t in tokens: print(t)
    """
    lexer = Lexer(source, filename)
    return lexer.tokenise()
