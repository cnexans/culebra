/**
 * Culebra Runtime Library
 * 
 * Provides C implementations of built-in functions for compiled Culebra programs.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdbool.h>

/**
 * Array structure to match LLVM definition: { i64 length, i8* data }
 */
typedef struct {
    int64_t length;
    char* data;
} Array;

/**
 * Print values to stdout (variadic function)
 * Note: This is kept for compatibility but not actively used.
 * The compiler uses specific print functions instead.
 */
void culebra_print(int dummy, ...) {
    va_list args;
    va_start(args, dummy);
    
    // Print all string arguments separated by spaces
    bool first = true;
    char* str;
    while ((str = va_arg(args, char*)) != NULL) {
        if (!first) printf(" ");
        printf("%s", str);
        first = false;
    }
    
    printf("\n");
    va_end(args);
}

/**
 * Enhanced print that takes a format string approach
 * The compiler will convert arguments to strings before calling
 */
void culebra_print_int(int64_t value) {
    printf("%lld\n", (long long)value);
}

void culebra_print_float(double value) {
    printf("%g\n", value);
}

void culebra_print_string(char* value) {
    printf("%s\n", value);
}

void culebra_print_bool(bool value) {
    printf("%s\n", value ? "true" : "false");
}

/**
 * Print multiple values (the compiler will handle formatting)
 */
void culebra_print_multi(int count, ...) {
    va_list args;
    va_start(args, count);
    
    for (int i = 0; i < count; i++) {
        if (i > 0) printf(" ");
        char* str = va_arg(args, char*);
        if (str != NULL) {
            printf("%s", str);
        }
    }
    printf("\n");
    fflush(stdout);
    
    va_end(args);
}

/**
 * Read a line from stdin with optional prompt
 */
char* culebra_input(char* prompt) {
    if (prompt != NULL && strlen(prompt) > 0) {
        printf("%s", prompt);
        fflush(stdout);
    }
    
    char* line = NULL;
    size_t len = 0;
    ssize_t read = getline(&line, &len, stdin);
    
    if (read == -1) {
        free(line);
        return strdup("");
    }
    
    // Remove trailing newline
    if (read > 0 && line[read - 1] == '\n') {
        line[read - 1] = '\0';
    }
    
    return line;
}

/**
 * Get length of a string or array
 */
int64_t culebra_len(char* ptr) {
    if (ptr == NULL) return 0;
    
    // Check if this is an array structure (simple heuristic)
    // For strings, just return strlen
    return (int64_t)strlen(ptr);
}

/**
 * Get length of an array structure
 */
int64_t culebra_len_array(Array* arr) {
    if (arr == NULL) return 0;
    return arr->length;
}

/**
 * Convert integer to character (returns single-char string)
 */
char* culebra_chr(int64_t code) {
    char* result = (char*)malloc(2);
    result[0] = (char)code;
    result[1] = '\0';
    return result;
}

/**
 * Get ASCII/Unicode value of first character in string
 */
int64_t culebra_ord(char* str) {
    if (str == NULL || str[0] == '\0') {
        return 0;
    }
    return (int64_t)str[0];
}

/**
 * Allocate memory (wrapper for malloc)
 */
void* malloc_wrapper(int64_t size) {
    return malloc((size_t)size);
}

/**
 * Free memory (wrapper for free)
 */
void free_wrapper(void* ptr) {
    free(ptr);
}

/**
 * String concatenation
 */
char* culebra_str_concat(char* s1, char* s2) {
    if (s1 == NULL) s1 = "";
    if (s2 == NULL) s2 = "";
    
    size_t len1 = strlen(s1);
    size_t len2 = strlen(s2);
    char* result = (char*)malloc(len1 + len2 + 1);
    
    strcpy(result, s1);
    strcat(result, s2);
    
    return result;
}

/**
 * Convert integer to string
 */
char* culebra_int_to_str(int64_t value) {
    char* buffer = (char*)malloc(32);
    snprintf(buffer, 32, "%lld", (long long)value);
    return buffer;
}

/**
 * Convert float to string
 */
char* culebra_float_to_str(double value) {
    char* buffer = (char*)malloc(32);
    snprintf(buffer, 32, "%g", value);
    return buffer;
}

/**
 * Convert bool to string
 */
char* culebra_bool_to_str(bool value) {
    return strdup(value ? "true" : "false");
}

/**
 * Create an array structure
 */
Array* culebra_create_array(int64_t length, int64_t element_size) {
    Array* arr = (Array*)malloc(sizeof(Array));
    arr->length = length;
    arr->data = (char*)calloc((size_t)length, (size_t)element_size);
    return arr;
}

/**
 * Free an array structure
 */
void culebra_free_array(Array* arr) {
    if (arr != NULL) {
        free(arr->data);
        free(arr);
    }
}

/**
 * Get element from array (returns pointer to element)
 */
void* culebra_array_get(Array* arr, int64_t index) {
    if (arr == NULL || index < 0 || index >= arr->length) {
        fprintf(stderr, "Array index out of bounds: %lld\n", (long long)index);
        exit(1);
    }
    // Assuming 8-byte elements (i64 or pointers)
    return arr->data + (index * 8);
}

/**
 * Set element in array
 */
void culebra_array_set(Array* arr, int64_t index, int64_t value) {
    if (arr == NULL || index < 0 || index >= arr->length) {
        fprintf(stderr, "Array index out of bounds: %lld\n", (long long)index);
        exit(1);
    }
    ((int64_t*)arr->data)[index] = value;
}

