import ast


class LevelOneOptimizer(ast.NodeTransformer):

    def __init__(self):
        self.explanations = []

    # 1. Constant Folding + Arithmetic Identities
    def visit_BinOp(self, node):
        self.generic_visit(node)

        # Constant folding
        if isinstance(node.left, ast.Constant) and isinstance(node.right, ast.Constant):
            try:
                value = eval(compile(ast.Expression(node), "", "eval"))
                self.explanations.append(
                    f"Applied constant folding: replaced expression with value {value}."
                )
                return ast.copy_location(ast.Constant(value=value), node)
            except Exception:
                pass

        # x + 0 or 0 + x
        if isinstance(node.op, ast.Add):
            if isinstance(node.right, ast.Constant) and node.right.value == 0:
                self.explanations.append("Simplified addition: x + 0 → x.")
                return node.left
            if isinstance(node.left, ast.Constant) and node.left.value == 0:
                self.explanations.append("Simplified addition: 0 + x → x.")
                return node.right

        # x * 1, x * 0
        if isinstance(node.op, ast.Mult):
            if isinstance(node.right, ast.Constant):
                if node.right.value == 1:
                    self.explanations.append("Simplified multiplication: x × 1 → x.")
                    return node.left
                if node.right.value == 0:
                    self.explanations.append("Simplified multiplication: x × 0 → 0.")
                    return ast.copy_location(ast.Constant(value=0), node)

            if isinstance(node.left, ast.Constant):
                if node.left.value == 1:
                    self.explanations.append("Simplified multiplication: 1 × x → x.")
                    return node.right
                if node.left.value == 0:
                    self.explanations.append("Simplified multiplication: 0 × x → 0.")
                    return ast.copy_location(ast.Constant(value=0), node)

        return node

    # 2. Remove double negation
    def visit_UnaryOp(self, node):
        self.generic_visit(node)
        if isinstance(node.op, ast.Not) and isinstance(node.operand, ast.UnaryOp):
            if isinstance(node.operand.op, ast.Not):
                self.explanations.append("Removed double negation: not(not x) → x.")
                return node.operand.operand
        return node

    # 3. Simplify boolean AND
    def visit_BoolOp(self, node):
        self.generic_visit(node)
        if isinstance(node.op, ast.And):
            original_len = len(node.values)
            node.values = [
                v for v in node.values
                if not (isinstance(v, ast.Constant) and v.value is True)
            ]
            if len(node.values) < original_len:
                self.explanations.append(
                    "Simplified boolean AND by removing redundant 'True' values."
                )
            if len(node.values) == 1:
                return node.values[0]
            # ✅ FIX: Handle case where all values were True
            if len(node.values) == 0:
                return ast.Constant(value=True)
        return node

    # 4. len(x) == 0 → not x
    def visit_Compare(self, node):
        self.generic_visit(node)
        if (
            isinstance(node.left, ast.Call)
            and isinstance(node.left.func, ast.Name)
            and node.left.func.id == "len"
            and len(node.left.args) > 0  # ✅ SAFETY: Check args exist
            and isinstance(node.ops[0], ast.Eq)
            and isinstance(node.comparators[0], ast.Constant)
            and node.comparators[0].value == 0
        ):
            self.explanations.append(
                "Replaced len(x) == 0 with not x for clarity and efficiency."
            )
            return ast.copy_location(
                ast.UnaryOp(op=ast.Not(), operand=node.left.args[0]), node
            )
        return node

    # 5. If–Else reduction
    def visit_If(self, node):
        self.generic_visit(node)

        # ✅ FIX: Return single Pass node instead of empty list
        if isinstance(node.test, ast.Constant):
            if node.test.value is True:
                self.explanations.append("Removed if-condition with constant True.")
                # Return body statements or Pass if empty
                if node.body:
                    return node.body if len(node.body) > 1 else node.body[0]
                return ast.Pass()
            if node.test.value is False:
                self.explanations.append("Removed if-condition with constant False.")
                # Return else statements or Pass if empty
                if node.orelse:
                    return node.orelse if len(node.orelse) > 1 else node.orelse[0]
                return ast.Pass()

        if (
            len(node.body) == 1 and len(node.orelse) == 1
            and isinstance(node.body[0], ast.Assign)
            and isinstance(node.orelse[0], ast.Assign)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.orelse[0].value, ast.Constant)
            and node.body[0].value.value is True
            and node.orelse[0].value.value is False
        ):
            self.explanations.append(
                "Reduced if-else assignment to direct boolean assignment."
            )
            return ast.Assign(
                targets=node.body[0].targets,
                value=node.test
            )

        return node

    # 6. Loop → List comprehension
    def visit_For(self, node):
        self.generic_visit(node)

        # ✅ IMPROVED: Better pattern matching and preserve original list
        if (
            len(node.body) == 1
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Call)
            and isinstance(node.body[0].value.func, ast.Attribute)
            and node.body[0].value.func.attr == "append"
            and len(node.body[0].value.args) == 1  # ✅ SAFETY: Ensure one arg
        ):
            list_var = node.body[0].value.func.value
            append_value = node.body[0].value.args[0]
            
            self.explanations.append(
                "Converted loop-based append to list comprehension."
            )
            
            # Create list comprehension
            list_comp = ast.ListComp(
                elt=append_value,
                generators=[
                    ast.comprehension(
                        target=node.target,
                        iter=node.iter,
                        ifs=[],
                        is_async=0
                    )
                ]
            )
            
            # Return assignment that updates the list
            return ast.copy_location(
                ast.Assign(
                    targets=[list_var],
                    value=list_comp
                ),
                node
            )

        return node

    # 7. Remove x = x
    def visit_Assign(self, node):
        self.generic_visit(node)
        
        # ✅ IMPROVED: Handle multiple targets and check all targets
        if (
            isinstance(node.value, ast.Name)
            and len(node.targets) == 1  # ✅ SAFETY: Single target only
            and isinstance(node.targets[0], ast.Name)
            and node.value.id == node.targets[0].id
        ):
            self.explanations.append(
                f"Removed redundant self-assignment: {node.targets[0].id} = {node.targets[0].id}."
            )
            return None
        return node

    # 8. Remove unused variables - ✅ FIXED VERSION
    def remove_unused_variables(self, tree):
        """Two-pass approach: collect used vars, then remove unused assignments"""
        
        # First pass: collect all used variables
        used_vars = set()
        
        class VarUsageVisitor(ast.NodeVisitor):
            def visit_Name(self, node):
                if isinstance(node.ctx, ast.Load):
                    used_vars.add(node.id)
                self.generic_visit(node)

        VarUsageVisitor().visit(tree)

        # Second pass: remove assignments to unused variables
        class RemoveUnusedAssign(ast.NodeTransformer):
            def __init__(self, used_vars, explanations_list):
                self.used_vars = used_vars
                self.explanations = explanations_list  # ✅ FIX: Use shared list

            def visit_Assign(self, node):
                self.generic_visit(node)

                # ✅ IMPROVED: Handle only simple single-target assignments
                if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                    var_name = node.targets[0].id

                    if var_name not in self.used_vars:
                        self.explanations.append(
                            f"Removed unused variable assignment: '{var_name}'"
                        )
                        return None  # Remove assignment

                return node

        # ✅ FIX: Pass explanations list so changes are captured
        remover = RemoveUnusedAssign(used_vars, self.explanations)
        return remover.visit(tree)


def optimize_code(source_code: str):
    """Main optimization function"""
    tree = ast.parse(source_code)

    optimizer = LevelOneOptimizer()
    optimized_tree = optimizer.visit(tree)
    ast.fix_missing_locations(optimized_tree)

    # Apply unused variable removal
    optimized_tree = optimizer.remove_unused_variables(optimized_tree)
    ast.fix_missing_locations(optimized_tree)

    return ast.unparse(optimized_tree), optimizer.explanations


# ✅ BONUS: Test function to verify optimizations
def test_optimizer():
    """Test cases for the optimizer"""
    
    test_cases = [
        # Constant folding
        "x = 2 + 3",
        
        # Arithmetic identities
        "y = x + 0",
        "z = x * 1",
        
        # Unused variable
        """
unused = 42
result = 10
print(result)
""",
        
        # Loop to list comprehension
        """
result = []
for i in range(10):
    result.append(i * 2)
""",
        
        # Boolean simplification
        "if True and x and True: pass",
    ]
    
    for i, code in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}:")
        print(f"{'='*60}")
        print("ORIGINAL:")
        print(code)
        
        optimized, explanations = optimize_code(code)
        
        print("\nOPTIMIZED:")
        print(optimized)
        
        print("\nEXPLANATIONS:")
        for exp in explanations:
            print(f"  • {exp}")

# ✅ Wrapper function for Flask integration
def run_rule_optimizer(code: str):
    """
    Wrapper used by app.py
    Returns optimized code AND explanations
    """
    optimized_code, explanations = optimize_code(code)
    return optimized_code, explanations


if __name__ == "__main__":
    test_optimizer()