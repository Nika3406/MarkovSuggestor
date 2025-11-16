class PseudocodeGenerator:
    def __init__(self, embedder=None):
        """
        Initialize pseudocode generator
        
        Args:
            embedder: FunctionEmbedder instance for semantic matching
        """
        self.embedder = embedder
        self.step_counter = 0
    
    def generate_explanation(self, code_summary, hmm_result, original_code):
        """
        Generate complete pseudocode explanation
        
        Args:
            code_summary: Output from FileManager.get_code_summary()
            hmm_result: Output from HMM.predict_intent()
            original_code: Original source code string
        
        Returns:
            Formatted explanation string
        """
        self.step_counter = 0
        
        explanation = []
        explanation.append("=" * 80)
        explanation.append("CODE EXPLANATION")
        explanation.append("=" * 80)
        explanation.append("")
        
        # Add original code
        explanation.append("ORIGINAL CODE:")
        explanation.append("-" * 80)
        explanation.append(original_code)
        explanation.append("")
        
        # Add HMM intent analysis
        explanation.append("INTENT ANALYSIS:")
        explanation.append("-" * 80)
        explanation.append(hmm_result['summary'])
        explanation.append(f"Dominant Pattern: {hmm_result.get('dominant_state', 'Unknown')}")
        explanation.append("")
        
        # Generate pseudocode
        explanation.append("PSEUDOCODE TRANSLATION:")
        explanation.append("-" * 80)
        
        pseudocode_steps = self._generate_pseudocode_steps(code_summary, hmm_result)
        explanation.extend(pseudocode_steps)
        explanation.append("")
        
        # Add algorithm summary
        explanation.append("ALGORITHM SUMMARY:")
        explanation.append("-" * 80)
        algorithm_summary = self._generate_algorithm_summary(code_summary, hmm_result)
        explanation.extend(algorithm_summary)
        explanation.append("")
        
        explanation.append("=" * 80)
        
        return "\n".join(explanation)
    
    def _generate_pseudocode_steps(self, code_summary, hmm_result):
        """Generate step-by-step pseudocode"""
        steps = []
        
        # Process imports
        if code_summary['imports']:
            for imp in code_summary['imports']:
                step = self._get_next_step()
                if imp['type'] == 'import':
                    steps.append(f"{step} Import {imp['module']} module for system operations")
                else:
                    steps.append(f"{step} Import {imp['name']} from {imp['module']}")
        
        # Process assignments and function calls together (in execution order)
        all_operations = []
        
        # Collect all operations with line numbers
        for call in code_summary['function_calls']:
            all_operations.append(('call', call))
        
        for assign in code_summary['assignments']:
            all_operations.append(('assign', assign))
        
        for struct in code_summary['control_flow']:
            all_operations.append(('control', struct))
        
        # Sort by line number
        all_operations.sort(key=lambda x: x[1].get('lineno', 0))
        
        # Generate steps for each operation
        indent_level = 0
        for op_type, op_data in all_operations:
            if op_type == 'call':
                step = self._generate_function_call_step(op_data, indent_level)
                steps.append(step)
            elif op_type == 'assign':
                step = self._generate_assignment_step(op_data, indent_level)
                steps.append(step)
            elif op_type == 'control':
                step, indent_change = self._generate_control_flow_step(op_data, indent_level)
                steps.append(step)
                indent_level += indent_change
        
        return steps
    
    def _generate_function_call_step(self, call_info, indent_level):
        """Generate pseudocode for a function call"""
        indent = "    " * indent_level
        step = self._get_next_step()
        
        full_name = call_info['full_name']
        args = call_info.get('args', [])
        
        # Try to get semantic description from embedder
        description = None
        if self.embedder:
            match = self.embedder.match_function_call(call_info)
            if match and match['similarity'] > 0.5:
                description = match['function']['description']
        
        # Generate step based on function pattern
        if description:
            # Use semantic description (first sentence only)
            desc_short = description.split('.')[0]
            return f"{indent}{step} {desc_short}"
        else:
            # Use pattern-based description
            return f"{indent}{step} {self._pattern_based_description(full_name, args)}"
    
    def _pattern_based_description(self, func_name, args):
        """Generate description based on function name patterns"""
        name_lower = func_name.lower()
        
        # OS module patterns
        if 'os.listdir' in name_lower:
            return f"Get list of all files and directories in {args[0] if args else 'specified path'}"
        elif 'os.getcwd' in name_lower:
            return "Get the current working directory path"
        elif 'os.path.join' in name_lower:
            return f"Combine path components: {', '.join(args)}"
        elif 'os.path.exists' in name_lower:
            return f"Check if path {args[0] if args else 'specified'} exists"
        elif 'os.path.isdir' in name_lower:
            return f"Check if {args[0] if args else 'path'} is a directory"
        elif 'os.path.isfile' in name_lower:
            return f"Check if {args[0] if args else 'path'} is a file"
        elif 'os.mkdir' in name_lower:
            return f"Create directory {args[0] if args else 'at specified path'}"
        elif 'os.remove' in name_lower:
            return f"Delete file {args[0] if args else 'at specified path'}"
        elif 'os.walk' in name_lower:
            return f"Traverse directory tree starting from {args[0] if args else 'root'}"
        
        # File operations
        elif 'open' in name_lower:
            return f"Open file {args[0] if args else 'specified'}"
        elif 'read' in name_lower:
            return "Read content from file"
        elif 'write' in name_lower:
            return "Write data to file"
        elif 'close' in name_lower:
            return "Close file handle"
        
        # Print/output
        elif 'print' in name_lower:
            return f"Display output: {args[0] if args else 'result'}"
        
        # Generic
        else:
            return f"Call function {func_name}" + (f" with arguments {', '.join(args)}" if args else "")
    
    def _generate_assignment_step(self, assign_info, indent_level):
        """Generate pseudocode for an assignment"""
        indent = "    " * indent_level
        step = self._get_next_step()
        
        var_name = assign_info['variable']
        return f"{indent}{step} Store result in variable '{var_name}'"
    
    def _generate_control_flow_step(self, struct_info, indent_level):
        """Generate pseudocode for control flow structures"""
        indent = "    " * indent_level
        step = self._get_next_step()
        
        struct_type = struct_info['type']
        
        if struct_type == 'for_loop':
            target = struct_info.get('target', 'item')
            step_text = f"{indent}{step} For each {target} in collection:"
            return step_text, 1  # Increase indent for loop body
        
        elif struct_type == 'while_loop':
            step_text = f"{indent}{step} While condition is true:"
            return step_text, 1
        
        elif struct_type == 'conditional':
            step_text = f"{indent}{step} If condition is met:"
            return step_text, 1
        
        elif struct_type == 'context_manager':
            step_text = f"{indent}{step} Open resource context (auto-cleanup):"
            return step_text, 1
        
        elif struct_type == 'error_handling':
            step_text = f"{indent}{step} Try to execute with error handling:"
            return step_text, 1
        
        else:
            return f"{indent}{step} Execute {struct_type}", 0
    
    def _generate_algorithm_summary(self, code_summary, hmm_result):
        """Generate high-level algorithm summary"""
        summary = []
        
        # Determine algorithm pattern
        dominant_state = hmm_result.get('dominant_state', 'UNKNOWN')
        
        if dominant_state == 'FILE_OPERATION':
            summary.append("Pattern: File System Operations")
            summary.append("Purpose: Interact with files and directories")
        elif dominant_state == 'PROCESS_MANAGEMENT':
            summary.append("Pattern: Process Control")
            summary.append("Purpose: Manage system processes")
        elif dominant_state == 'SYSTEM_INFO':
            summary.append("Pattern: System Information Retrieval")
            summary.append("Purpose: Query system state and properties")
        elif dominant_state == 'PATH_MANIPULATION':
            summary.append("Pattern: Path Operations")
            summary.append("Purpose: Manipulate file system paths")
        elif dominant_state == 'DATA_PROCESSING':
            summary.append("Pattern: Data Processing")
            summary.append("Purpose: Transform and analyze data")
        else:
            summary.append("Pattern: General Operations")
            summary.append("Purpose: Mixed system operations")
        
        # Add complexity estimate
        num_operations = len(code_summary['function_calls'])
        num_loops = len([s for s in code_summary['control_flow'] if 'loop' in s['type']])
        
        if num_loops > 0:
            summary.append(f"Complexity: O(n) or higher - contains {num_loops} loop(s)")
        else:
            summary.append(f"Complexity: O(1) - {num_operations} sequential operation(s)")
        
        # Add key operations
        if code_summary['function_calls']:
            key_funcs = [call['full_name'] for call in code_summary['function_calls'][:3]]
            summary.append(f"Key Operations: {', '.join(key_funcs)}")
        
        return summary
    
    def _get_next_step(self):
        """Get next step number"""
        self.step_counter += 1
        return f"Step {self.step_counter}:"