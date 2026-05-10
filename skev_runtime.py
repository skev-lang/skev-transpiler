"""
╔══════════════════════════════════════════════════════════════╗
║           SKEV LANGUAGE — PYTHON RUNTIME LIBRARY            ║
║                                                              ║
║  Copyright © 2026 AJ. All Rights Reserved.                   ║
║  skev.dev | skev.org                                         ║
╚══════════════════════════════════════════════════════════════╝

WHAT IS THIS FILE?
──────────────────
This file implements the core concepts of the Skev programming
language in Python. It lets us TEST whether Skev's design is
correct BEFORE building the real compiler.

Think of it as a "simulation" of Skev running on top of Python.

WHY PYTHON FIRST?
─────────────────
The real Skev compiler will be written in Rust and produce
native machine code (via LLVM). That will take months to build.

By implementing Skev's concepts in Python first, we can:
  → Prove the language design actually works
  → Run real Skev programs right now
  → Catch any design mistakes early (cheap to fix in Python)
  → Build a test suite that the real compiler must also pass

WHAT THIS FILE COVERS:
──────────────────────
  Section 1:  Panic system        (Chapter 6 of spec)
  Section 2:  result[T]           (Chapter 6 of spec)
  Section 3:  maybe T             (Chapter 3 of spec)
  Section 4:  Game-native types   (Chapter 3 of spec)
              Vector2!, Vector3!, Color!, Transform!
  Section 5:  skev.math library   (Chapter 7 of spec)
  Section 6:  ARC simulation      (Chapter 4 of spec)
  Section 7:  Entity base class   (Chapter 3 of spec)
  Section 8:  Data value type     (Chapter 3 of spec)
  Section 9:  Generic types       (Chapter 3.5 of spec)
              Pair[A,B], Range[T]
  Section 10: Generic algorithms  (Chapter 3.5 of spec)
              identity, find_max, find_first, pipe
  Section 11: Debug utilities     (Chapter 11 of spec)

HONEST LIMITATIONS:
───────────────────
  ❌ Performance:  Python is 10-100x slower than the real compiler.
                   "Fast like C++" requires the LLVM compiler.
  ❌ ARC memory:   Python uses garbage collection, not retain/release.
                   We simulate ARC semantics, not the implementation.
  ❌ Realtime:     Python cannot enforce realtime guarantees.
  ✅ Everything else: Logic, semantics, algorithms — all validated.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import TypeVar, Generic, Optional, Callable, Any
from enum import Enum
import math as _math
import sys

T = TypeVar('T')
U = TypeVar('U')


# ══════════════════════════════════════════════════════════════
# SECTION 1 — PANIC SYSTEM (Chapter 6)
# ══════════════════════════════════════════════════════════════
#
# A PANIC is an UNRECOVERABLE error — something so wrong
# the program cannot safely continue.
#
# Examples:  array index out of bounds, divide by zero,
#            invariant that should NEVER be false... is false.
#
# Key rule from spec: "Panics cannot be caught — fix the code."
#
# This is DIFFERENT from result[T] (Section 2).
#   result[T] = EXPECTED failures, handled gracefully.
#   panic     = UNEXPECTED bugs that should never happen.
#
# Spec reference: Chapter 6, Section 6.7
# ══════════════════════════════════════════════════════════════

class SkevPanic(Exception):
    """
    Raised when a Skev panic occurs.
    The program stops immediately — there is no recovery.
    """
    def __init__(self, message: str):
        super().__init__(f"[SKEV PANIC] {message}")
        self.skev_message = message


_panic_handler: Optional[Callable[[str], None]] = None


def engine_on_panic(handler: Callable[[str], None]) -> None:
    """
    Register a handler for graceful shutdown before a panic.
    Used in shipped games to save crash reports.

    Skev syntax:
        engine.on_panic >> crash_info
            log.crash("unhandled_panic", >> ... << )
        << on_panic
    """
    global _panic_handler
    _panic_handler = handler


def skev_panic(message: str) -> None:
    """
    Fire a Skev panic. Calls the handler (if any), then raises.
    Nothing can catch this — the program terminates.
    """
    if _panic_handler:
        _panic_handler(message)
    raise SkevPanic(message)


def skev_assert(condition: bool, message: str = "Assertion failed") -> None:
    """
    Developer invariant check. Panics if condition is False.

    Use for things that should NEVER happen in correct code.

    Skev syntax:  assert health >= 0 "Health cannot be negative"
    Python usage: skev_assert(health >= 0, "Health cannot be negative")
    """
    if not condition:
        skev_panic(f"Assert failed: {message}")


# ══════════════════════════════════════════════════════════════
# SECTION 2 — result[T] (Chapter 6)
# ══════════════════════════════════════════════════════════════
#
# result[T] represents an operation that either:
#   SUCCEEDS with a value of type T
#   FAILS with an error
#
# WHY NOT EXCEPTIONS?
# ───────────────────
# With exceptions, you cannot tell from a function's signature
# whether it can fail. With result[T], the type tells you:
#
#   validate_health(v: int) -> result[int]
#   ↑ This TELLS YOU it can fail. The compiler FORCES you to handle it.
#
# THREE WAYS TO HANDLE A RESULT:
# ────────────────────────────────
#   1. match      → handle both succeed and fail explicitly
#   2. or_else    → use a fallback value on failure
#   3. propagate  → pass failure up to the caller (-> operator)
#
# Spec: "Unhandled result = compile error." (Chapter 6)
# ══════════════════════════════════════════════════════════════

class _ResultState(Enum):
    SUCCEED = "succeed"
    FAIL    = "fail"


class Result(Generic[T]):
    """
    Skev result[T] — an operation that either succeeded or failed.

    Create:  succeed(value)  or  fail(error)
    Handle:  .match(...)  or  .or_else(...)  or  .propagate()
    """

    def __init__(self, state: _ResultState, value: Any = None, error: Any = None):
        self._state   = state
        self._value   = value
        self._error   = error
        self._checked = False  # was this result ever examined?

    @staticmethod
    def succeed(value: Any = None) -> 'Result':
        """
        Create a successful result.
        Skev:   succeed value
        Python: succeed(42)
        """
        return Result(_ResultState.SUCCEED, value=value)

    @staticmethod
    def fail(error: Any) -> 'Result':
        """
        Create a failed result.
        Skev:   fail MyError.variant
        Python: fail(MyError.variant)
        """
        return Result(_ResultState.FAIL, error=error)

    @property
    def is_success(self) -> bool:
        """True if operation succeeded."""
        self._checked = True
        return self._state == _ResultState.SUCCEED

    @property
    def is_failure(self) -> bool:
        """True if operation failed."""
        self._checked = True
        return self._state == _ResultState.FAIL

    @property
    def value(self) -> T:
        """Get success value. PANICS if this result failed."""
        self._checked = True
        if self._state != _ResultState.SUCCEED:
            skev_panic(
                f"Tried to read .value of a FAILED result.\n"
                f"  Error was: {self._error}\n"
                f"  Always check .is_success before reading .value."
            )
        return self._value

    @property
    def error(self) -> Any:
        """Get error. PANICS if this result succeeded."""
        self._checked = True
        if self._state != _ResultState.FAIL:
            skev_panic(
                f"Tried to read .error of a SUCCESSFUL result.\n"
                f"  Value was: {self._value}"
            )
        return self._error

    def or_else(self, fallback: Any) -> Any:
        """
        Return value on success, fallback on failure.

        Skev:   value = operation() or_else default_value
        Python: value = result.or_else(0)

        Fallback can be a value or a callable (called only on failure).
        """
        self._checked = True
        if self._state == _ResultState.SUCCEED:
            return self._value
        return fallback() if callable(fallback) else fallback

    def match(self, on_succeed: Callable, on_fail: Callable) -> Any:
        """
        Handle BOTH outcomes explicitly — the safest pattern.

        Skev:
            match result >>
                succeed value -> handle_success(value)
                fail error    -> handle_failure(error)
            << result

        Python:
            result.match(
                on_succeed=lambda v: handle_success(v),
                on_fail=lambda e: handle_failure(e)
            )
        """
        self._checked = True
        if self._state == _ResultState.SUCCEED:
            return on_succeed(self._value)
        return on_fail(self._error)

    def propagate(self) -> T:
        """
        Unwrap success, or propagate failure to the caller.

        Skev:   value :: T = -> operation()
        Python: value = result.propagate()

        If succeeded → returns the value (continues normally).
        If failed    → raises _PropagateFailure (caller handles it).

        This is Skev's -> (arrow) propagation operator.
        "If this failed, I also fail — let the caller deal with it."
        """
        self._checked = True
        if self._state == _ResultState.FAIL:
            raise _PropagateFailure(self._error)
        return self._value

    def __repr__(self) -> str:
        if self._state == _ResultState.SUCCEED:
            return f"succeed({self._value!r})"
        return f"fail({self._error!r})"

    def __del__(self):
        """Warn if result was never examined. In real Skev: compile error."""
        if not self._checked:
            print(
                f"[SKEV WARNING] Unhandled result: {self!r}\n"
                f"  In real Skev, ignoring a result is a compile error.",
                file=sys.stderr
            )


class _PropagateFailure(Exception):
    """
    Internal: implements Skev's -> propagation operator.
    Not part of the public API — users never see this.
    """
    def __init__(self, error: Any):
        self.error = error


def succeed(value: Any = None) -> Result:
    """Skev: succeed value → Python: succeed(value)"""
    return Result.succeed(value)


def fail(error: Any) -> Result:
    """Skev: fail ErrorType → Python: fail(ErrorType)"""
    return Result.fail(error)


# ══════════════════════════════════════════════════════════════
# SECTION 3 — maybe T (Chapter 3)
# ══════════════════════════════════════════════════════════════
#
# maybe T represents a value that MIGHT exist or might NOT.
# It is Skev's safe replacement for null/None.
#
# THE NULL PROBLEM:
# ─────────────────
# In most languages, any variable can be null. Using a null
# variable crashes the program (NullPointerException, segfault).
# Tony Hoare called null his "billion-dollar mistake."
#
# HOW maybe T FIXES THIS:
# ─────────────────────────
# In Skev, values CANNOT be null by default.
# If something might not exist, declare it as maybe T.
# The compiler then FORCES you to check before using it.
#
# Skev syntax:
#   target :: maybe Enemy = scene.find_enemy(id)
#   if target exists >>
#       attack(target)    ← safe: checked first
#   << target exists
#
# Spec: Chapter 3
# ══════════════════════════════════════════════════════════════

class Maybe(Generic[T]):
    """
    Skev maybe T — a value that might or might not exist.

    Create:  some(value)  or  nothing()
    Check:   if maybe_val.exists: ...
    Unwrap:  maybe_val.value  (panics if nothing)
    Safe:    maybe_val.or_else(fallback)
    """

    def __init__(self, value: Optional[T] = None, has_value: bool = False):
        self._value     = value
        self._has_value = has_value

    @staticmethod
    def some(value: T) -> 'Maybe[T]':
        """
        Wrap a value — it EXISTS.
        Panics if you pass None (use nothing() for that).
        """
        if value is None:
            skev_panic(
                "maybe.some() called with None.\n"
                "  Use nothing() to represent 'no value'.\n"
                "  Use some(value) only when a real value exists."
            )
        return Maybe(value=value, has_value=True)

    @staticmethod
    def nothing() -> 'Maybe':
        """No value — does NOT exist. Skev: variable = nothing"""
        return Maybe(has_value=False)

    @property
    def exists(self) -> bool:
        """True if a value exists. Check this before using .value."""
        return self._has_value

    @property
    def value(self) -> T:
        """
        Get the wrapped value. PANICS if nothing.
        Always check .exists first.
        """
        if not self._has_value:
            skev_panic(
                "Tried to access the value of 'nothing'.\n"
                "  Check 'if value exists >>' before using the value."
            )
        return self._value

    def or_else(self, fallback: Any) -> Any:
        """
        Return the value if it exists, otherwise return the fallback.
        Skev:   value = maybe_val or fallback
        Python: value = maybe_val.or_else(fallback)
        """
        if self._has_value:
            return self._value
        return fallback() if callable(fallback) else fallback

    def __bool__(self) -> bool:
        """Allows: if maybe_val:  (same as .exists)"""
        return self._has_value

    def __repr__(self) -> str:
        return f"maybe({self._value!r})" if self._has_value else "nothing"


def some(value: T) -> Maybe[T]:
    """Value EXISTS. Skev: variable has a value."""
    return Maybe.some(value)


def nothing() -> Maybe:
    """Value DOES NOT EXIST. Skev: variable = nothing"""
    return Maybe.nothing()


# ══════════════════════════════════════════════════════════════
# SECTION 4 — GAME-NATIVE TYPES (Chapter 3, ! suffix)
# ══════════════════════════════════════════════════════════════
#
# These types are built into Skev for game development.
# The ! suffix marks them as game-native (visually distinct).
#
# In the real compiler: SIMD-optimised CPU instructions.
# In this Python runtime: dataclasses with full math operations.
#
# Types: Vector2!  Vector3!  Color!  Transform!
# Spec: Chapter 3, Section 3.3
# ══════════════════════════════════════════════════════════════

@dataclass
class Vector2:
    """Skev: Vector2! — 2D vector. Used for: 2D positions, sizes, directions."""
    x: float = 0.0
    y: float = 0.0

    def __add__(self, o): return Vector2(self.x+o.x, self.y+o.y)
    def __sub__(self, o): return Vector2(self.x-o.x, self.y-o.y)
    def __mul__(self, s): return Vector2(self.x*s, self.y*s)
    def __truediv__(self, s): return Vector2(self.x/s, self.y/s)

    def length(self) -> float:
        """Distance from origin: sqrt(x² + y²)"""
        return _math.sqrt(self.x**2 + self.y**2)

    def normalised(self) -> 'Vector2':
        """Unit vector (length 1.0) in same direction."""
        l = self.length()
        return Vector2(0.0, 0.0) if l == 0 else Vector2(self.x/l, self.y/l)

    def dot(self, o: 'Vector2') -> float:
        """Dot product. Useful for: angle between vectors, projections."""
        return self.x*o.x + self.y*o.y

    def distance_to(self, o: 'Vector2') -> float:
        """Distance between two points."""
        return (self - o).length()

    def __repr__(self): return f"Vector2!({self.x}, {self.y})"


@dataclass
class Vector3:
    """
    Skev: Vector3! — 3D vector.
    The most commonly used type in 3D games.
    Used for: positions, velocities, directions, normals.
    """
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __add__(self, o): return Vector3(self.x+o.x, self.y+o.y, self.z+o.z)
    def __sub__(self, o): return Vector3(self.x-o.x, self.y-o.y, self.z-o.z)
    def __mul__(self, s): return Vector3(self.x*s, self.y*s, self.z*s)
    def __truediv__(self, s): return Vector3(self.x/s, self.y/s, self.z/s)

    def __eq__(self, o: object) -> bool:
        """Equality with floating-point tolerance (1e-6).
        Needed because 0.1 + 0.2 ≠ 0.3 exactly in any computer."""
        if not isinstance(o, Vector3): return False
        return abs(self.x-o.x)<1e-6 and abs(self.y-o.y)<1e-6 and abs(self.z-o.z)<1e-6

    def length(self) -> float:
        """3D distance from origin."""
        return _math.sqrt(self.x**2 + self.y**2 + self.z**2)

    def normalised(self) -> 'Vector3':
        """Unit vector (length 1.0) in same direction."""
        l = self.length()
        return Vector3(0.0,0.0,0.0) if l==0 else Vector3(self.x/l, self.y/l, self.z/l)

    def dot(self, o: 'Vector3') -> float:
        """Dot product of two 3D vectors."""
        return self.x*o.x + self.y*o.y + self.z*o.z

    def cross(self, o: 'Vector3') -> 'Vector3':
        """Cross product — returns vector perpendicular to BOTH.
        Classic use: find surface normal, or 'up' from right+forward."""
        return Vector3(
            self.y*o.z - self.z*o.y,
            self.z*o.x - self.x*o.z,
            self.x*o.y - self.y*o.x
        )

    def distance_to(self, o: 'Vector3') -> float:
        """Distance between two 3D points."""
        return (self - o).length()

    def lerp(self, o: 'Vector3', t: float) -> 'Vector3':
        """Linear interpolation. t=0→this, t=0.5→midpoint, t=1→other.
        Classic use: smooth camera follow, gradual movement."""
        return Vector3(
            self.x+(o.x-self.x)*t,
            self.y+(o.y-self.y)*t,
            self.z+(o.z-self.z)*t
        )

    def __repr__(self): return f"Vector3!({self.x}, {self.y}, {self.z})"


@dataclass
class Color:
    """
    Skev: Color! — RGBA colour. Values 0.0-1.0 (NOT 0-255).
    This matches how GPUs work internally.
    r=red  g=green  b=blue  a=alpha(transparency)
    """
    r: float = 1.0
    g: float = 1.0
    b: float = 1.0
    a: float = 1.0

    @staticmethod
    def white() -> 'Color': return Color(1.0, 1.0, 1.0, 1.0)
    @staticmethod
    def black() -> 'Color': return Color(0.0, 0.0, 0.0, 1.0)
    @staticmethod
    def red()   -> 'Color': return Color(1.0, 0.0, 0.0, 1.0)
    @staticmethod
    def green() -> 'Color': return Color(0.0, 1.0, 0.0, 1.0)
    @staticmethod
    def blue()  -> 'Color': return Color(0.0, 0.0, 1.0, 1.0)

    @staticmethod
    def from_hex(hex_str: str) -> 'Color':
        """Create colour from hex string like '#FF0000' (red).
        Supports #RRGGBB and #RRGGBBAA formats."""
        h = hex_str.lstrip('#')
        r = int(h[0:2], 16)/255.0
        g = int(h[2:4], 16)/255.0
        b = int(h[4:6], 16)/255.0
        a = int(h[6:8], 16)/255.0 if len(h)==8 else 1.0
        return Color(r, g, b, a)

    def lerp(self, o: 'Color', t: float) -> 'Color':
        """Blend between two colours. t=0→this, t=1→other.
        Used for: fade effects, health bar colour changes."""
        return Color(
            self.r+(o.r-self.r)*t, self.g+(o.g-self.g)*t,
            self.b+(o.b-self.b)*t, self.a+(o.a-self.a)*t
        )

    def __repr__(self):
        return f"Color!({self.r:.2f}, {self.g:.2f}, {self.b:.2f}, {self.a:.2f})"


@dataclass
class Transform:
    """
    Skev: Transform! — position + rotation + scale.
    Every object in a 3D scene has a Transform.
    Describes: WHERE it is, WHICH WAY it faces, HOW BIG it is.
    """
    position: Vector3 = field(default_factory=lambda: Vector3(0.0, 0.0, 0.0))
    rotation: Vector3 = field(default_factory=lambda: Vector3(0.0, 0.0, 0.0))
    scale:    Vector3 = field(default_factory=lambda: Vector3(1.0, 1.0, 1.0))

    def __repr__(self):
        return f"Transform!(pos={self.position}, rot={self.rotation}, scale={self.scale})"


# ══════════════════════════════════════════════════════════════
# SECTION 5 — skev.math (Chapter 7)
# ══════════════════════════════════════════════════════════════
#
# The standard math library — always available, no import needed.
# Mathematical building blocks for almost every game mechanic.
#
# Key functions:
#   clamp      → keep a value within a range
#   lerp       → smoothly move between two values
#   smoothstep → smooth movement with ease-in/ease-out
#   map        → convert a value from one range to another
#   noise      → smooth random values (terrain, effects)
#
# In the real compiler: these map to LLVM intrinsics
# (often single optimised CPU instructions).
# ══════════════════════════════════════════════════════════════

class SkevMath:
    """Skev's built-in math library. Access as: math.clamp(...)"""

    PI  = _math.pi        # 3.14159...
    TAU = _math.pi * 2    # 6.28318... (full circle)
    E   = _math.e         # 2.71828...
    INF = float('inf')    # Infinity

    @staticmethod
    def clamp(value: float, min_val: float, max_val: float) -> float:
        """
        Keep value within [min_val, max_val].
        Below min → returns min. Above max → returns max.

        Classic use:  health = math.clamp(health - damage, 0, max_health)
        Skev syntax:  math.clamp(value, min, max)
        """
        return max(min_val, min(max_val, value))

    @staticmethod
    def lerp(a: float, b: float, t: float) -> float:
        """
        Linear interpolation from 'a' to 'b' by fraction 't'.
        t=0.0→a  t=0.5→midpoint  t=1.0→b

        Classic use:  cam_x = math.lerp(cam_x, target_x, 0.1)
                      (moves camera 10% closer each frame — smooth follow)
        """
        return a + (b - a) * t

    @staticmethod
    def smoothstep(edge0: float, edge1: float, x: float) -> float:
        """
        Like lerp but starts slowly, speeds up, then slows again.
        Looks more natural than constant-speed lerp.

        Classic use:  fade = math.smoothstep(0.0, 1.0, time / duration)
        """
        t = SkevMath.clamp((x - edge0) / (edge1 - edge0), 0.0, 1.0)
        return t * t * (3.0 - 2.0 * t)

    @staticmethod
    def map(value: float, in_min: float, in_max: float,
            out_min: float, out_max: float) -> float:
        """
        Map a value from one range to another.

        Example:  bar_width = math.map(health, 0, 100, 0, 200)
                  (health 0-100 → pixel width 0-200)
        """
        if in_max == in_min:
            return out_min
        t = (value - in_min) / (in_max - in_min)
        return out_min + t * (out_max - out_min)

    @staticmethod
    def noise(x: float, y: float = 0.0, z: float = 0.0) -> float:
        """
        Value noise — consistent 'random' value for any coordinate.
        Same input → same output. Nearby inputs → different outputs.

        Classic use:  height = math.noise(world_x * 0.01, world_z * 0.01)

        NOTE: Simplified hash-based noise for testing.
              Real Skev uses Perlin/Simplex noise.
        """
        import hashlib
        h = int(hashlib.md5(f"{x:.4f},{y:.4f},{z:.4f}".encode()).hexdigest()[:8], 16)
        return (h / 0xFFFFFFFF) * 2.0 - 1.0  # -1.0 to 1.0

    @staticmethod
    def abs(x: float) -> float:
        """Absolute value: abs(-5) = 5"""
        return _math.fabs(x)

    @staticmethod
    def sqrt(x: float) -> float:
        """Square root. PANICS if x is negative."""
        if x < 0:
            skev_panic(f"math.sqrt received negative number: {x}")
        return _math.sqrt(x)

    @staticmethod
    def pow(base: float, exp: float) -> float:
        """Power: math.pow(2, 10) = 1024"""
        return _math.pow(base, exp)

    @staticmethod
    def floor(x: float) -> int:
        """Round DOWN: floor(3.9) = 3"""
        return int(_math.floor(x))

    @staticmethod
    def ceil(x: float) -> int:
        """Round UP: ceil(3.1) = 4"""
        return int(_math.ceil(x))

    @staticmethod
    def round(x: float, decimals: int = 0) -> float:
        """Round to nearest."""
        return round(x, decimals)

    @staticmethod
    def sin(x: float) -> float:
        """Sine in radians. Range: -1.0 to 1.0."""
        return _math.sin(x)

    @staticmethod
    def cos(x: float) -> float:
        """Cosine in radians. Range: -1.0 to 1.0."""
        return _math.cos(x)

    @staticmethod
    def tan(x: float) -> float:
        """Tangent in radians."""
        return _math.tan(x)

    @staticmethod
    def atan2(y: float, x: float) -> float:
        """Angle of a 2D vector.
        Classic use:  angle = math.atan2(target.y - self.y, target.x - self.x)"""
        return _math.atan2(y, x)

    @staticmethod
    def max(*args) -> float:
        """Largest value: math.max(3, 7, 1) = 7"""
        return max(*args)

    @staticmethod
    def min(*args) -> float:
        """Smallest value: math.min(3, 7, 1) = 1"""
        return min(*args)

    @staticmethod
    def sign(x: float) -> float:
        """Sign: positive→1.0  negative→-1.0  zero→0.0"""
        if x > 0: return 1.0
        if x < 0: return -1.0
        return 0.0

    @staticmethod
    def deg_to_rad(d: float) -> float:
        """Degrees to radians. 180° = π radians."""
        return d * (_math.pi / 180.0)

    @staticmethod
    def rad_to_deg(r: float) -> float:
        """Radians to degrees. π radians = 180°."""
        return r * (180.0 / _math.pi)


# Global instance — Skev: math.clamp(...)  Python: math.clamp(...)
math = SkevMath()


# ══════════════════════════════════════════════════════════════
# SECTION 6 — ARC SIMULATION (Chapter 4)
# ══════════════════════════════════════════════════════════════
#
# ARC = Automatic Reference Counting — Skev's memory system.
#
# HOW ARC WORKS:
# ──────────────
# Every entity has an invisible counter (the ARC count).
#   New reference to entity   → ARC count UP   (retain)
#   Reference goes away       → ARC count DOWN  (release)
#   ARC count reaches 0       → entity DESTROYED (memory freed)
#
# WHY ARC NOT GARBAGE COLLECTION?
# ────────────────────────────────
# Garbage collection (Python, C#, Java) can pause your program
# at any moment. In games this causes "GC stutter" — visible lag.
# ARC destroys objects immediately when the last reference is gone.
# No pauses. No stutter. Fully predictable.
#
# WEAK REFERENCES:
# ─────────────────
# A weak reference observes an entity WITHOUT owning it.
# Does not increment ARC count.
# Becomes 'nothing' automatically if entity is destroyed.
# Never causes dangling pointers. Always safe to check.
#
# Spec: Chapter 4
# ══════════════════════════════════════════════════════════════

class ARCObject:
    """
    Base for all ARC-managed objects.
    In real Skev: implemented at LLVM IR level with atomic operations.
    In Python: we simulate the semantics.
    """

    def __init__(self):
        self._arc_count    = 1       # starts at 1 (creator holds it)
        self._is_destroyed = False
        self._weak_refs: list = []

    def _arc_retain(self) -> None:
        """New reference acquired. ARC count goes up."""
        if self._is_destroyed:
            skev_panic(f"Tried to use destroyed entity: {type(self).__name__}")
        self._arc_count += 1

    def _arc_release(self) -> None:
        """Reference released. ARC count goes down. Destroy if zero."""
        self._arc_count -= 1
        if self._arc_count <= 0:
            self._destroy()

    def _destroy(self) -> None:
        """ARC count reached 0 — destroy this object."""
        self._is_destroyed = True
        for w in self._weak_refs:
            w._target = None  # notify all weak references

    @property
    def arc_count(self) -> int:
        """Current reference count. Useful for debugging."""
        return self._arc_count


class WeakRef(Generic[T]):
    """
    Weak reference — observe an entity without owning it.

    Skev syntax:  enemy_ref :: weak Enemy = enemy
    Does NOT increment ARC count.
    Becomes 'nothing' automatically when entity is destroyed.

    Spec: Chapter 4 — "weak T implies maybe — auto-clears on destroy"
    """

    def __init__(self, target: T):
        self._target = target
        if isinstance(target, ARCObject):
            target._weak_refs.append(self)

    @property
    def exists(self) -> bool:
        """True if the target entity still exists."""
        return (self._target is not None and
                not getattr(self._target, '_is_destroyed', False))

    @property
    def value(self) -> Maybe:
        """
        Get target as maybe value.
        Exists → some(target). Destroyed → nothing().
        Spec: "weak T implies maybe"
        """
        return Maybe.some(self._target) if self.exists else Maybe.nothing()


# ══════════════════════════════════════════════════════════════
# SECTION 7 — ENTITY BASE CLASS (Chapter 3)
# ══════════════════════════════════════════════════════════════
#
# An entity is Skev's main building block for game objects.
# Player, enemy, bullet, camera — all entities.
#
# Entities are REFERENCE TYPES: passing an entity passes a
# reference to the SAME object (not a copy).
#
# Entities can have COMPONENTS: has Physics, has AudioSource
# Entities respond to EVENTS:   when update(delta) → ...
#
# Spec: Chapter 3 — "entity = reference type (heap/ARC)"
# ══════════════════════════════════════════════════════════════

class Entity(ARCObject):
    """
    Base class for all Skev entities.
    Extend this to create entities:
        class Player(Entity):
            def __init__(self):
                super().__init__()
                self.health = 100
    """

    def __init__(self):
        super().__init__()
        self._components: dict = {}

    def attach(self, component: Any) -> None:
        """Attach a component. Skev: has ComponentName"""
        self._components[type(component).__name__] = component

    def has_component(self, t: type) -> bool:
        """Check if component is attached."""
        return t.__name__ in self._components

    def get_component(self, t: type) -> Maybe:
        """Get component as maybe (nothing if not attached)."""
        name = t.__name__
        return Maybe.some(self._components[name]) if name in self._components else Maybe.nothing()

    def fire_event(self, event_name: str, *args, **kwargs) -> None:
        """Fire an event. Calls on_update(), on_collision() etc."""
        handler = f"on_{event_name}"
        if hasattr(self, handler):
            getattr(self, handler)(*args, **kwargs)

    def __repr__(self):
        status = "destroyed" if self._is_destroyed else f"arc={self._arc_count}"
        return f"entity:{type(self).__name__}({status})"


# ══════════════════════════════════════════════════════════════
# SECTION 8 — DATA VALUE TYPE (Chapter 3)
# ══════════════════════════════════════════════════════════════
#
# data types are VALUE TYPES — copied on assignment.
# Changes to a copy don't affect the original.
#
# This is DIFFERENT from entities (reference types):
#   data:   copy semantics — independent after assignment
#   entity: reference semantics — shared after assignment
#
# Spec: Chapter 3 — "data = value type (stack/copy)"
# ══════════════════════════════════════════════════════════════

class SkevData:
    """Base class for Skev data types (value semantics via copy())."""

    def copy(self) -> 'SkevData':
        """
        Create a deep copy — fully independent from the original.
        In real Skev, data types are copied automatically on assignment.
        """
        import copy
        return copy.deepcopy(self)


# ══════════════════════════════════════════════════════════════
# SECTION 9 — GENERIC DATA TYPES (Chapter 3.5)
# ══════════════════════════════════════════════════════════════
#
# Generics let you write code that works with ANY type
# while remaining fully type-safe.
#
# WITHOUT GENERICS: write IntPair, FloatPair, StringPair — tedious.
# WITH GENERICS:    write Pair[A, B] once — works for any types.
#
# The [T] syntax is consistent throughout Skev:
#   list[T]  result[T]  map[K,V]  channel[T]  Pair[A,B]  Range[T]
#   (all use the same [] notation — you already know it)
#
# Spec: Chapter 3.5
# ══════════════════════════════════════════════════════════════

@dataclass
class Pair(Generic[T, U]):
    """
    Skev: data Pair[A, B] >> first :: A  second :: B << Pair

    A container for exactly two values of any types.
    Examples:  Pair("Player", 100)   Pair(Vector3(...), 0.5)
    """
    first:  T = None
    second: U = None

    def __repr__(self): return f"Pair[{self.first!r}, {self.second!r}]"


@dataclass
class Range(Generic[T]):
    """
    Skev: data Range[T where T: Comparable] >> min_val :: T  max_val :: T << Range

    A range between two comparable values. Use contains() to check membership.
    The T: Comparable constraint means T must support < > == operators.
    Works with: int, float, string. NOT with: Vector3, Color (not comparable).

    Example:  Range(0.0, 100.0).contains(50.0)  → True
    """
    min_val: T = None
    max_val: T = None

    def contains(self, value: T) -> bool:
        """True if min_val <= value <= max_val (inclusive boundaries)."""
        return self.min_val <= value <= self.max_val

    def __repr__(self): return f"Range[{self.min_val!r}..{self.max_val!r}]"


# ══════════════════════════════════════════════════════════════
# SECTION 10 — GENERIC ALGORITHMS (Chapter 3.5)
# ══════════════════════════════════════════════════════════════
# Generic functions that work with any compatible type.
# ══════════════════════════════════════════════════════════════

def identity(value: T) -> T:
    """
    Returns input unchanged. Works for any type.
    Skev: identity[T](value: T) -> T
    Useful as placeholder, for testing, and in pipelines.
    """
    return value


def find_max(items: list) -> Maybe:
    """
    Find the largest value. Returns nothing() if list is empty.
    Skev: find_max[T where T: Comparable](items: list[T]) -> maybe T
    Works with int, float, string. Not Vector3 (not comparable with >).
    """
    return nothing() if not items else some(max(items))


def find_min(items: list) -> Maybe:
    """
    Find the smallest value. Returns nothing() if list is empty.
    Skev: find_min[T where T: Comparable](items: list[T]) -> maybe T
    """
    return nothing() if not items else some(min(items))


def find_first(items: list, predicate: Callable) -> Maybe:
    """
    Find first item matching a condition. Returns nothing() if none match.
    Skev: find_first[T](items: list[T], predicate: fn(T) -> bool) -> maybe T

    Example:  find_first(enemies, lambda e: e.health < 10)
              → first low-health enemy, or nothing
    """
    for item in items:
        if predicate(item):
            return some(item)
    return nothing()


def pipe(input_result: Result, transform: Callable) -> Result:
    """
    Chain result-returning operations (pipeline pattern).
    Skev: pipe[T, U](input: result[T], transform: fn(T) -> result[U]) -> result[U]

    If input SUCCEEDED → applies transform to the value.
    If input FAILED    → passes failure through WITHOUT calling transform.

    This enables clean error-handling pipelines:
        result = pipe(pipe(pipe(
            read_data(),         # step 1
            validate_format),    # step 2 (skipped if step 1 failed)
            parse_into_type))    # step 3 (skipped if step 1 or 2 failed)

    Any failure automatically skips all remaining steps.
    Spec: Chapter 3.5
    """
    if input_result.is_success:
        return transform(input_result.value)
    return input_result  # pass failure through unchanged


# ══════════════════════════════════════════════════════════════
# SECTION 11 — DEBUG UTILITIES (Chapter 11)
# ══════════════════════════════════════════════════════════════

class SkevDebug:
    """
    Skev debug logging. In release builds, debug.log is stripped
    completely — zero performance cost in shipped games.
    Spec: Chapter 11 — Observability
    """
    @staticmethod
    def log(msg: str) -> None:
        """Normal debug message. Stripped from release."""
        print(f"[skev] {msg}")

    @staticmethod
    def warn(msg: str) -> None:
        """Warning — unexpected but non-fatal."""
        print(f"[skev:warn] {msg}", file=sys.stderr)

    @staticmethod
    def error(msg: str) -> None:
        """Error — failed but program continues."""
        print(f"[skev:error] {msg}", file=sys.stderr)


# Global instance: Skev: debug.log(...)  Python: debug.log(...)
debug = SkevDebug()
