"""
Culebra LLVM IR Compiler Module

This module provides LLVM IR code generation and AOT compilation
for the Culebra programming language.
"""

from culebra.compiler.codegen import LLVMCodeGenerator
from culebra.compiler.compiler import compile_to_llvm_ir, compile_to_executable

__all__ = ['LLVMCodeGenerator', 'compile_to_llvm_ir', 'compile_to_executable']

