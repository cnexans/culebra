"""
LLVM IR Code Generator for Culebra

Traverses the AST and generates LLVM IR code.
"""

from typing import Dict, List, Optional, Tuple, Any
from culebra import ast
from culebra.compiler.types import (
    CulebraType, LLVMType, I64, DOUBLE, I1, I8_PTR, VOID,
    get_llvm_type, infer_type_from_value, get_binary_result_type,
    needs_type_conversion, get_conversion_instruction
)
from culebra.compiler.builtins import get_all_declarations, is_builtin


class LLVMCodeGenerator:
    """
    LLVM IR code generator that traverses Culebra AST.
    
    Uses visitor pattern to generate LLVM IR from AST nodes.
    """
    
    def __init__(self):
        self.output: List[str] = []
        self.temp_counter = 0
        self.label_counter = 0
        self.string_counter = 0
        self.global_strings: Dict[str, str] = {}
        
        # Variable tracking: name -> (llvm_register, type)
        self.variables: Dict[str, Tuple[str, CulebraType]] = {}
        
        # Function tracking: name -> (return_type, param_types)
        self.functions: Dict[str, Tuple[CulebraType, List[CulebraType]]] = {}
        
        # Current function context
        self.current_function: Optional[str] = None
        self.current_return_type: Optional[CulebraType] = None
        
    def generate(self, program: ast.Program) -> str:
        """
        Generate complete LLVM IR module from AST.
        
        Args:
            program: Root AST node (Program)
            
        Returns:
            Complete LLVM IR as string
        """
        self.output = []
        
        # Module header
        self.emit("; ModuleID = 'culebra'")
        self.emit('source_filename = "culebra"')
        self.emit('')
        
        # Array type definition
        self.emit('%array = type { i64, i8* }')
        self.emit('')
        
        # Built-in function declarations
        self.emit('; Built-in function declarations')
        self.emit(get_all_declarations())
        self.emit('')
        
        # Additional runtime function declarations
        self.emit('declare i8* @culebra_str_concat(i8*, i8*)')
        self.emit('declare i8* @culebra_int_to_str(i64)')
        self.emit('declare i8* @culebra_float_to_str(double)')
        self.emit('declare i8* @culebra_bool_to_str(i1)')
        self.emit('declare void @culebra_print_int(i64)')
        self.emit('declare void @culebra_print_float(double)')
        self.emit('declare void @culebra_print_string(i8*)')
        self.emit('declare void @culebra_print_bool(i1)')
        self.emit('declare void @culebra_print_multi(i32, ...)')
        self.emit('declare %array* @culebra_create_array(i64, i64)')
        self.emit('declare void @culebra_free_array(%array*)')
        self.emit('declare i8* @culebra_array_get(%array*, i64)')
        self.emit('declare void @culebra_array_set(%array*, i64, i64)')
        self.emit('declare i64 @culebra_len_array(%array*)')
        self.emit('')
        
        # Process all statements in the program
        # First pass: collect function definitions
        for stmt in program.statements:
            if isinstance(stmt, ast.FunctionDefinition):
                self._register_function(stmt)
        
        # Generate main function wrapper
        self.emit('define i32 @main() {')
        self.emit('entry:')
        
        # Process all top-level statements
        for stmt in program.statements:
            if isinstance(stmt, ast.FunctionDefinition):
                # Skip function definitions in main, they'll be generated separately
                pass
            else:
                self.visit(stmt)
        
        self.emit('  ret i32 0')
        self.emit('}')
        self.emit('')
        
        # Generate function definitions
        for stmt in program.statements:
            if isinstance(stmt, ast.FunctionDefinition):
                self._generate_function(stmt)
        
        # String constants at the end
        if self.global_strings:
            self.emit('; String constants')
            for name, value in self.global_strings.items():
                escaped = value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\0A')
                str_len = len(value) + 1
                self.emit(f'{name} = private unnamed_addr constant [{str_len} x i8] c"{escaped}\\00"')
        
        return '\n'.join(self.output)
    
    def emit(self, line: str):
        """Add a line to the output."""
        self.output.append(line)
    
    def new_temp(self) -> str:
        """Generate a new temporary register name."""
        self.temp_counter += 1
        return f"%t{self.temp_counter}"
    
    def new_label(self, prefix: str = "label") -> str:
        """Generate a new label name."""
        self.label_counter += 1
        return f"{prefix}{self.label_counter}"
    
    def new_string_constant(self, value: str) -> str:
        """
        Create or reuse a global string constant.
        
        Args:
            value: String value
            
        Returns:
            Global variable name for the string
        """
        # Check if we already have this string
        for name, existing_value in self.global_strings.items():
            if existing_value == value:
                return name
        
        # Create new string constant
        self.string_counter += 1
        name = f"@.str.{self.string_counter}"
        self.global_strings[name] = value
        return name
    
    def visit(self, node: ast.ASTNode) -> Optional[str]:
        """
        Visit an AST node and generate LLVM IR.
        
        Returns:
            LLVM register containing the result (for expressions)
        """
        if isinstance(node, ast.Integer):
            return self.visit_integer(node)
        elif isinstance(node, ast.Float):
            return self.visit_float(node)
        elif isinstance(node, ast.String):
            return self.visit_string(node)
        elif isinstance(node, ast.Bool):
            return self.visit_bool(node)
        elif isinstance(node, ast.Identifier):
            return self.visit_identifier(node)
        elif isinstance(node, ast.Assignment):
            return self.visit_assignment(node)
        elif isinstance(node, ast.BinaryOperation):
            return self.visit_binary_operation(node)
        elif isinstance(node, ast.PrefixOperation):
            return self.visit_prefix_operation(node)
        elif isinstance(node, ast.Conditional):
            return self.visit_conditional(node)
        elif isinstance(node, ast.While):
            return self.visit_while(node)
        elif isinstance(node, ast.For):
            return self.visit_for(node)
        elif isinstance(node, ast.FunctionCall):
            return self.visit_function_call(node)
        elif isinstance(node, ast.ReturnStatement):
            return self.visit_return(node)
        elif isinstance(node, ast.Array):
            return self.visit_array(node)
        elif isinstance(node, ast.BracketAccess):
            return self.visit_bracket_access(node)
        else:
            raise NotImplementedError(f"Code generation for {type(node).__name__} not implemented")
    
    def visit_integer(self, node: ast.Integer) -> str:
        """Generate IR for integer literal."""
        # Integer literals are used directly, no register needed
        return str(node.value)
    
    def visit_float(self, node: ast.Float) -> str:
        """Generate IR for float literal."""
        # Float literals in LLVM use hexadecimal representation
        # For simplicity, we'll use decimal with proper formatting
        return str(node.value)
    
    def visit_string(self, node: ast.String) -> str:
        """Generate IR for string literal."""
        # Create global string constant and get pointer to it
        global_name = self.new_string_constant(node.value)
        str_len = len(node.value) + 1
        
        temp = self.new_temp()
        self.emit(f"  {temp} = getelementptr [{str_len} x i8], [{str_len} x i8]* {global_name}, i32 0, i32 0")
        return temp
    
    def visit_bool(self, node: ast.Bool) -> str:
        """Generate IR for boolean literal."""
        return '1' if node.value else '0'
    
    def visit_identifier(self, node: ast.Identifier) -> str:
        """Generate IR for identifier (variable load)."""
        if node.value not in self.variables:
            raise NameError(f"Undefined variable: {node.value}")
        
        alloca_reg, var_type = self.variables[node.value]
        llvm_type = get_llvm_type(var_type)
        
        temp = self.new_temp()
        self.emit(f"  {temp} = load {llvm_type}, {llvm_type}* {alloca_reg}")
        return temp
    
    def visit_assignment(self, node: ast.Assignment) -> Optional[str]:
        """Generate IR for assignment."""
        # Evaluate the right-hand side
        value_reg = self.visit(node.value)
        value_type = self._infer_expression_type(node.value)
        
        if isinstance(node.identifier, ast.Identifier):
            var_name = node.identifier.value
            
            # Check if variable exists, if not create it
            if var_name not in self.variables:
                # Allocate stack space for new variable
                llvm_type = get_llvm_type(value_type)
                alloca_reg = self.new_temp()
                self.emit(f"  {alloca_reg} = alloca {llvm_type}")
                self.variables[var_name] = (alloca_reg, value_type)
            
            alloca_reg, _ = self.variables[var_name]
            llvm_type = get_llvm_type(value_type)
            
            # Store the value
            self.emit(f"  store {llvm_type} {value_reg}, {llvm_type}* {alloca_reg}")
        
        elif isinstance(node.identifier, ast.BracketAccess):
            # Array element assignment
            self._visit_array_store(node.identifier, value_reg, value_type)
        
        return None
    
    def visit_binary_operation(self, node: ast.BinaryOperation) -> str:
        """Generate IR for binary operations."""
        left_reg = self.visit(node.left)
        right_reg = self.visit(node.right)
        
        left_type = self._infer_expression_type(node.left)
        right_type = self._infer_expression_type(node.right)
        
        op_str = node.token.literal
        result_type = get_binary_result_type(left_type, right_type, op_str)
        
        # Handle type conversions
        if left_type != right_type:
            if left_type == CulebraType.INTEGER and right_type == CulebraType.FLOAT:
                conv_temp = self.new_temp()
                self.emit(f"  {conv_temp} = sitofp i64 {left_reg} to double")
                left_reg = conv_temp
                left_type = CulebraType.FLOAT
            elif left_type == CulebraType.FLOAT and right_type == CulebraType.INTEGER:
                conv_temp = self.new_temp()
                self.emit(f"  {conv_temp} = sitofp i64 {right_reg} to double")
                right_reg = conv_temp
                right_type = CulebraType.FLOAT
        
        temp = self.new_temp()
        
        # Arithmetic operations
        if isinstance(node, ast.PlusOperation):
            if left_type == CulebraType.STRING:
                # String concatenation
                self.emit(f"  {temp} = call i8* @culebra_str_concat(i8* {left_reg}, i8* {right_reg})")
            elif left_type == CulebraType.FLOAT:
                self.emit(f"  {temp} = fadd double {left_reg}, {right_reg}")
            else:
                self.emit(f"  {temp} = add i64 {left_reg}, {right_reg}")
        
        elif isinstance(node, ast.MinusOperation):
            if left_type == CulebraType.FLOAT:
                self.emit(f"  {temp} = fsub double {left_reg}, {right_reg}")
            else:
                self.emit(f"  {temp} = sub i64 {left_reg}, {right_reg}")
        
        elif isinstance(node, ast.MultiplicationOperation):
            if left_type == CulebraType.FLOAT:
                self.emit(f"  {temp} = fmul double {left_reg}, {right_reg}")
            else:
                self.emit(f"  {temp} = mul i64 {left_reg}, {right_reg}")
        
        elif isinstance(node, ast.DivisionOperation):
            if left_type == CulebraType.FLOAT:
                self.emit(f"  {temp} = fdiv double {left_reg}, {right_reg}")
            else:
                self.emit(f"  {temp} = sdiv i64 {left_reg}, {right_reg}")
        
        # Comparison operations
        elif isinstance(node, ast.EqualOperation):
            if left_type == CulebraType.FLOAT:
                self.emit(f"  {temp} = fcmp oeq double {left_reg}, {right_reg}")
            else:
                self.emit(f"  {temp} = icmp eq i64 {left_reg}, {right_reg}")
        
        elif isinstance(node, ast.NotEqualOperation):
            if left_type == CulebraType.FLOAT:
                self.emit(f"  {temp} = fcmp one double {left_reg}, {right_reg}")
            else:
                self.emit(f"  {temp} = icmp ne i64 {left_reg}, {right_reg}")
        
        elif isinstance(node, ast.LessOperation):
            if left_type == CulebraType.FLOAT:
                self.emit(f"  {temp} = fcmp olt double {left_reg}, {right_reg}")
            else:
                self.emit(f"  {temp} = icmp slt i64 {left_reg}, {right_reg}")
        
        elif isinstance(node, ast.LessOrEqualOperation):
            if left_type == CulebraType.FLOAT:
                self.emit(f"  {temp} = fcmp ole double {left_reg}, {right_reg}")
            else:
                self.emit(f"  {temp} = icmp sle i64 {left_reg}, {right_reg}")
        
        elif isinstance(node, ast.GreaterOperation):
            if left_type == CulebraType.FLOAT:
                self.emit(f"  {temp} = fcmp ogt double {left_reg}, {right_reg}")
            else:
                self.emit(f"  {temp} = icmp sgt i64 {left_reg}, {right_reg}")
        
        elif isinstance(node, ast.GreaterOrEqualOperation):
            if left_type == CulebraType.FLOAT:
                self.emit(f"  {temp} = fcmp oge double {left_reg}, {right_reg}")
            else:
                self.emit(f"  {temp} = icmp sge i64 {left_reg}, {right_reg}")
        
        # Logical operations
        elif isinstance(node, ast.AndOperation):
            self.emit(f"  {temp} = and i1 {left_reg}, {right_reg}")
        
        elif isinstance(node, ast.OrOperation):
            self.emit(f"  {temp} = or i1 {left_reg}, {right_reg}")
        
        else:
            raise NotImplementedError(f"Binary operation {type(node).__name__} not implemented")
        
        return temp
    
    def visit_prefix_operation(self, node: ast.PrefixOperation) -> str:
        """Generate IR for prefix operations."""
        operand_reg = self.visit(node.value)
        operand_type = self._infer_expression_type(node.value)
        
        temp = self.new_temp()
        
        if isinstance(node, ast.NegativeOperation):
            if operand_type == CulebraType.FLOAT:
                self.emit(f"  {temp} = fneg double {operand_reg}")
            else:
                self.emit(f"  {temp} = sub i64 0, {operand_reg}")
        
        elif isinstance(node, ast.NotOperation):
            self.emit(f"  {temp} = xor i1 {operand_reg}, 1")
        
        else:
            raise NotImplementedError(f"Prefix operation {type(node).__name__} not implemented")
        
        return temp
    
    def visit_conditional(self, node: ast.Conditional) -> Optional[str]:
        """Generate IR for if/else statements."""
        # Evaluate condition
        cond_reg = self.visit(node.condition)
        cond_type = self._infer_expression_type(node.condition)
        
        # Convert to i1 if necessary
        if cond_type != CulebraType.BOOL:
            bool_temp = self.new_temp()
            if cond_type == CulebraType.INTEGER:
                self.emit(f"  {bool_temp} = icmp ne i64 {cond_reg}, 0")
            elif cond_type == CulebraType.FLOAT:
                self.emit(f"  {bool_temp} = fcmp one double {cond_reg}, 0.0")
            else:
                bool_temp = cond_reg
            cond_reg = bool_temp
        
        # Generate labels
        then_label = self.new_label("then")
        else_label = self.new_label("else") if node.otherwise else None
        merge_label = self.new_label("merge")
        
        # Branch instruction
        if else_label:
            self.emit(f"  br i1 {cond_reg}, label %{then_label}, label %{else_label}")
        else:
            self.emit(f"  br i1 {cond_reg}, label %{then_label}, label %{merge_label}")
        
        # Then block
        self.emit(f"{then_label}:")
        for stmt in node.body.statements:
            self.visit(stmt)
        self.emit(f"  br label %{merge_label}")
        
        # Else block (if exists)
        if else_label:
            self.emit(f"{else_label}:")
            if isinstance(node.otherwise, ast.Conditional):
                # Handle elif as nested if
                self.visit_conditional(node.otherwise)
            else:
                for stmt in node.otherwise.body.statements:
                    self.visit(stmt)
                self.emit(f"  br label %{merge_label}")
        
        # Merge block
        self.emit(f"{merge_label}:")
        
        return None
    
    def visit_while(self, node: ast.While) -> Optional[str]:
        """Generate IR for while loops."""
        # Generate labels
        cond_label = self.new_label("while_cond")
        body_label = self.new_label("while_body")
        end_label = self.new_label("while_end")
        
        # Jump to condition check
        self.emit(f"  br label %{cond_label}")
        
        # Condition block
        self.emit(f"{cond_label}:")
        cond_reg = self.visit(node.condition)
        cond_type = self._infer_expression_type(node.condition)
        
        # Convert to i1 if necessary
        if cond_type != CulebraType.BOOL:
            bool_temp = self.new_temp()
            if cond_type == CulebraType.INTEGER:
                self.emit(f"  {bool_temp} = icmp ne i64 {cond_reg}, 0")
            else:
                bool_temp = cond_reg
            cond_reg = bool_temp
        
        self.emit(f"  br i1 {cond_reg}, label %{body_label}, label %{end_label}")
        
        # Body block
        self.emit(f"{body_label}:")
        for stmt in node.body.statements:
            self.visit(stmt)
        self.emit(f"  br label %{cond_label}")
        
        # End block
        self.emit(f"{end_label}:")
        
        return None
    
    def visit_for(self, node: ast.For) -> Optional[str]:
        """Generate IR for for loops (converted to while loop)."""
        # Execute pre statement
        self.visit(node.pre)
        
        # Generate labels
        cond_label = self.new_label("for_cond")
        body_label = self.new_label("for_body")
        post_label = self.new_label("for_post")
        end_label = self.new_label("for_end")
        
        # Jump to condition check
        self.emit(f"  br label %{cond_label}")
        
        # Condition block
        self.emit(f"{cond_label}:")
        cond_reg = self.visit(node.condition)
        cond_type = self._infer_expression_type(node.condition)
        
        # Convert to i1 if necessary
        if cond_type != CulebraType.BOOL:
            bool_temp = self.new_temp()
            if cond_type == CulebraType.INTEGER:
                self.emit(f"  {bool_temp} = icmp ne i64 {cond_reg}, 0")
            else:
                bool_temp = cond_reg
            cond_reg = bool_temp
        
        self.emit(f"  br i1 {cond_reg}, label %{body_label}, label %{end_label}")
        
        # Body block
        self.emit(f"{body_label}:")
        for stmt in node.body.statements:
            self.visit(stmt)
        self.emit(f"  br label %{post_label}")
        
        # Post block
        self.emit(f"{post_label}:")
        self.visit(node.post)
        self.emit(f"  br label %{cond_label}")
        
        # End block
        self.emit(f"{end_label}:")
        
        return None
    
    def visit_function_call(self, node: ast.FunctionCall) -> str:
        """Generate IR for function calls."""
        func_name = node.function.value
        
        # Handle built-in functions
        if func_name == 'print':
            return self._generate_print_call(node)
        elif func_name == 'input':
            return self._generate_input_call(node)
        elif func_name == 'len':
            return self._generate_len_call(node)
        elif func_name == 'chr':
            return self._generate_chr_call(node)
        elif func_name == 'ord':
            return self._generate_ord_call(node)
        
        # User-defined functions
        if func_name not in self.functions:
            raise NameError(f"Undefined function: {func_name}")
        
        return_type, param_types = self.functions[func_name]
        
        # Evaluate arguments
        arg_regs = []
        for arg in node.arguments:
            arg_reg = self.visit(arg)
            arg_regs.append(arg_reg)
        
        # Build call instruction
        llvm_return_type = get_llvm_type(return_type)
        args_str = ', '.join(f"{get_llvm_type(param_types[i])} {arg_regs[i]}" 
                            for i in range(len(arg_regs)))
        
        if return_type == CulebraType.VOID:
            self.emit(f"  call {llvm_return_type} @{func_name}({args_str})")
            return "0"  # Dummy value for void functions
        else:
            temp = self.new_temp()
            self.emit(f"  {temp} = call {llvm_return_type} @{func_name}({args_str})")
            return temp
    
    def visit_return(self, node: ast.ReturnStatement) -> Optional[str]:
        """Generate IR for return statements."""
        if node.value:
            value_reg = self.visit(node.value)
            value_type = self._infer_expression_type(node.value)
            llvm_type = get_llvm_type(value_type)
            self.emit(f"  ret {llvm_type} {value_reg}")
        else:
            self.emit("  ret void")
        return None
    
    def visit_array(self, node: ast.Array) -> str:
        """Generate IR for array creation."""
        # Create array structure
        length = len(node.elements)
        temp = self.new_temp()
        self.emit(f"  {temp} = call %array* @culebra_create_array(i64 {length}, i64 8)")
        
        # Initialize elements
        for i, elem in enumerate(node.elements):
            elem_reg = self.visit(elem)
            elem_type = self._infer_expression_type(elem)
            
            # Convert to i64 if necessary
            if elem_type == CulebraType.INTEGER:
                self.emit(f"  call void @culebra_array_set(%array* {temp}, i64 {i}, i64 {elem_reg})")
        
        return temp
    
    def visit_bracket_access(self, node: ast.BracketAccess) -> str:
        """Generate IR for array/string indexing."""
        target_reg = self.visit(node.target)
        index_reg = self.visit(node.index)
        target_type = self._infer_expression_type(node.target)
        
        if target_type == CulebraType.ARRAY:
            # Array access
            temp = self.new_temp()
            ptr_temp = self.new_temp()
            self.emit(f"  {ptr_temp} = call i8* @culebra_array_get(%array* {target_reg}, i64 {index_reg})")
            self.emit(f"  {temp} = bitcast i8* {ptr_temp} to i64*")
            result_temp = self.new_temp()
            self.emit(f"  {result_temp} = load i64, i64* {temp}")
            return result_temp
        elif target_type == CulebraType.STRING:
            # String indexing (return character as string)
            temp = self.new_temp()
            char_ptr = self.new_temp()
            self.emit(f"  {char_ptr} = getelementptr i8, i8* {target_reg}, i64 {index_reg}")
            self.emit(f"  {temp} = load i8, i8* {char_ptr}")
            # Convert char to i64 for now
            result = self.new_temp()
            self.emit(f"  {result} = sext i8 {temp} to i64")
            return result
        
        raise TypeError(f"Cannot index type {target_type}")
    
    def _visit_array_store(self, bracket_access: ast.BracketAccess, value_reg: str, value_type: CulebraType):
        """Helper to generate array element store."""
        target_reg = self.visit(bracket_access.target)
        index_reg = self.visit(bracket_access.index)
        
        # For now, only support i64 array elements
        if value_type == CulebraType.INTEGER:
            self.emit(f"  call void @culebra_array_set(%array* {target_reg}, i64 {index_reg}, i64 {value_reg})")
    
    def _register_function(self, func_def: ast.FunctionDefinition):
        """Register a function signature."""
        func_name = func_def.name.value
        # For now, assume all functions return i64 and take i64 parameters
        param_types = [CulebraType.INTEGER] * len(func_def.arguments)
        return_type = CulebraType.INTEGER  # Default, will be improved with type inference
        self.functions[func_name] = (return_type, param_types)
    
    def _generate_function(self, func_def: ast.FunctionDefinition):
        """Generate a complete function definition."""
        func_name = func_def.name.value
        return_type, param_types = self.functions[func_name]
        
        # Save current context
        old_variables = self.variables.copy()
        old_function = self.current_function
        old_return_type = self.current_return_type
        
        self.current_function = func_name
        self.current_return_type = return_type
        
        # Build parameter list
        params_list = []
        for i, arg in enumerate(func_def.arguments):
            llvm_type = get_llvm_type(param_types[i])
            param_name = f"%{arg.value}"
            params_list.append(f"{llvm_type} {param_name}")
        
        params_str = ', '.join(params_list)
        llvm_return_type = get_llvm_type(return_type)
        
        # Function header
        self.emit(f"define {llvm_return_type} @{func_name}({params_str}) {{")
        self.emit("entry:")
        
        # Allocate space for parameters and store them
        for i, arg in enumerate(func_def.arguments):
            arg_name = arg.value
            llvm_type = get_llvm_type(param_types[i])
            alloca_reg = self.new_temp()
            self.emit(f"  {alloca_reg} = alloca {llvm_type}")
            self.emit(f"  store {llvm_type} %{arg_name}, {llvm_type}* {alloca_reg}")
            self.variables[arg_name] = (alloca_reg, param_types[i])
        
        # Generate function body
        for stmt in func_def.body.statements:
            self.visit(stmt)
        
        # Add default return if needed
        if return_type == CulebraType.VOID:
            self.emit("  ret void")
        else:
            # Return 0 as default
            self.emit(f"  ret {llvm_return_type} 0")
        
        self.emit("}")
        self.emit("")
        
        # Restore context
        self.variables = old_variables
        self.current_function = old_function
        self.current_return_type = old_return_type
    
    def _generate_print_call(self, node: ast.FunctionCall) -> str:
        """Generate specialized print call."""
        if len(node.arguments) == 0:
            # Empty print (just newline)
            empty_str = self.new_string_constant("")
            str_len = 1
            temp = self.new_temp()
            self.emit(f"  {temp} = getelementptr [{str_len} x i8], [{str_len} x i8]* @.str.{self.string_counter}, i32 0, i32 0")
            self.emit(f"  call void @culebra_print_string(i8* {temp})")
        elif len(node.arguments) == 1:
            # Single argument
            arg_reg = self.visit(node.arguments[0])
            arg_type = self._infer_expression_type(node.arguments[0])
            
            if arg_type == CulebraType.INTEGER:
                self.emit(f"  call void @culebra_print_int(i64 {arg_reg})")
            elif arg_type == CulebraType.FLOAT:
                self.emit(f"  call void @culebra_print_float(double {arg_reg})")
            elif arg_type == CulebraType.STRING:
                self.emit(f"  call void @culebra_print_string(i8* {arg_reg})")
            elif arg_type == CulebraType.BOOL:
                self.emit(f"  call void @culebra_print_bool(i1 {arg_reg})")
        else:
            # Multiple arguments - convert all to strings and concatenate, then print
            result_str = None
            space_str_global = self.new_string_constant(" ")
            space_len = 2
            space_temp = self.new_temp()
            self.emit(f"  {space_temp} = getelementptr [{space_len} x i8], [{space_len} x i8]* {space_str_global}, i32 0, i32 0")
            
            for i, arg in enumerate(node.arguments):
                arg_reg = self.visit(arg)
                arg_type = self._infer_expression_type(arg)
                
                # Convert to string
                arg_str = None
                if arg_type == CulebraType.STRING:
                    arg_str = arg_reg
                elif arg_type == CulebraType.INTEGER:
                    temp = self.new_temp()
                    self.emit(f"  {temp} = call i8* @culebra_int_to_str(i64 {arg_reg})")
                    arg_str = temp
                elif arg_type == CulebraType.FLOAT:
                    temp = self.new_temp()
                    self.emit(f"  {temp} = call i8* @culebra_float_to_str(double {arg_reg})")
                    arg_str = temp
                elif arg_type == CulebraType.BOOL:
                    temp = self.new_temp()
                    self.emit(f"  {temp} = call i8* @culebra_bool_to_str(i1 {arg_reg})")
                    arg_str = temp
                
                # Concatenate
                if result_str is None:
                    result_str = arg_str
                else:
                    # Add space
                    temp1 = self.new_temp()
                    self.emit(f"  {temp1} = call i8* @culebra_str_concat(i8* {result_str}, i8* {space_temp})")
                    # Add argument
                    temp2 = self.new_temp()
                    self.emit(f"  {temp2} = call i8* @culebra_str_concat(i8* {temp1}, i8* {arg_str})")
                    result_str = temp2
            
            # Print the final concatenated string
            self.emit(f"  call void @culebra_print_string(i8* {result_str})")
        
        return "0"
    
    def _generate_input_call(self, node: ast.FunctionCall) -> str:
        """Generate input call."""
        if len(node.arguments) == 0:
            # No prompt
            empty_str = self.new_string_constant("")
            str_len = 1
            prompt_temp = self.new_temp()
            self.emit(f"  {prompt_temp} = getelementptr [{str_len} x i8], [{str_len} x i8]* @.str.{self.string_counter}, i32 0, i32 0")
        else:
            prompt_temp = self.visit(node.arguments[0])
        
        temp = self.new_temp()
        self.emit(f"  {temp} = call i8* @culebra_input(i8* {prompt_temp})")
        return temp
    
    def _generate_len_call(self, node: ast.FunctionCall) -> str:
        """Generate len call."""
        arg_reg = self.visit(node.arguments[0])
        arg_type = self._infer_expression_type(node.arguments[0])
        
        temp = self.new_temp()
        if arg_type == CulebraType.ARRAY:
            self.emit(f"  {temp} = call i64 @culebra_len_array(%array* {arg_reg})")
        else:
            self.emit(f"  {temp} = call i64 @culebra_len(i8* {arg_reg})")
        return temp
    
    def _generate_chr_call(self, node: ast.FunctionCall) -> str:
        """Generate chr call."""
        arg_reg = self.visit(node.arguments[0])
        temp = self.new_temp()
        self.emit(f"  {temp} = call i8* @culebra_chr(i64 {arg_reg})")
        return temp
    
    def _generate_ord_call(self, node: ast.FunctionCall) -> str:
        """Generate ord call."""
        arg_reg = self.visit(node.arguments[0])
        temp = self.new_temp()
        self.emit(f"  {temp} = call i64 @culebra_ord(i8* {arg_reg})")
        return temp
    
    def _infer_expression_type(self, expr: ast.Expression) -> CulebraType:
        """Infer the type of an expression."""
        if isinstance(expr, ast.Integer):
            return CulebraType.INTEGER
        elif isinstance(expr, ast.Float):
            return CulebraType.FLOAT
        elif isinstance(expr, ast.String):
            return CulebraType.STRING
        elif isinstance(expr, ast.Bool):
            return CulebraType.BOOL
        elif isinstance(expr, ast.Array):
            return CulebraType.ARRAY
        elif isinstance(expr, ast.Identifier):
            if expr.value in self.variables:
                return self.variables[expr.value][1]
            return CulebraType.INTEGER  # Default
        elif isinstance(expr, ast.BinaryOperation):
            left_type = self._infer_expression_type(expr.left)
            right_type = self._infer_expression_type(expr.right)
            return get_binary_result_type(left_type, right_type, expr.token.literal)
        elif isinstance(expr, ast.FunctionCall):
            func_name = expr.function.value
            if func_name in self.functions:
                return self.functions[func_name][0]
            # Built-in functions
            if func_name in ['len', 'ord']:
                return CulebraType.INTEGER
            elif func_name in ['input', 'chr']:
                return CulebraType.STRING
            return CulebraType.INTEGER  # Default
        elif isinstance(expr, ast.BracketAccess):
            # Array access returns element type (assume i64 for now)
            return CulebraType.INTEGER
        
        return CulebraType.INTEGER  # Default

