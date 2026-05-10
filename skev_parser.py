"""
Skev Language - Parser
Token Stream -> Abstract Syntax Tree (AST)
Copyright (c) 2026 AJ. All Rights Reserved. skev.dev | skev.org

WHAT IS A PARSER?
-----------------
The parser reads the token stream from the lexer and builds
an AST (Abstract Syntax Tree) - a tree that captures the
MEANING of the program, not just its characters.

Pipeline:
  Source text -> [LEXER] -> Tokens -> [PARSER] -> AST -> [EMITTER] -> Python

The lexer answers: "What are the words?"
The parser answers: "What do the words MEAN together?"

Example:
  Tokens: ENTITY IDENT:Player BLOCK_OPEN IDENT:health PROP IDENT:int ASSIGN INT:100 ...
  AST:    EntityDecl("Player") -> [PropertyDecl("health", "int", 100)]

SPEC REFERENCE: Chapter 2
  "Grammar is LL(1) compatible - no backtracking required."
  "Innermost block closes FIRST. Outermost block closes LAST."
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Any
from skev_lexer import Token, TokenType, tokenise


# =============================================================
# SECTION 1 - AST NODE DEFINITIONS
# =============================================================
# Each node type represents one meaningful construct in Skev.
# Nodes form a tree: Program -> EntityDecl -> PropertyDecl etc.

@dataclass
class ASTNode:
    """Base class for all AST nodes."""
    line: int = 0
    def node_type(self): return type(self).__name__

# --- Top-level declarations ---

@dataclass
class Program(ASTNode):
    """Root of every Skev AST. Contains all top-level declarations."""
    declarations: List[ASTNode] = field(default_factory=list)

@dataclass
class EntityDecl(ASTNode):
    """entity Name >> body << Name"""
    name: str = ""
    body: List[ASTNode] = field(default_factory=list)

@dataclass
class DataDecl(ASTNode):
    """data Name[T] >> fields << Name"""
    name: str = ""
    generic_params: List[str] = field(default_factory=list)
    body: List[ASTNode] = field(default_factory=list)

@dataclass
class KindDecl(ASTNode):
    """kind Name >> variant1  variant2 << Name"""
    name: str = ""
    variants: List[str] = field(default_factory=list)

@dataclass
class AliasDecl(ASTNode):
    """alias Name[T] = ExistingType"""
    name: str = ""
    generic_params: List[str] = field(default_factory=list)
    target: str = ""

@dataclass
class ImportDecl(ASTNode):
    """import skev.math"""
    path: str = ""

# --- Entity body members ---

@dataclass
class PropertyDecl(ASTNode):
    """
    name :: Type [= value]
    Modifiers: fixed, shared, hidden, weak
    """
    name: str = ""
    type_expr: Optional[ASTNode] = None
    value: Optional[ASTNode] = None
    modifiers: List[str] = field(default_factory=list)

@dataclass
class ComponentDecl(ASTNode):
    """has ComponentName"""
    component_name: str = ""

@dataclass
class EventHandler(ASTNode):
    """
    when event_name(params)
        body
    << event_name [: TypeName]
    """
    event_name: str = ""
    params: List[tuple] = field(default_factory=list)
    close_type: Optional[str] = None
    body: List[ASTNode] = field(default_factory=list)
    is_async: bool = False

@dataclass
class FunctionDecl(ASTNode):
    """
    [async] name(params) -> ReturnType
        body
    << name
    """
    name: str = ""
    params: List[tuple] = field(default_factory=list)
    return_type: Optional[ASTNode] = None
    body: List[ASTNode] = field(default_factory=list)
    is_async: bool = False

# --- Statements ---

@dataclass
class IfStmt(ASTNode):
    """if condition >> then_body << condition [else >> else_body << else]"""
    condition: ASTNode = None
    then_body: List[ASTNode] = field(default_factory=list)
    else_body: List[ASTNode] = field(default_factory=list)

@dataclass
class MatchArm(ASTNode):
    """One arm of a match statement."""
    pattern: ASTNode = None
    body: List[ASTNode] = field(default_factory=list)
    is_inline: bool = False

@dataclass
class MatchStmt(ASTNode):
    """match value >> arms << value"""
    value: ASTNode = None
    arms: List[MatchArm] = field(default_factory=list)

@dataclass
class LoopStmt(ASTNode):
    """
    Three forms:
      iterate: loop item in collection >> ... << item
      range:   loop i from 0 to 10 >> ... << i
      while:   loop while condition >> ... << while condition
    """
    kind: str = ""           # "iterate", "range", "while"
    var_name: Optional[str] = None
    iterable: Optional[ASTNode] = None
    from_expr: Optional[ASTNode] = None
    to_expr: Optional[ASTNode] = None
    condition: Optional[ASTNode] = None
    body: List[ASTNode] = field(default_factory=list)

@dataclass
class AssignStmt(ASTNode):
    """name = expr  or  name += expr  etc."""
    target: ASTNode = None
    value: ASTNode = None
    operator: str = "="

@dataclass
class VarDecl(ASTNode):
    """Local variable declaration: name :: Type = value"""
    name: str = ""
    type_expr: Optional[ASTNode] = None
    value: Optional[ASTNode] = None
    modifiers: List[str] = field(default_factory=list)

@dataclass
class ReturnStmt(ASTNode):
    """result value / succeed value / fail ErrorType"""
    kind: str = "result"
    value: Optional[ASTNode] = None

@dataclass
class AssertStmt(ASTNode):
    """assert condition "message" """
    condition: ASTNode = None
    message: Optional[str] = None

@dataclass
class ExprStmt(ASTNode):
    """An expression used as a statement (typically a function call)."""
    expr: ASTNode = None

# --- Expressions ---

@dataclass
class IntLiteral(ASTNode):
    value: int = 0

@dataclass
class FloatLiteral(ASTNode):
    value: float = 0.0

@dataclass
class StringLiteral(ASTNode):
    value: str = ""

@dataclass
class BoolLiteral(ASTNode):
    value: bool = False

@dataclass
class NothingLiteral(ASTNode):
    pass

@dataclass
class Identifier(ASTNode):
    name: str = ""

@dataclass
class MemberAccess(ASTNode):
    """player.health  math.clamp  etc."""
    obj: ASTNode = None
    member: str = ""

@dataclass
class CallExpr(ASTNode):
    """function(args)  obj.method(args)"""
    callee: ASTNode = None
    args: List[ASTNode] = field(default_factory=list)

@dataclass
class BinaryExpr(ASTNode):
    """left op right"""
    left: ASTNode = None
    operator: str = ""
    right: ASTNode = None

@dataclass
class UnaryExpr(ASTNode):
    """not expr   -expr"""
    operator: str = ""
    operand: ASTNode = None

@dataclass
class TypeExpr(ASTNode):
    """Type name, optionally with parameters: list[int]  map[K,V]  maybe T"""
    name: str = ""
    params: List[ASTNode] = field(default_factory=list)

@dataclass
class IndexExpr(ASTNode):
    """items[0]  lookup["key"]"""
    obj: ASTNode = None
    index: ASTNode = None

@dataclass
class PropagateExpr(ASTNode):
    """-> operation()  (the Skev error propagation operator)"""
    expr: ASTNode = None


# =============================================================
# SECTION 2 - PARSE ERROR
# =============================================================

@dataclass
class ParseError:
    message: str
    line: int
    column: int
    def __repr__(self):
        return f"ParseError at L{self.line}:C{self.column} - {self.message}"


# =============================================================
# SECTION 3 - THE PARSER
# =============================================================
#
# This is a RECURSIVE DESCENT PARSER.
# Each grammar rule becomes a Python method.
# Methods call each other for nested rules.
# LL(1): we always know which rule applies by looking at the
# current token - no backtracking needed.

# Keywords that are valid as member names after a dot
_KEYWORD_AS_MEMBER = {
    TokenType.RESULT, TokenType.MATCH, TokenType.FROM, TokenType.TO,
    TokenType.IN, TokenType.LOOP, TokenType.ASYNC,
}

# Modifiers that can appear before a property
_MODIFIERS = {TokenType.FIXED, TokenType.SHARED, TokenType.HIDDEN, TokenType.WEAK}

# Tokens that signal the end of most expressions
_STATEMENT_ENDERS = {
    TokenType.EOF, TokenType.BLOCK_CLOSE, TokenType.BLOCK_OPEN,
}


class Parser:
    """
    Converts a token stream into a Program AST.

    Usage:
        parser = Parser(tokens)
        program, errors = parser.parse()
    """

    def __init__(self, tokens: List[Token]):
        # Skip comments and newlines - they don't affect structure
        self.tokens = [t for t in tokens if t.type not in (
            TokenType.COMMENT, TokenType.DOC_COMMENT,
            TokenType.BLOCK_COMMENT, TokenType.NEWLINE,
        )]
        self.pos = 0
        self.errors: List[ParseError] = []

    # ---- Navigation -------------------------------------------------

    def _cur(self) -> Token:
        """Current token (not consumed)."""
        if self.pos >= len(self.tokens):
            return Token(TokenType.EOF, "", 0, 0)
        return self.tokens[self.pos]

    def _peek(self, offset: int = 1) -> Token:
        """Look ahead without consuming."""
        p = self.pos + offset
        if p >= len(self.tokens):
            return Token(TokenType.EOF, "", 0, 0)
        return self.tokens[p]

    def _adv(self) -> Token:
        """Consume and return current token."""
        t = self._cur()
        if self.pos < len(self.tokens):
            self.pos += 1
        return t

    def _check(self, *types) -> bool:
        return self._cur().type in types

    def _match(self, *types) -> Optional[Token]:
        if self._cur().type in types:
            return self._adv()
        return None

    def _expect(self, typ, msg="") -> Optional[Token]:
        if self._cur().type == typ:
            return self._adv()
        t = self._cur()
        self._err(msg or f"Expected {typ.name} but got {t.type.name} ({t.value!r})", t)
        return None

    def _err(self, message: str, tok=None):
        t = tok or self._cur()
        self.errors.append(ParseError(message, t.line, t.column))

    def _skip_label(self):
        """
        Skip the close label after <<.
        Strategy: parse the label as an expression and discard it.
        This stops exactly at the end of the label without consuming
        the next statement (which might also start with an identifier).

        Examples:
          << health < 0   -> parses 'health < 0', stops at next stmt
          << state        -> parses 'state', stops at next stmt
          << i            -> parses 'i', stops at next stmt
          << while alive  -> consumes 'while', parses 'alive', stops
        """
        # while loops close with << while condition
        if self._check(TokenType.WHILE):
            self._adv()
        # else blocks close with << else
        if self._check(TokenType.ELSE):
            self._adv()
            return
        # Parse the label as expression and discard
        if not self._check(*_STATEMENT_ENDERS):
            try:
                self._expr()
            except Exception:
                pass


    def parse(self) -> tuple:
        prog = Program(line=1)
        while not self._check(TokenType.EOF):
            d = self._top_level()
            if d is not None:
                prog.declarations.append(d)
        return prog, self.errors

    def _top_level(self) -> Optional[ASTNode]:
        t = self._cur()
        if t.type == TokenType.ENTITY:    return self._entity()
        if t.type == TokenType.DATA:      return self._data()
        if t.type == TokenType.KIND:      return self._kind()
        if t.type == TokenType.ALIAS:     return self._alias()
        if t.type == TokenType.IMPORT:    return self._import()
        if t.type == TokenType.ASYNC:     return self._function(is_async=True)
        if t.type == TokenType.IDENT and self._peek().type == TokenType.LPAREN:
            return self._function()
        self._err(f"Unexpected top-level token: {t.type.name} ({t.value!r})", t)
        self._adv()
        return None

    # ---- Entity -----------------------------------------------------

    def _entity(self) -> Optional[EntityDecl]:
        line = self._cur().line
        self._expect(TokenType.ENTITY)
        nt = self._expect(TokenType.IDENT, "Expected entity name")
        if not nt: return None
        name = nt.value
        self._expect(TokenType.BLOCK_OPEN, f"Expected '>>' after entity name '{name}'")
        body = []
        while not self._check(TokenType.EOF):
            if self._check(TokenType.BLOCK_CLOSE):
                self._adv()
                ct = self._cur()
                if ct.type == TokenType.IDENT and ct.value == name:
                    self._adv(); break
                else:
                    self._err(f"Expected '<< {name}' to close entity", ct); break
            n = self._entity_member()
            if n: body.append(n)
        return EntityDecl(name=name, body=body, line=line)

    def _entity_member(self) -> Optional[ASTNode]:
        t = self._cur()
        mods = []
        while self._check(*_MODIFIERS):
            mods.append(self._adv().value)
            t = self._cur()
        if t.type == TokenType.HAS:    return self._component()
        if t.type == TokenType.WHEN:   return self._event_handler()
        if t.type == TokenType.ASYNC:  return self._function(is_async=True)
        if t.type == TokenType.IDENT:
            if self._peek().type == TokenType.LPAREN:
                return self._function(modifiers=mods)
            return self._property(modifiers=mods)
        if t.type == TokenType.MAYBE:  return self._property(modifiers=mods)
        self._err(f"Unexpected token in entity body: {t.type.name} ({t.value!r})", t)
        self._adv()
        return None

    # ---- Data -------------------------------------------------------

    def _data(self) -> Optional[DataDecl]:
        line = self._cur().line
        self._expect(TokenType.DATA)
        nt = self._expect(TokenType.IDENT, "Expected data name")
        if not nt: return None
        name = nt.value
        gp = self._generic_params() if self._check(TokenType.LBRACKET) else []
        self._expect(TokenType.BLOCK_OPEN)
        body = []
        while not self._check(TokenType.EOF):
            if self._check(TokenType.BLOCK_CLOSE):
                self._adv()
                ct = self._cur()
                if ct.type == TokenType.IDENT and ct.value == name:
                    self._adv(); break
                else:
                    self._err(f"Expected '<< {name}'", ct); break
            p = self._property()
            if p: body.append(p)
        return DataDecl(name=name, generic_params=gp, body=body, line=line)

    # ---- Kind -------------------------------------------------------

    def _kind(self) -> Optional[KindDecl]:
        line = self._cur().line
        self._expect(TokenType.KIND)
        nt = self._expect(TokenType.IDENT, "Expected kind name")
        if not nt: return None
        name = nt.value
        self._expect(TokenType.BLOCK_OPEN)
        variants = []
        while not self._check(TokenType.EOF):
            if self._check(TokenType.BLOCK_CLOSE):
                self._adv()
                ct = self._cur()
                if ct.type == TokenType.IDENT and ct.value == name:
                    self._adv(); break
                else:
                    self._err(f"Expected '<< {name}'", ct); break
            if self._check(TokenType.IDENT):
                variants.append(self._adv().value)
            else:
                self._err(f"Expected variant name, got {self._cur().type.name}")
                self._adv()
        return KindDecl(name=name, variants=variants, line=line)

    # ---- Alias ------------------------------------------------------

    def _alias(self) -> Optional[AliasDecl]:
        line = self._cur().line
        self._expect(TokenType.ALIAS)
        nt = self._expect(TokenType.IDENT, "Expected alias name")
        if not nt: return None
        name = nt.value
        gp = self._generic_params() if self._check(TokenType.LBRACKET) else []
        self._expect(TokenType.ASSIGN, "Expected '='")
        parts = []
        while not self._check(*_STATEMENT_ENDERS):
            parts.append(self._adv().value)
        return AliasDecl(name=name, generic_params=gp, target=''.join(parts), line=line)

    # ---- Import -----------------------------------------------------

    def _import(self) -> Optional[ImportDecl]:
        line = self._cur().line
        self._expect(TokenType.IMPORT)
        parts = []
        if self._check(TokenType.IDENT):
            parts.append(self._adv().value)
            while self._check(TokenType.DOT):
                self._adv()
                if self._check(TokenType.IDENT):
                    parts.append(self._adv().value)
        if not parts:
            self._err("Expected import path")
            return None
        return ImportDecl(path='.'.join(parts), line=line)

    # ---- Property ---------------------------------------------------

    def _property(self, modifiers=None) -> Optional[PropertyDecl]:
        line = self._cur().line
        mods = modifiers or []
        nt = self._expect(TokenType.IDENT, "Expected property name")
        if not nt: return None
        name = nt.value
        self._expect(TokenType.PROP, f"Expected '::' after '{name}'")
        type_expr = self._type_expr()
        value = None
        if self._match(TokenType.ASSIGN):
            value = self._expr()
        return PropertyDecl(name=name, type_expr=type_expr,
                           value=value, modifiers=mods, line=line)

    # ---- Component --------------------------------------------------

    def _component(self) -> Optional[ComponentDecl]:
        line = self._cur().line
        self._expect(TokenType.HAS)
        nt = self._expect(TokenType.IDENT, "Expected component name")
        if not nt: return None
        return ComponentDecl(component_name=nt.value, line=line)

    # ---- Event handler ----------------------------------------------

    def _event_handler(self) -> Optional[EventHandler]:
        line = self._cur().line
        self._expect(TokenType.WHEN)
        nt = self._expect(TokenType.IDENT, "Expected event name")
        if not nt: return None
        event_name = nt.value
        params = self._param_list()
        body = []
        close_type = None
        while not self._check(TokenType.EOF):
            if self._check(TokenType.BLOCK_CLOSE):
                self._adv()
                ct = self._cur()
                if ct.type == TokenType.IDENT and ct.value == event_name:
                    self._adv()
                    if self._check(TokenType.COLON):
                        self._adv()
                        if self._check(TokenType.IDENT):
                            close_type = self._adv().value
                    break
                else:
                    self._err(f"Expected '<< {event_name}'", ct); break
            s = self._stmt()
            if s: body.append(s)
        return EventHandler(event_name=event_name, params=params,
                           close_type=close_type, body=body, line=line)

    # ---- Function ---------------------------------------------------

    def _function(self, modifiers=None, is_async=False) -> Optional[FunctionDecl]:
        line = self._cur().line
        if is_async and self._check(TokenType.ASYNC):
            self._adv()
        nt = self._expect(TokenType.IDENT, "Expected function name")
        if not nt: return None
        name = nt.value
        params = self._param_list()
        ret = None
        if self._match(TokenType.ARROW):
            ret = self._type_expr()
        body = []
        while not self._check(TokenType.EOF):
            if self._check(TokenType.BLOCK_CLOSE):
                self._adv()
                ct = self._cur()
                if ct.type == TokenType.IDENT and ct.value == name:
                    self._adv(); break
                else:
                    self._err(f"Expected '<< {name}'", ct); break
            s = self._stmt()
            if s: body.append(s)
        return FunctionDecl(name=name, params=params, return_type=ret,
                           body=body, is_async=is_async, line=line)

    # ---- Statements -------------------------------------------------

    def _stmt(self) -> Optional[ASTNode]:
        t = self._cur()
        if t.type == TokenType.IF:      return self._if_stmt()
        if t.type == TokenType.MATCH:   return self._match_stmt()
        if t.type == TokenType.LOOP:    return self._loop_stmt()
        if t.type in (TokenType.RESULT, TokenType.SUCCEED):
            return self._return_stmt(t.value)
        if t.type == TokenType.FAIL:    return self._fail_stmt()
        if t.type == TokenType.ASSERT:  return self._assert_stmt()
        if t.type in (TokenType.STOP, TokenType.SKIP):
            self._adv()
            return ExprStmt(expr=Identifier(name=t.value, line=t.line), line=t.line)
        if t.type in _MODIFIERS:
            return self._local_var_modified()
        if t.type in (TokenType.IDENT, TokenType.GAME_NATIVE):
            return self._ident_stmt()
        if t.type == TokenType.ARROW:
            return self._propagate_stmt()
        # Fallback: try as expression
        e = self._expr()
        if e: return ExprStmt(expr=e, line=t.line)
        self._err(f"Unexpected token: {t.type.name} ({t.value!r})", t)
        self._adv()
        return None

    def _ident_stmt(self) -> Optional[ASTNode]:
        """Identifier starting a statement: var decl, assignment, or call."""
        line = self._cur().line
        # var decl: IDENT :: ...
        if self._check(TokenType.IDENT) and self._peek().type == TokenType.PROP:
            return self._local_var()
        e = self._expr()
        if self._check(TokenType.ASSIGN):
            op = self._adv().value
            v = self._expr()
            return AssignStmt(target=e, value=v, operator=op, line=line)
        if self._check(TokenType.PLUS_EQ, TokenType.MINUS_EQ,
                      TokenType.STAR_EQ, TokenType.SLASH_EQ):
            op = self._adv().value
            v = self._expr()
            return AssignStmt(target=e, value=v, operator=op, line=line)
        return ExprStmt(expr=e, line=line)

    def _local_var(self, mods=None) -> Optional[VarDecl]:
        line = self._cur().line
        nt = self._expect(TokenType.IDENT, "Expected variable name")
        if not nt: return None
        name = nt.value
        self._expect(TokenType.PROP)
        te = self._type_expr()
        v = None
        if self._match(TokenType.ASSIGN):
            v = self._expr()
        return VarDecl(name=name, type_expr=te, value=v,
                      modifiers=mods or [], line=line)

    def _local_var_modified(self) -> Optional[VarDecl]:
        mods = []
        while self._check(*_MODIFIERS):
            mods.append(self._adv().value)
        return self._local_var(mods=mods)

    def _propagate_stmt(self) -> Optional[ASTNode]:
        line = self._cur().line
        self._adv()  # consume '->'
        e = self._expr()
        return ExprStmt(expr=PropagateExpr(expr=e, line=line), line=line)

    # ---- If ---------------------------------------------------------

    def _if_stmt(self) -> Optional[IfStmt]:
        line = self._cur().line
        self._expect(TokenType.IF)
        cond = self._expr()
        self._expect(TokenType.BLOCK_OPEN, "Expected '>>'")
        then_body = []
        while not self._check(TokenType.EOF):
            if self._check(TokenType.BLOCK_CLOSE):
                self._adv(); self._skip_label(); break
            s = self._stmt()
            if s: then_body.append(s)
        else_body = []
        if self._check(TokenType.ELSE):
            self._adv()
            self._expect(TokenType.BLOCK_OPEN, "Expected '>>'")
            while not self._check(TokenType.EOF):
                if self._check(TokenType.BLOCK_CLOSE):
                    self._adv()
                    # << else — consume the 'else' keyword as a label
                    if self._check(TokenType.ELSE):
                        self._adv()
                    else:
                        self._skip_label()
                    break
                s = self._stmt()
                if s: else_body.append(s)
        return IfStmt(condition=cond, then_body=then_body,
                     else_body=else_body, line=line)

    # ---- Match ------------------------------------------------------

    def _match_stmt(self) -> Optional[MatchStmt]:
        line = self._cur().line
        self._expect(TokenType.MATCH)
        val = self._expr()
        self._expect(TokenType.BLOCK_OPEN, "Expected '>>'")
        arms = []
        while not self._check(TokenType.EOF):
            if self._check(TokenType.BLOCK_CLOSE):
                self._adv(); self._skip_label(); break
            arm = self._match_arm()
            if arm: arms.append(arm)
        return MatchStmt(value=val, arms=arms, line=line)

    def _match_arm(self) -> Optional[MatchArm]:
        line = self._cur().line
        pat = self._expr()
        if self._check(TokenType.ARROW):
            self._adv()
            act = self._expr()
            return MatchArm(pattern=pat,
                           body=[ExprStmt(expr=act, line=line)],
                           is_inline=True, line=line)
        elif self._check(TokenType.BLOCK_OPEN):
            self._adv()
            body = []
            while not self._check(TokenType.EOF):
                if self._check(TokenType.BLOCK_CLOSE):
                    self._adv(); self._skip_label(); break
                s = self._stmt()
                if s: body.append(s)
            return MatchArm(pattern=pat, body=body, is_inline=False, line=line)
        else:
            self._err("Expected '->' or '>>' after match pattern")
            return None

    # ---- Loop -------------------------------------------------------

    def _loop_stmt(self) -> Optional[LoopStmt]:
        line = self._cur().line
        self._expect(TokenType.LOOP)
        if self._check(TokenType.WHILE):
            return self._loop_while(line)
        vt = self._expect(TokenType.IDENT, "Expected loop variable")
        if not vt: return None
        vn = vt.value
        if self._check(TokenType.IN):   return self._loop_iterate(line, vn)
        if self._check(TokenType.FROM): return self._loop_range(line, vn)
        self._err(f"Expected 'in' or 'from' after loop var '{vn}'")
        return None

    def _loop_body(self):
        body = []
        while not self._check(TokenType.EOF):
            if self._check(TokenType.BLOCK_CLOSE):
                self._adv(); self._skip_label(); break
            s = self._stmt()
            if s: body.append(s)
        return body

    def _loop_iterate(self, line, vn) -> LoopStmt:
        self._expect(TokenType.IN)
        it = self._expr()
        self._expect(TokenType.BLOCK_OPEN)
        return LoopStmt(kind="iterate", var_name=vn, iterable=it,
                       body=self._loop_body(), line=line)

    def _loop_range(self, line, vn) -> LoopStmt:
        self._expect(TokenType.FROM)
        fe = self._expr()
        self._expect(TokenType.TO)
        te = self._expr()
        self._expect(TokenType.BLOCK_OPEN)
        return LoopStmt(kind="range", var_name=vn, from_expr=fe,
                       to_expr=te, body=self._loop_body(), line=line)

    def _loop_while(self, line) -> LoopStmt:
        self._adv()  # consume 'while'
        cond = self._expr()
        self._expect(TokenType.BLOCK_OPEN)
        return LoopStmt(kind="while", condition=cond,
                       body=self._loop_body(), line=line)

    # ---- Return / fail / assert -------------------------------------

    def _return_stmt(self, kind="result") -> ReturnStmt:
        line = self._cur().line
        self._adv()
        v = None
        if not self._check(*_STATEMENT_ENDERS):
            v = self._expr()
        return ReturnStmt(kind=kind, value=v, line=line)

    def _fail_stmt(self) -> ReturnStmt:
        line = self._cur().line
        self._adv()
        ev = self._expr()
        # Skip optional 'with key: value' context
        if self._check(TokenType.WITH):
            self._adv()
            while not self._check(*_STATEMENT_ENDERS) and not self._check(TokenType.EOF):
                self._adv()
        return ReturnStmt(kind="fail", value=ev, line=line)

    def _assert_stmt(self) -> AssertStmt:
        line = self._cur().line
        self._adv()
        cond = self._expr()
        msg = None
        if self._check(TokenType.STRING):
            raw = self._adv().value.strip('"')
            msg = raw
        return AssertStmt(condition=cond, message=msg, line=line)

    # ---- Expressions ------------------------------------------------
    # Operator precedence (lowest to highest):
    #   or -> and -> not -> comparison -> + - -> * / % -> unary -> postfix -> primary

    def _expr(self): return self._or()

    def _or(self):
        L = self._and()
        while self._check(TokenType.OR):
            op = self._adv().value
            R = self._and()
            L = BinaryExpr(left=L, operator=op, right=R, line=L.line if L else 0)
        return L

    def _and(self):
        L = self._not()
        while self._check(TokenType.AND):
            op = self._adv().value
            R = self._not()
            L = BinaryExpr(left=L, operator=op, right=R, line=L.line if L else 0)
        return L

    def _not(self):
        if self._check(TokenType.NOT):
            line = self._cur().line
            op = self._adv().value
            return UnaryExpr(operator=op, operand=self._not(), line=line)
        return self._comparison()

    def _comparison(self):
        L = self._addition()
        cmp_types = (TokenType.EQ_EQ, TokenType.NOT_EQ, TokenType.LT,
                     TokenType.GT, TokenType.LT_EQ, TokenType.GT_EQ,
                     TokenType.IS, TokenType.CONTAINS)
        while self._check(*cmp_types):
            op = self._adv().value
            R = self._addition()
            L = BinaryExpr(left=L, operator=op, right=R, line=L.line if L else 0)
        return L

    def _addition(self):
        L = self._multiplication()
        while self._check(TokenType.PLUS, TokenType.MINUS):
            op = self._adv().value
            R = self._multiplication()
            L = BinaryExpr(left=L, operator=op, right=R, line=L.line if L else 0)
        return L

    def _multiplication(self):
        L = self._unary()
        while self._check(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op = self._adv().value
            R = self._unary()
            L = BinaryExpr(left=L, operator=op, right=R, line=L.line if L else 0)
        return L

    def _unary(self):
        if self._check(TokenType.MINUS):
            line = self._cur().line
            op = self._adv().value
            return UnaryExpr(operator=op, operand=self._unary(), line=line)
        return self._postfix()

    def _postfix(self):
        """Member access, calls, index - chain left to right."""
        e = self._primary()
        while True:
            if self._check(TokenType.DOT):
                line = self._cur().line
                self._adv()
                mt = self._cur()
                if mt.type == TokenType.IDENT or mt.type in _KEYWORD_AS_MEMBER:
                    m = self._adv().value
                    e = MemberAccess(obj=e, member=m, line=line)
                else:
                    self._err(f"Expected member name after '.'", mt); break
            elif self._check(TokenType.LPAREN):
                line = self._cur().line
                args = self._arg_list()
                e = CallExpr(callee=e, args=args, line=line)
            elif self._check(TokenType.LBRACKET):
                line = self._cur().line
                self._adv()
                idx = self._expr()
                self._expect(TokenType.RBRACKET, "Expected ']'")
                e = IndexExpr(obj=e, index=idx, line=line)
            else:
                break
        return e

    def _primary(self):
        t = self._cur()
        line = t.line

        if t.type == TokenType.INT:
            self._adv()
            return IntLiteral(value=int(t.value.replace('_', '')), line=line)

        if t.type == TokenType.FLOAT:
            self._adv()
            return FloatLiteral(value=float(t.value), line=line)

        if t.type == TokenType.STRING:
            self._adv()
            raw = t.value
            if raw.startswith('"') and raw.endswith('"'):
                raw = raw[1:-1]
            return StringLiteral(value=raw, line=line)

        if t.type == TokenType.TRUE:
            self._adv(); return BoolLiteral(value=True, line=line)

        if t.type == TokenType.FALSE:
            self._adv(); return BoolLiteral(value=False, line=line)

        if t.type == TokenType.NOTHING:
            self._adv(); return NothingLiteral(line=line)

        if t.type in (TokenType.IDENT, TokenType.GAME_NATIVE):
            self._adv(); return Identifier(name=t.value, line=line)

        if t.type == TokenType.LPAREN:
            self._adv()
            e = self._expr()
            self._expect(TokenType.RPAREN, "Expected ')'")
            return e

        if t.type == TokenType.ARROW:
            self._adv()
            return PropagateExpr(expr=self._expr(), line=line)

        if t.type == TokenType.AWAIT:
            self._adv()
            return CallExpr(callee=Identifier(name="await", line=line),
                           args=[self._expr()], line=line)

        # Keywords that can appear in expression position
        if t.type in (TokenType.MAYBE, TokenType.RESULT,
                     TokenType.SUCCEED, TokenType.FAIL, TokenType.NOTHING):
            self._adv(); return Identifier(name=t.value, line=line)

        self._err(f"Expected expression, got {t.type.name} ({t.value!r})", t)
        self._adv()
        return NothingLiteral(line=line)

    # ---- Type expressions ------------------------------------------

    def _type_expr(self) -> Optional[TypeExpr]:
        line = self._cur().line

        if self._check(TokenType.MAYBE):
            self._adv()
            inner = self._type_expr()
            return TypeExpr(name="maybe", params=[inner], line=line)

        if self._check(TokenType.WEAK):
            self._adv()
            inner = self._type_expr()
            return TypeExpr(name="weak", params=[inner], line=line)

        if self._check(TokenType.GAME_NATIVE):
            t = self._adv()
            return TypeExpr(name=t.value, params=[], line=line)

        t = self._cur()
        name = self._adv().value
        params = []
        if self._check(TokenType.LBRACKET):
            self._adv()
            if not self._check(TokenType.RBRACKET):
                params.append(self._type_expr())
                while self._check(TokenType.COMMA):
                    self._adv()
                    params.append(self._type_expr())
            self._expect(TokenType.RBRACKET, "Expected ']'")
        return TypeExpr(name=name, params=params, line=line)

    # ---- Helpers ---------------------------------------------------

    def _param_list(self):
        """Parse (name: Type, name: Type) - returns list of (name, type, default)."""
        params = []
        if not self._check(TokenType.LPAREN): return params
        self._adv()
        if not self._check(TokenType.RPAREN):
            p = self._one_param()
            if p: params.append(p)
            while self._check(TokenType.COMMA):
                self._adv()
                p = self._one_param()
                if p: params.append(p)
        self._expect(TokenType.RPAREN, "Expected ')'")
        return params

    def _one_param(self):
        if not self._check(TokenType.IDENT): return None
        name = self._adv().value
        type_str = None
        default = None
        if self._check(TokenType.COLON):
            self._adv()
            te = self._type_expr()
            type_str = te.name if te else None
        if self._check(TokenType.ASSIGN):
            self._adv()
            default = self._expr()
        return (name, type_str, default)

    def _arg_list(self):
        """Parse (expr, expr) - function call arguments."""
        args = []
        self._expect(TokenType.LPAREN, "Expected '('")
        if not self._check(TokenType.RPAREN):
            args.append(self._expr())
            while self._check(TokenType.COMMA):
                self._adv()
                args.append(self._expr())
        self._expect(TokenType.RPAREN, "Expected ')'")
        return args

    def _generic_params(self):
        """Parse [T] or [A, B]."""
        params = []
        self._adv()  # consume '['
        if self._check(TokenType.IDENT):
            params.append(self._adv().value)
            while self._check(TokenType.COMMA):
                self._adv()
                if self._check(TokenType.IDENT):
                    params.append(self._adv().value)
        self._expect(TokenType.RBRACKET, "Expected ']'")
        return params


# =============================================================
# SECTION 4 - CONVENIENCE FUNCTION
# =============================================================

def parse(source: str, filename: str = "<source>") -> tuple:
    """
    Parse Skev source code into an AST.

    Args:
        source:   complete Skev source code string
        filename: for error messages (optional)

    Returns:
        (program, errors)
        program: Program AST node (the root)
        errors:  list of ParseError objects (empty if valid)
    """
    tokens, lex_errors = tokenise(source, filename)
    parser = Parser(tokens)
    program, parse_errors = parser.parse()
    return program, list(lex_errors) + parse_errors
