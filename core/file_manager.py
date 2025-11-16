import ast
import re

class FileManager:
    def __init__(self, file: str):
        self.file = file
        self.tree = None
        try:
            self.tree = ast.parse(file)
        except SyntaxError as e:
            print(f"Syntax error in file: {e}")
    
    def get_imports(self):
        """Extract all import statements"""
        imports = []
        
        if self.tree:
            for node in ast.walk(self.tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append({
                            'type': 'import',
                            'module': alias.name,
                            'alias': alias.asname
                        })
                elif isinstance(node, ast.ImportFrom):
                    module = node.module if node.module else ''
                    for alias in node.names:
                        imports.append({
                            'type': 'from_import',
                            'module': module,
                            'name': alias.name,
                            'alias': alias.asname
                        })
        
        return imports
    
    def get_function_calls(self):
        """Extract all function calls with context"""
        calls = []
        
        if self.tree:
            for node in ast.walk(self.tree):
                if isinstance(node, ast.Call):
                    call_info = self._extract_call_info(node)
                    if call_info:
                        calls.append(call_info)
        
        return calls
    
    def _extract_call_info(self, node):
        """Extract detailed information about a function call"""
        try:
            if isinstance(node.func, ast.Name):
                # Simple function call: func()
                return {
                    'type': 'simple',
                    'name': node.func.id,
                    'full_name': node.func.id,
                    'args': self._extract_args(node.args),
                    'lineno': node.lineno
                }
            elif isinstance(node.func, ast.Attribute):
                # Method call: obj.method() or module.func()
                obj_name = self._get_obj_name(node.func.value)
                return {
                    'type': 'attribute',
                    'object': obj_name,
                    'method': node.func.attr,
                    'full_name': f"{obj_name}.{node.func.attr}",
                    'args': self._extract_args(node.args),
                    'lineno': node.lineno
                }
        except Exception as e:
            print(f"Error extracting call info: {e}")
            return None
    
    def _get_obj_name(self, node):
        """Recursively get the full object name"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_obj_name(node.value)}.{node.attr}"
        else:
            return "unknown"
    
    def _extract_args(self, args):
        """Extract argument information"""
        arg_list = []
        for arg in args:
            if isinstance(arg, ast.Constant):
                arg_list.append(str(arg.value))
            elif isinstance(arg, ast.Name):
                arg_list.append(arg.id)
            else:
                arg_list.append("complex_arg")
        return arg_list
    
    def get_control_flow(self):
        """Extract control flow structures"""
        structures = []
        
        if self.tree:
            for node in ast.walk(self.tree):
                if isinstance(node, ast.For):
                    structures.append({
                        'type': 'for_loop',
                        'lineno': node.lineno,
                        'target': self._get_target_name(node.target)
                    })
                elif isinstance(node, ast.While):
                    structures.append({
                        'type': 'while_loop',
                        'lineno': node.lineno
                    })
                elif isinstance(node, ast.If):
                    structures.append({
                        'type': 'conditional',
                        'lineno': node.lineno
                    })
                elif isinstance(node, ast.With):
                    structures.append({
                        'type': 'context_manager',
                        'lineno': node.lineno
                    })
                elif isinstance(node, ast.Try):
                    structures.append({
                        'type': 'error_handling',
                        'lineno': node.lineno
                    })
        
        return structures
    
    def _get_target_name(self, node):
        """Get the target variable name"""
        if isinstance(node, ast.Name):
            return node.id
        else:
            return "unknown"
    
    def get_assignments(self):
        """Extract variable assignments"""
        assignments = []
        
        if self.tree:
            for node in ast.walk(self.tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            assignments.append({
                                'variable': target.id,
                                'lineno': node.lineno
                            })
        
        return assignments
    
    def tokenize_for_hmm(self):
        """Create token sequence for HMM processing"""
        tokens = []
        
        # Add import tokens
        for imp in self.get_imports():
            tokens.append('IMPORT')
            tokens.append(imp['module'])
        
        # Add function call tokens
        for call in self.get_function_calls():
            tokens.append('CALL')
            tokens.append(call['full_name'])
        
        # Add control flow tokens
        for struct in self.get_control_flow():
            tokens.append(struct['type'].upper())
        
        # Add assignment tokens
        for assign in self.get_assignments():
            tokens.append('ASSIGN')
        
        return tokens
    
    def get_code_summary(self):
        """Get a complete summary of the code structure"""
        return {
            'imports': self.get_imports(),
            'function_calls': self.get_function_calls(),
            'control_flow': self.get_control_flow(),
            'assignments': self.get_assignments(),
            'tokens': self.tokenize_for_hmm()
        }