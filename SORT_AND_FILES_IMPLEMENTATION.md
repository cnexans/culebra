# Array Sorting and File Reading Implementation Summary

## Overview
Successfully implemented array sorting, string splitting, file reading, and utility functions (type conversions and abs) to enable Culebra to solve real-world data processing tasks like Advent of Code problems.

## Implemented Features

### 1. Array Sorting

**Method**: `arr.sort()`

**Behavior**:
- Mutates array in-place
- Returns `None`
- Sorts in ascending order
- Works with numbers and strings

**Example**:
```culebra
nums = [5, 2, 8, 1, 9]
nums.sort()
print(nums)  # [1, 2, 5, 8, 9]

strs = ["zebra", "apple", "banana"]
strs.sort()
print(strs)  # ["apple", "banana", "zebra"]
```

### 2. String Splitting

**Method**: `str.split(delimiter)`

**Behavior**:
- Returns array of substrings
- Splits on the delimiter string
- Works like Python's `str.split()`

**Example**:
```culebra
text = "hello,world,test"
parts = text.split(",")
print(parts)  # ["hello", "world", "test"]

line = "1   2"
nums = line.split("   ")
print(nums)  # ["1", "2"]
```

### 3. File Reading

**Function**: `read_file(path)`

**Behavior**:
- Returns entire file contents as a single string
- Raises `FileNotFoundError` if file doesn't exist
- Uses UTF-8 encoding

**Example**:
```culebra
content = read_file("data.txt")
print(content)
```

**Function**: `read_lines(path)`

**Behavior**:
- Returns array of lines (strings)
- Strips newline characters from each line
- Raises `FileNotFoundError` if file doesn't exist
- Uses UTF-8 encoding

**Example**:
```culebra
lines = read_lines("data.txt")
for i = 0; i < len(lines); i = i + 1:
    print(lines[i])
```

### 4. Type Conversion Functions

**Function**: `int(value)`

**Behavior**:
- Converts string or float to integer
- Raises `ValueError` if conversion fails

**Example**:
```culebra
x = int("42")      # 42
y = int(3.14)      # 3
```

**Function**: `float(value)`

**Behavior**:
- Converts string or int to float
- Raises `ValueError` if conversion fails

**Example**:
```culebra
x = float("3.14")  # 3.14
y = float(42)      # 42.0
```

**Function**: `str(value)`

**Behavior**:
- Converts any value to string representation

**Example**:
```culebra
s = str(123)       # "123"
t = str(3.14)      # "3.14"
```

### 5. Math Functions

**Function**: `abs(value)`

**Behavior**:
- Returns absolute value of a number
- Works with int and float
- Raises `TypeError` for non-numeric values

**Example**:
```culebra
print(abs(-5))     # 5
print(abs(-3.14))  # 3.14
```

## Real-World Example: Advent of Code 2024 Day 1

Successfully solved AoC 2024 Day 1 with Culebra, producing identical results to the Python solution.

**Python Version**:
```python
data = open("./aoc/2024/1/input.txt", "r").read().split("\n")

left, right = [], []
for line in data:
    left.append(int(line.split("   ")[0]))
    right.append(int(line.split("   ")[1]))

left.sort()
right.sort()

dist = 0
for i in range(len(left)):
    dist += abs(left[i] - right[i])

print(dist)
```

**Culebra Version**:
```culebra
data = read_lines("./aoc/2024/1/input.txt")

left = []
right = []

for i = 0; i < len(data); i = i + 1:
    line = data[i]
    parts = line.split("   ")
    left.push(int(parts[0]))
    right.push(int(parts[1]))

left.sort()
right.sort()

dist = 0
for i = 0; i < len(left); i = i + 1:
    dist = dist + abs(left[i] - right[i])

print(dist)
```

**Result**: Both produce `1765812` ✓

## Implementation Details

### Modified Files
- `culebra/interpreter/interpreter.py`
  - Added `sort` to array method dispatch
  - Added `split` to string method dispatch
  - Implemented 6 new built-in functions
  - Registered all new built-ins in `load_builtins()`

### New Built-in Functions
1. `read_file(path)` - Read entire file
2. `read_lines(path)` - Read file as array of lines
3. `int(value)` - Convert to integer
4. `float(value)` - Convert to float
5. `str(value)` - Convert to string
6. `abs(value)` - Absolute value

### New Methods
1. `array.sort()` - Sort array in-place
2. `string.split(delimiter)` - Split string into array

## Test Results

### Backward Compatibility
- ✅ All 100 existing tests pass
- ✅ No breaking changes

### New Test Files
1. `examples/sort_and_files_test.culebra` - Basic feature tests
2. `examples/file_reading_test.culebra` - File I/O tests
3. `aoc/2024/1/sol.culebra` - Real-world application

### Test Coverage
- ✅ Array sorting (numeric and string)
- ✅ Empty array sorting
- ✅ String splitting with various delimiters
- ✅ File reading (entire file and lines)
- ✅ Type conversions (int, float, str)
- ✅ Absolute value function
- ✅ Real-world problem solving

## Usage Examples

### Data Processing Pipeline
```culebra
# Read CSV-like data
lines = read_lines("data.csv")

# Parse and process
numbers = []
for i = 0; i < len(lines); i = i + 1:
    parts = lines[i].split(",")
    numbers.push(int(parts[0]))

# Sort and analyze
numbers.sort()
print("Min:", numbers[0])
print("Max:", numbers[len(numbers) - 1])
```

### Text Processing
```culebra
# Read and split text
content = read_file("document.txt")
words = content.split(" ")

print("Word count:", len(words))
```

### Numeric Computations
```culebra
# Calculate sum of absolute differences
values = [10, -5, 3, -8]
total = 0
for i = 0; i < len(values); i = i + 1:
    total = total + abs(values[i])
print("Total:", total)
```

## Error Handling

All new functions include proper error handling:

- **File operations**: Raise `FileNotFoundError` for missing files
- **Type conversions**: Raise `ValueError` for invalid conversions
- **Method calls**: Raise `TypeError` for incorrect argument counts
- **Abs function**: Raise `TypeError` for non-numeric values

## Language Capabilities

With these additions, Culebra now supports:
- ✅ File I/O
- ✅ String manipulation
- ✅ Array sorting
- ✅ Type conversions
- ✅ Mathematical operations
- ✅ Data processing workflows
- ✅ Real-world problem solving

This makes Culebra suitable for:
- Advent of Code challenges
- Data analysis tasks
- Text processing
- File manipulation
- Educational programming

