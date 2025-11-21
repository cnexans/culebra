"""
Compilation Pipeline for Culebra

Provides high-level functions to compile Culebra source to LLVM IR
and native executables.
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, List

from culebra.lexer import Lexer
from culebra.parser import Parser
from culebra.compiler.codegen import LLVMCodeGenerator


def compile_to_llvm_ir(source: str) -> str:
    """
    Compile Culebra source code to LLVM IR.
    
    Args:
        source: Culebra source code as string
        
    Returns:
        LLVM IR as string
        
    Raises:
        Exception: If lexing or parsing fails
    """
    # Lex
    lexer = Lexer()
    tokens = lexer.tokenize(source)
    
    # Parse
    parser = Parser(tokens)
    program = parser.parse()
    
    if parser.has_error:
        raise Exception(f"Parse error: {parser.last_error}")
    
    # Generate LLVM IR
    codegen = LLVMCodeGenerator()
    llvm_ir = codegen.generate(program)
    
    return llvm_ir


def compile_to_executable(
    source_file: str,
    output_file: str,
    runtime_libs: Optional[List[str]] = None,
    optimize: bool = True,
    emit_llvm: bool = False,
    keep_ir: bool = False,
    clang_path: str = "clang"
) -> bool:
    """
    Compile Culebra source file to native executable.
    
    Args:
        source_file: Path to Culebra source file
        output_file: Path for output executable
        runtime_libs: Additional C runtime libraries to link
        optimize: Enable optimizations (-O2)
        emit_llvm: Only emit LLVM IR, don't compile to executable
        keep_ir: Keep intermediate .ll file
        clang_path: Path to clang compiler
        
    Returns:
        True if compilation succeeded, False otherwise
    """
    source_path = Path(source_file)
    if not source_path.exists():
        print(f"Error: Source file '{source_file}' not found")
        return False
    
    # Read source
    with open(source_path, 'r') as f:
        source = f.read()
    
    try:
        # Generate LLVM IR
        llvm_ir = compile_to_llvm_ir(source)
        
        # Determine IR output path
        if emit_llvm:
            ir_path = output_file
        else:
            if keep_ir:
                ir_path = str(source_path.with_suffix('.ll'))
            else:
                # Create temporary file
                fd, ir_path = tempfile.mkstemp(suffix='.ll')
                os.close(fd)
        
        # Write LLVM IR to file
        with open(ir_path, 'w') as f:
            f.write(llvm_ir)
        
        if emit_llvm:
            print(f"LLVM IR written to: {ir_path}")
            return True
        
        # Find runtime library
        runtime_dir = Path(__file__).parent.parent / 'runtime'
        runtime_c = runtime_dir / 'runtime.c'
        
        if not runtime_c.exists():
            print(f"Error: Runtime library not found at {runtime_c}")
            return False
        
        # Build clang command
        cmd = [clang_path]
        
        # Optimization flags
        if optimize:
            cmd.append('-O2')
        else:
            cmd.append('-O0')
        
        # Input files
        cmd.append(ir_path)
        cmd.append(str(runtime_c))
        
        # Additional runtime libraries
        if runtime_libs:
            cmd.extend(runtime_libs)
        
        # Output
        cmd.extend(['-o', output_file])
        
        # Compile
        print(f"Compiling to executable: {output_file}")
        print(f"Command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print("Compilation failed:")
            print(result.stderr)
            return False
        
        # Clean up temporary IR file if requested
        if not keep_ir and not emit_llvm:
            try:
                os.unlink(ir_path)
            except:
                pass
        
        print(f"Successfully compiled to: {output_file}")
        return True
        
    except Exception as e:
        print(f"Compilation error: {e}")
        import traceback
        traceback.print_exc()
        return False


def compile_file(
    source_file: str,
    output_file: Optional[str] = None,
    emit_llvm: bool = False,
    keep_ir: bool = False,
    optimize: bool = True,
    runtime_libs: Optional[List[str]] = None
) -> bool:
    """
    Convenience function to compile a Culebra file.
    
    Args:
        source_file: Path to Culebra source file
        output_file: Path for output (auto-generated if None)
        emit_llvm: Only emit LLVM IR
        keep_ir: Keep intermediate .ll file
        optimize: Enable optimizations
        runtime_libs: Additional C runtime libraries
        
    Returns:
        True if compilation succeeded
    """
    source_path = Path(source_file)
    
    if output_file is None:
        if emit_llvm:
            output_file = str(source_path.with_suffix('.ll'))
        else:
            output_file = str(source_path.with_suffix(''))
    
    return compile_to_executable(
        source_file=source_file,
        output_file=output_file,
        runtime_libs=runtime_libs,
        optimize=optimize,
        emit_llvm=emit_llvm,
        keep_ir=keep_ir
    )


def get_llvm_ir_for_source(source: str) -> str:
    """
    Get LLVM IR for Culebra source (convenience function for REPL).
    
    Args:
        source: Culebra source code
        
    Returns:
        LLVM IR as string
    """
    return compile_to_llvm_ir(source)

