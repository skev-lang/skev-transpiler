<!--
Copyright © 2026 AJ. All Rights Reserved.
Licensed under Apache 2.0. skev.dev | skev.org
-->

# Skev Python Transpiler

The official Python transpiler for the Skev programming language.

> This is **Milestone 2** of the Skev compiler roadmap.
> It validates the language design and provides a runnable
> reference implementation. The real compiler (Rust + LLVM)
> is Milestone 3.

---

## What It Does

```
.skev source code
      ↓  skev_lexer.py    → tokens
      ↓  skev_parser.py   → AST
      ↓  skev_emitter.py  → Python code
      ↓  exec()           → running program
```

Skev programs execute. The transpiler is complete and tested.

---

## Quick Start

```bash
# Clone the repo
git clone https://github.com/skev-lang/skev-transpiler.git
cd skev-transpiler

# Run all tests
python3 test_skev_runtime.py     # 104 tests
python3 test_skev_lexer.py       # 124 tests
python3 test_skev_parser.py      #  75 tests
python3 test_skev_emitter.py     #  47 tests
python3 test_skev_e2e.py         #  67 tests

# Run a Skev program
python3 -c "
from skev_emitter import emit
code, errors = emit(open('your_file.skev').read())
exec(code)
"
```

---

## Test Results

```
skev_runtime.py   104/104 ✅
skev_lexer.py     124/124 ✅
skev_parser.py     75/75  ✅
skev_emitter.py    47/47  ✅
test_skev_e2e.py   67/67  ✅
─────────────────────────────
Total             417/417 ✅
```

---

## The 8 End-to-End Programs

| Program | Tests |
|---------|-------|
| RPG Combat Engine | 10 |
| Inventory System | 7 |
| State Machine | 9 |
| Leaderboard | 8 |
| Error Handling Chain | 7 |
| Physics and Math | 8 |
| Achievement System | 7 |
| Data Pipeline | 11 |

---

## Files

```
skev_runtime.py      Language runtime (ARC, result[T], Vector3!, etc.)
skev_lexer.py        Tokeniser (.skev text → tokens)
skev_parser.py       Parser (tokens → AST)
skev_emitter.py      Emitter (AST → Python code)

test_skev_runtime.py  Runtime tests
test_skev_lexer.py    Lexer tests
test_skev_parser.py   Parser tests
test_skev_emitter.py  Emitter tests
test_skev_e2e.py      End-to-end program tests
```

---

## Compliance

The 417 tests in this transpiler become the **compiler compliance suite**
for Milestone 3. The Rust/LLVM compiler is correct when it passes all 417.

---

## Requirements

```
Python 3.11+
No external dependencies
```

---

## License

Apache License 2.0 — Copyright © 2026 AJ.

skev.dev | skev.org
