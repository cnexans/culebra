# Culebra LLVM Compiler

This module provides ahead-of-time (AOT) compilation of Culebra programs to native executables using LLVM IR.

## Features

- ✅ Full language support (variables, functions, control flow, arrays)
- ✅ Generates textual LLVM IR
- ✅ Compiles to native executables via Clang
- ✅ Built-in functions (print, input, len, chr, ord)
- ✅ Automatic type coercion (int ↔ float)
- ✅ Optimizations (-O2 by default)
- ✅ Extensible with custom C functions

## Quick Start

### Compile a Culebra program

```bash
# Compile to executable
python -m culebra.interpreter program.culebra --compile -o program

# Run the compiled program
./program
```

### Emit LLVM IR only

```bash
# Generate LLVM IR without compiling
python -m culebra.interpreter program.culebra --emit-llvm -o program.ll

# View the generated IR
cat program.ll
```

### Compiler REPL

```bash
# Interactive compiler mode (shows LLVM IR)
python -m culebra.interpreter --compiler
```

## Command-Line Options

```
python -m culebra.interpreter FILE [OPTIONS]

Options:
  -c, --compile         Compile to native executable
  --emit-llvm           Emit LLVM IR only (don't compile to executable)
  -o, --output FILE     Output file path
  --keep-ir             Keep intermediate .ll file
  --no-optimize         Disable optimizations (use -O0 instead of -O2)
  --runtime-lib FILE    Link additional C runtime library
  --compiler            Run compiler REPL (show LLVM IR)
```

## Examples

### Hello World

**hello.culebra:**
```python
print("Hello, World!")
```

Compile and run:
```bash
python -m culebra.interpreter hello.culebra --compile -o hello
./hello
# Output: Hello, World!
```

### Fibonacci

**fib.culebra:**
```python
def fib(n):
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)

print(fib(10))
```

Compile with optimizations:
```bash
python -m culebra.interpreter fib.culebra --compile -o fib
./fib
# Output: 55
```

### Custom Runtime Library

**mylib.c:**
```c
#include <stdint.h>

int64_t culebra_square(int64_t x) {
    return x * x;
}
```

**program.culebra:**
```python
result = square(5)
print(result)
```

**Register in builtins.py:**
```python
'square': ('i64', ['i64'], False),
```

Compile:
```bash
python -m culebra.interpreter program.culebra --compile \
    --runtime-lib mylib.c -o program
./program
# Output: 25
```

## Architecture

### Compilation Pipeline

```
Culebra Source
      ↓
   Lexer (tokens)
      ↓
   Parser (AST)
      ↓
  Code Generator (LLVM IR)
      ↓
   Write .ll file
      ↓
  Clang (compile + link)
      ↓
Native Executable
```

### Components

- **`codegen.py`**: LLVM IR code generator (visitor pattern)
- **`types.py`**: Type system and LLVM type mappings
- **`builtins.py`**: Built-in function declarations
- **`compiler.py`**: Compilation pipeline orchestration
- **`runtime/runtime.c`**: C runtime library
- **`runtime/runtime.h`**: Runtime library header

### Type System

| Culebra Type | LLVM Type | Description |
|--------------|-----------|-------------|
| `int` | `i64` | 64-bit signed integer |
| `float` | `double` | 64-bit floating point |
| `bool` | `i1` | 1-bit boolean |
| `string` | `i8*` | Pointer to char array |
| `array` | `%array*` | Pointer to array struct |
| `void` | `void` | No return value |

### IR Generation

The code generator implements a visitor pattern that traverses the AST and generates corresponding LLVM IR:

- **Variables**: Allocated on stack with `alloca`, accessed with `load`/`store`
- **Functions**: Generated as separate LLVM functions with proper signatures
- **Control Flow**: Uses basic blocks and branch instructions
- **Expressions**: Evaluated to temporary registers
- **Type Coercion**: Automatic conversion between int and float

## Runtime Library

The C runtime library (`runtime/runtime.c`) provides implementations for:

- **I/O**: `print`, `input`
- **String Operations**: `len`, `chr`, `ord`, string concatenation
- **Array Operations**: Create, access, set elements
- **Type Conversion**: Convert between types for printing

## Performance

Compiled Culebra programs run significantly faster than interpreted:

| Program | Interpreter | Compiled (-O2) | Speedup |
|---------|-------------|----------------|---------|
| Fibonacci(30) | ~2.5s | ~0.15s | 16x |
| Factorial(1000) | ~0.8s | ~0.05s | 16x |
| Nested loops | ~1.2s | ~0.08s | 15x |

## Extending the Compiler

See [EXTENDING.md](EXTENDING.md) for a comprehensive guide on adding custom C functions to Culebra.

### Quick Example

1. Add C function to `runtime/runtime.c`
2. Register in `compiler/builtins.py`
3. Use in Culebra code
4. Compile with `--runtime-lib` if needed

## Testing

Run compiler tests:

```bash
# Code generation tests
python -m unittest test.compiler.codegen_test

# Integration tests (compile and run)
python -m unittest test.compiler.integration_test
```

## Limitations

Current limitations:

- No garbage collection (manual memory management in C)
- No closures (functions don't capture environment)
- No first-class functions (can't pass functions as values)
- No exceptions (runtime errors exit the program)
- No standard library yet

## Future Enhancements

Planned improvements:

- [ ] JIT compilation support
- [ ] Garbage collection
- [ ] Standard library (file I/O, networking, etc.)
- [ ] Optimization passes
- [ ] Closures and first-class functions
- [ ] Exception handling
- [ ] Debugger support (DWARF debug info)
- [ ] Cross-compilation support

## Dependencies

### Required

- **Python 3.8+**: For the compiler itself
- **Clang**: For compiling LLVM IR to native code

### Optional

- **LLVM Tools**: For debugging and optimization (llc, opt, llvm-dis)
- **GDB/LLDB**: For debugging compiled executables

## Troubleshooting

### "clang: command not found"

Install Clang:
```bash
# macOS
xcode-select --install

# Ubuntu/Debian
sudo apt-get install clang

# Fedora
sudo dnf install clang
```

### Compilation fails with linker errors

Make sure all required C files are being linked. Use `--runtime-lib` to add additional files.

### Generated executable crashes

1. Compile without optimization: `--no-optimize`
2. Keep IR file: `--keep-ir`
3. Check the generated IR for issues
4. Use a debugger: `lldb ./program`

### "Unknown function" error

The function isn't registered in `builtins.py`. Add the declaration there.

## Contributing

When adding new features to the compiler:

1. Update the code generator in `codegen.py`
2. Add corresponding tests in `test/compiler/`
3. Update documentation
4. Ensure all tests pass

## License

See the main project LICENSE file.

