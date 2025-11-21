/**
 * Culebra Runtime Library Header
 */

#ifndef CULEBRA_RUNTIME_H
#define CULEBRA_RUNTIME_H

#include <stdint.h>
#include <stdbool.h>

/**
 * Array structure
 */
typedef struct {
    int64_t length;
    char* data;
} Array;

// I/O functions
void culebra_print(...);
void culebra_print_int(int64_t value);
void culebra_print_float(double value);
void culebra_print_string(char* value);
void culebra_print_bool(bool value);
void culebra_print_multi(int count, ...);
char* culebra_input(char* prompt);

// String/Array functions
int64_t culebra_len(char* ptr);
int64_t culebra_len_array(Array* arr);
char* culebra_chr(int64_t code);
int64_t culebra_ord(char* str);

// Memory management
void* malloc_wrapper(int64_t size);
void free_wrapper(void* ptr);

// String operations
char* culebra_str_concat(char* s1, char* s2);
char* culebra_int_to_str(int64_t value);
char* culebra_float_to_str(double value);
char* culebra_bool_to_str(bool value);

// Array operations
Array* culebra_create_array(int64_t length, int64_t element_size);
void culebra_free_array(Array* arr);
void* culebra_array_get(Array* arr, int64_t index);
void culebra_array_set(Array* arr, int64_t index, int64_t value);

#endif // CULEBRA_RUNTIME_H

