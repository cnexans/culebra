# Extending Culebra with Custom C Functions

This guide explains how to add custom built-in functions written in C to the Culebra compiler.

## Overview

The Culebra compiler generates LLVM IR that links against a C runtime library. You can extend the language by adding new C functions that can be called from Culebra code.

## Quick Example

Let's add a simple `sqrt` function:

### Step 1: Implement the C function

Add to `culebra/runtime/runtime.c`:

```c
#include <math.h>

double culebra_sqrt(double x) {
    return sqrt(x);
}
```

### Step 2: Register the LLVM declaration

Add to `culebra/compiler/builtins.py` in the `BUILTIN_FUNCTIONS` dictionary:

```python
BUILTIN_FUNCTIONS: Dict[str, Tuple[str, List[str], bool]] = {
    # ... existing functions ...
    'sqrt': ('double', ['double'], False),
}
```

### Step 3: Use in Culebra code

```python
result = sqrt(16.0)
print(result)  # Outputs: 4.0
```

### Step 4: Compile with math library

```bash
python -m culebra.interpreter myprogram.culebra --compile -o myprogram --runtime-lib -lm
```

## Detailed Guide

### Type Mappings

When defining C functions, you need to map Culebra types to LLVM types:

| Culebra Type | LLVM Type | C Type |
|--------------|-----------|--------|
| `int` | `i64` | `int64_t` |
| `float` | `double` | `double` |
| `bool` | `i1` | `bool` or `int` (0/1) |
| `string` | `i8*` | `char*` |
| `array` | `%array*` | `Array*` (see below) |
| `void` | `void` | `void` |

### Working with Arrays

Arrays in Culebra are structs with a length and data pointer:

```c
typedef struct {
    int64_t length;
    char* data;
} Array;
```

Example function that works with arrays:

```c
int64_t culebra_sum_array(Array* arr) {
    int64_t sum = 0;
    int64_t* elements = (int64_t*)arr->data;
    for (int64_t i = 0; i < arr->length; i++) {
        sum += elements[i];
    }
    return sum;
}
```

Register it:

```python
'sum_array': ('i64', ['%array*'], False),
```

### Working with Strings

Strings are null-terminated C strings (`char*`):

```c
int64_t culebra_count_vowels(char* str) {
    int64_t count = 0;
    for (int i = 0; str[i] != '\0'; i++) {
        char c = tolower(str[i]);
        if (c == 'a' || c == 'e' || c == 'i' || c == 'o' || c == 'u') {
            count++;
        }
    }
    return count;
}
```

Register it:

```python
'count_vowels': ('i64', ['i8*'], False),
```

### Memory Management

If your function allocates memory that should be returned to Culebra, use `malloc`:

```c
char* culebra_repeat_string(char* str, int64_t count) {
    size_t len = strlen(str);
    char* result = (char*)malloc(len * count + 1);
    result[0] = '\0';
    
    for (int64_t i = 0; i < count; i++) {
        strcat(result, str);
    }
    
    return result;
}
```

**Note:** The Culebra runtime currently doesn't have automatic garbage collection. Memory allocated in C functions should be managed carefully.

### Variadic Functions

While technically possible, variadic functions are discouraged due to platform-specific calling conventions. Instead, use fixed-parameter versions:

```c
// DON'T do this:
void my_func(...) { }

// DO this instead:
void my_func_2(int64_t a, int64_t b) { }
void my_func_3(int64_t a, int64_t b, int64_t c) { }
```

### Using External Libraries

To link against external libraries, pass them during compilation:

#### Example: Using SDL2 for graphics

```c
// In culebra/runtime/sdl_bindings.c
#include <SDL2/SDL.h>

void* culebra_sdl_init(int64_t flags) {
    if (SDL_Init((Uint32)flags) < 0) {
        return NULL;
    }
    return (void*)1; // Success marker
}
```

Register in builtins.py:

```python
'sdl_init': ('i8*', ['i64'], False),
```

Compile with SDL2:

```bash
python -m culebra.interpreter game.culebra --compile -o game \
    --runtime-lib culebra/runtime/sdl_bindings.c \
    --runtime-lib -lSDL2
```

## Advanced: Complex Data Structures

### Example: HashMap

Let's implement a simple hash map:

#### 1. Define the structure (`culebra/runtime/hashmap.c`)

```c
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

typedef struct HashNode {
    char* key;
    int64_t value;
    struct HashNode* next;
} HashNode;

typedef struct {
    HashNode** buckets;
    int64_t size;
} HashMap;

void* culebra_hashmap_create(int64_t size) {
    HashMap* map = (HashMap*)malloc(sizeof(HashMap));
    map->size = size;
    map->buckets = (HashNode**)calloc(size, sizeof(HashNode*));
    return map;
}

void culebra_hashmap_set(void* map_ptr, char* key, int64_t value) {
    HashMap* map = (HashMap*)map_ptr;
    // Simple hash function
    int64_t hash = 0;
    for (int i = 0; key[i]; i++) {
        hash = (hash * 31 + key[i]) % map->size;
    }
    
    // Insert or update
    HashNode* node = map->buckets[hash];
    while (node != NULL) {
        if (strcmp(node->key, key) == 0) {
            node->value = value;
            return;
        }
        node = node->next;
    }
    
    // Create new node
    HashNode* new_node = (HashNode*)malloc(sizeof(HashNode));
    new_node->key = strdup(key);
    new_node->value = value;
    new_node->next = map->buckets[hash];
    map->buckets[hash] = new_node;
}

int64_t culebra_hashmap_get(void* map_ptr, char* key) {
    HashMap* map = (HashMap*)map_ptr;
    int64_t hash = 0;
    for (int i = 0; key[i]; i++) {
        hash = (hash * 31 + key[i]) % map->size;
    }
    
    HashNode* node = map->buckets[hash];
    while (node != NULL) {
        if (strcmp(node->key, key) == 0) {
            return node->value;
        }
        node = node->next;
    }
    
    return 0; // Not found
}

void culebra_hashmap_free(void* map_ptr) {
    HashMap* map = (HashMap*)map_ptr;
    for (int64_t i = 0; i < map->size; i++) {
        HashNode* node = map->buckets[i];
        while (node != NULL) {
            HashNode* next = node->next;
            free(node->key);
            free(node);
            node = next;
        }
    }
    free(map->buckets);
    free(map);
}
```

#### 2. Register the functions

In `culebra/compiler/builtins.py`:

```python
'hashmap_create': ('i8*', ['i64'], False),
'hashmap_set': ('void', ['i8*', 'i8*', 'i64'], False),
'hashmap_get': ('i64', ['i8*', 'i8*'], False),
'hashmap_free': ('void', ['i8*'], False),
```

#### 3. Use in Culebra

```python
# Create a hash map with 10 buckets
scores = hashmap_create(10)

# Set values
hashmap_set(scores, "Alice", 95)
hashmap_set(scores, "Bob", 87)
hashmap_set(scores, "Charlie", 92)

# Get values
alice_score = hashmap_get(scores, "Alice")
print("Alice's score:", alice_score)

# Clean up
hashmap_free(scores)
```

#### 4. Compile with the custom runtime

```bash
python -m culebra.interpreter myprogram.culebra --compile -o myprogram \
    --runtime-lib culebra/runtime/hashmap.c
```

## Best Practices

1. **Naming Convention**: Prefix all C functions with `culebra_` to avoid conflicts
2. **Memory Safety**: Be careful with memory allocation and deallocation
3. **Error Handling**: C functions should handle errors gracefully (return error codes or use stderr)
4. **Documentation**: Document your C functions for other developers
5. **Testing**: Test C functions independently before integrating with Culebra
6. **Type Safety**: Ensure type mappings are correct between C and LLVM

## Common Pitfalls

1. **Wrong Type Mapping**: Using `int` instead of `int64_t` can cause subtle bugs
2. **Memory Leaks**: Forgetting to free allocated memory
3. **Null Pointers**: Not checking for NULL before dereferencing
4. **String Encoding**: Culebra strings are UTF-8, ensure C functions handle them correctly
5. **Platform Differences**: Be aware of platform-specific calling conventions

## Debugging Tips

1. Use `fprintf(stderr, ...)` for debug output
2. Compile without optimization (`--no-optimize`) for easier debugging
3. Use `lldb` or `gdb` to debug the compiled executable
4. Keep the intermediate `.ll` file (`--keep-ir`) to inspect LLVM IR
5. Test C functions standalone before integrating

## Example: Complete Extension

See `examples/extending_culebra/` (to be created) for a complete example of extending Culebra with custom C functions for file I/O, networking, and more.

