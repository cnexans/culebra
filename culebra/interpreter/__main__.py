import sys
import argparse
from pathlib import Path
from culebra.interpreter.interpreter import Interpreter
from culebra.parser import Parser
from culebra.lexer import Lexer
from culebra.error_reporter import ErrorReporter
from culebra.token import TokenType


def main():
    parser = argparse.ArgumentParser(description='Culebra interpreter, compiler, or REPL')

    # Optional filename
    parser.add_argument('filename', nargs='?', help='Source file to interpret or compile')

    # Mode flags
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('-l', '--lexer', action='store_true', help='Run lexer')
    mode_group.add_argument('-p', '--parser', action='store_true', help='Run parser')
    mode_group.add_argument('-i', '--interpreter', action='store_true', help='Run interpreter')
    mode_group.add_argument('-c', '--compile', action='store_true', help='Compile to executable')
    mode_group.add_argument('--compiler', action='store_true', help='Run compiler REPL (show LLVM IR)')

    # Compiler flags
    parser.add_argument('-o', '--output', help='Output file path')
    parser.add_argument('--emit-llvm', action='store_true', help='Emit LLVM IR only (don\'t compile to executable)')
    parser.add_argument('--keep-ir', action='store_true', help='Keep intermediate .ll file')
    parser.add_argument('--no-optimize', action='store_true', help='Disable optimizations')
    parser.add_argument('--runtime-lib', action='append', help='Additional C runtime library to link')

    # Parse arguments
    args = parser.parse_args()

    if args.filename is None:
        # --- REPL mode ---
        if args.lexer:
            mode = "lexer"
        elif args.parser:
            mode = "parser"
        elif args.compiler:
            mode = "compiler"
        elif args.interpreter:
            mode = "interpreter"
        else:
            mode = "interpreter"  # default REPL mode
        from culebra import repl
        repl.repl(mode)
    else:
        # --- File processing mode ---
        file_path = Path(args.filename)
        if not file_path.exists():
            print(f"Error: File '{args.filename}' not found")
            sys.exit(1)
        
        # Handle compilation mode
        if args.compile or args.emit_llvm:
            from culebra.compiler.compiler import compile_file
            
            success = compile_file(
                source_file=str(file_path),
                output_file=args.output,
                emit_llvm=args.emit_llvm,
                keep_ir=args.keep_ir,
                optimize=not args.no_optimize,
                runtime_libs=args.runtime_lib
            )
            
            sys.exit(0 if success else 1)
        
        try:
            # Read the source file
            with open(file_path, 'r') as f:
                source = f.read()

            # Create lexer and generate tokens
            lexer = Lexer()
            tokens = lexer.tokenize(source)

            if args.lexer:
                for token in tokens:
                    if token.type != TokenType.EOF:
                        print(token)
                return

            # Create parser (renamed local variable to avoid shadowing the argparse parser)
            ast_parser = Parser(tokens)
            ast = ast_parser.parse()

            if ast_parser.has_error:
                reporter = ErrorReporter(source)
                reporter.report(ast_parser.last_token, str(ast_parser.last_error))
                sys.exit(1)

            # If parse flag is set, pretty print the AST and exit
            if args.parser:
                print(ast.pretty())
                return

            # Otherwise, create interpreter and run the AST
            interpreter = Interpreter()

            try:
                interpreter.evaluate(ast)
            except Exception as e:
                reporter = ErrorReporter(source)
                reporter.report(interpreter.last_node.token, str(e))
                sys.exit(1)

        except Exception as e:
            print(f"Error: {str(e)}")
            sys.exit(1)

if __name__ == '__main__':
    main()