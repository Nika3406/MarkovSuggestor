"""
Code explanation module using HMM analysis and function embeddings.
"""

import os
import sys
import re
from collections import defaultdict

# Add parent directory to path for imports
plugin_dir = os.path.dirname(os.path.abspath(__file__))
if plugin_dir not in sys.path:
    sys.path.append(plugin_dir)

try:
    from embedder import FunctionEmbedder
except ImportError:
    FunctionEmbedder = None

try:
    from markov import HiddenMarkovModel
    from observer import observe_lines, HiddenStates
except ImportError:
    HiddenMarkovModel = None
    observe_lines = None
    HiddenStates = None


class CodeExplainer:
    """Explains Python code using HMM and semantic analysis"""

    def __init__(self):
        self.embedder = None
        if FunctionEmbedder:
            self.embedder = FunctionEmbedder()
            db_path = os.path.join(plugin_dir, 'os_function_database.json')
            if os.path.exists(db_path):
                self.embedder.load_database(db_path)

    def explain_code(self, code):
        """Generate a human-readable explanation of the code"""

        explanation_parts = []

        # Header
        explanation_parts.append("=" * 80)
        explanation_parts.append("CODE EXPLANATION")
        explanation_parts.append("=" * 80)
        explanation_parts.append("")

        # 1. Basic Structure Analysis
        explanation_parts.append("STRUCTURE ANALYSIS:")
        explanation_parts.append("-" * 80)
        structure = self._analyze_structure(code)
        explanation_parts.append(structure)
        explanation_parts.append("")

        # 2. Pseudocode Translation
        explanation_parts.append("PSEUDOCODE:")
        explanation_parts.append("-" * 80)
        pseudocode = self._generate_pseudocode(code)
        explanation_parts.append(pseudocode)
        explanation_parts.append("")

        # 3. HMM State Analysis (if available)
        if HiddenMarkovModel and observe_lines:
            explanation_parts.append("INTENT ANALYSIS (Hidden Markov Model):")
            explanation_parts.append("-" * 80)
            hmm_analysis = self._analyze_with_hmm(code)
            explanation_parts.append(hmm_analysis)
            explanation_parts.append("")

        # 4. Function Analysis
        if self.embedder:
            explanation_parts.append("DETECTED FUNCTIONS:")
            explanation_parts.append("-" * 80)
            func_analysis = self._analyze_functions(code)
            explanation_parts.append(func_analysis)
            explanation_parts.append("")

        # 5. Complexity & Algorithm Detection
        explanation_parts.append("ALGORITHM & COMPLEXITY:")
        explanation_parts.append("-" * 80)
        complexity = self._analyze_complexity(code)
        explanation_parts.append(complexity)
        explanation_parts.append("")

        return "\n".join(explanation_parts)

    def _analyze_structure(self, code):
        """Analyze basic code structure"""
        lines = code.strip().split('\n')
        non_empty = [l for l in lines if l.strip() and not l.strip().startswith('#')]

        imports = [l for l in lines if 'import' in l]
        functions = [l for l in lines if l.strip().startswith('def ')]
        classes = [l for l in lines if l.strip().startswith('class ')]

        analysis = []
        analysis.append("Total lines: {}".format(len(lines)))
        analysis.append("Code lines: {}".format(len(non_empty)))
        analysis.append("Imports: {}".format(len(imports)))
        analysis.append("Functions defined: {}".format(len(functions)))
        analysis.append("Classes defined: {}".format(len(classes)))

        if imports:
            analysis.append("\nImported modules:")
            for imp in imports[:5]:  # Show first 5
                analysis.append("  • {}".format(imp.strip()))

        return "\n".join(analysis)

    def _generate_pseudocode(self, code):
        """Convert code to readable pseudocode"""
        lines = code.strip().split('\n')
        pseudocode = []

        indent_level = 0

        for line in lines:
            stripped = line.strip()

            # Skip empty lines and comments
            if not stripped or stripped.startswith('#'):
                continue

            # Calculate indent
            indent = len(line) - len(line.lstrip())
            indent_level = indent // 4
            prefix = "  " * indent_level

            # Translate common patterns
            if 'import' in stripped:
                pseudocode.append(
                    "{}IMPORT {}".format(
                        prefix,
                        stripped.split('import')[1].strip()
                    )
                )

            elif stripped.startswith('def '):
                func_name = stripped.split('(')[0].replace('def ', '')
                pseudocode.append(
                    "{}DEFINE function {}".format(prefix, func_name)
                )

            elif stripped.startswith('class '):
                class_name = stripped.split(':')[0].replace('class ', '')
                pseudocode.append(
                    "{}DEFINE class {}".format(prefix, class_name)
                )

            elif stripped.startswith('for '):
                pseudocode.append(
                    "{}FOR EACH {}".format(
                        prefix,
                        stripped.split('for')[1].split(':')[0].strip()
                    )
                )

            elif stripped.startswith('while '):
                condition = stripped.split('while')[1].split(':')[0].strip()
                pseudocode.append(
                    "{}WHILE {}".format(prefix, condition)
                )

            elif stripped.startswith('if '):
                condition = stripped.split('if')[1].split(':')[0].strip()
                pseudocode.append(
                    "{}IF {}".format(prefix, condition)
                )

            elif stripped.startswith('elif '):
                condition = stripped.split('elif')[1].split(':')[0].strip()
                pseudocode.append(
                    "{}ELSE IF {}".format(prefix, condition)
                )

            elif stripped.startswith('else:'):
                pseudocode.append("{}ELSE".format(prefix))

            elif stripped.startswith('return '):
                value = stripped.replace('return ', '')
                pseudocode.append(
                    "{}RETURN {}".format(prefix, value)
                )

            elif stripped.startswith('print('):
                pseudocode.append(
                    "{}OUTPUT {}".format(prefix, stripped)
                )

            elif '=' in stripped and not stripped.startswith('=='):
                var = stripped.split('=')[0].strip()
                pseudocode.append(
                    "{}SET {} to calculated value".format(prefix, var)
                )

            else:
                # Generic action
                pseudocode.append(
                    "{}EXECUTE: {}".format(prefix, stripped[:50])
                )

        return "\n".join(pseudocode) if pseudocode else "No executable code found"

    def _analyze_with_hmm(self, code):
        """Analyze code intent using Hidden Markov Model"""
        try:
            lines = code.strip().split('\n')
            observed = observe_lines(lines)

            if not observed:
                return "No observable patterns detected"

            # Get hidden states
            from observer import emission_probabilities, transition_probabilities
            hidden = HiddenMarkovModel.emit(
                observed,
                emission_probabilities,
                transition_probabilities
            )

            analysis = []
            analysis.append("Detected Intent States:")

            # Count state frequencies
            state_counts = defaultdict(int)
            for state in hidden:
                state_counts[state] += 1

            for state, count in sorted(
                state_counts.items(),
                key=lambda x: -x[1]
            ):
                analysis.append("  • {}: {} occurrences".format(state, count))

            # Predict next action
            if hidden:
                suggestion = HiddenMarkovModel.transform(hidden)
                analysis.append(
                    "\nSuggested next functions: {}".format(suggestion)
                )

            return "\n".join(analysis)

        except Exception as e:
            return "HMM analysis error: {}".format(str(e))

    def _analyze_functions(self, code):
        """Analyze functions used in the code"""
        try:
            # Find function calls like os.path.join(), random.randint(), etc.
            func_pattern = r'([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)\s*\('
            matches = re.findall(func_pattern, code)

            if not matches:
                return "No function calls detected"

            analysis = []
            unique_funcs = list(set(matches))[:10]  # Limit to 10

            for func in unique_funcs:
                analysis.append("\n• {}()".format(func))

                # Try to get info from embedder
                if self.embedder and '.' in func:
                    try:
                        results = self.embedder.find_similar_functions(
                            func,
                            top_k=1
                        )
                        if results and results[0]['similarity'] > 0.7:
                            desc = results[0]['function'].get(
                                'description',
                                ''
                            )
                            # Get first line of description
                            if desc:
                                first_line = desc.split('\n')[0]
                            else:
                                first_line = 'No description'
                            analysis.append(
                                "  {}".format(first_line[:80])
                            )
                    except Exception:
                        pass

            return "\n".join(analysis)

        except Exception as e:
            return "Function analysis error: {}".format(str(e))

    def _analyze_complexity(self, code):
        """Detect algorithms and estimate complexity"""
        analysis = []

        # Detect common patterns
        has_loops = 'for ' in code or 'while ' in code
        has_nested_loops = code.count('for ') > 1 or code.count('while ') > 1
        has_recursion = 'def ' in code and any(
            func_name in code[code.index('def '):]
            for func_name in re.findall(r'def\s+(\w+)', code)
        )

        # Algorithm patterns
        algorithms = []
        if 'sort' in code.lower():
            algorithms.append("Sorting algorithm detected")
        if 'search' in code.lower() or 'find' in code.lower():
            algorithms.append("Search pattern detected")
        if has_recursion:
            algorithms.append("Recursive approach detected")
        if 'enumerate' in code or 'range' in code:
            algorithms.append("Iteration pattern detected")

        # Complexity estimate
        if has_nested_loops:
            complexity = "O(n²) or higher - Nested iterations detected"
        elif has_loops:
            complexity = "O(n) - Single loop iteration"
        elif has_recursion:
            complexity = (
                "Depends on recursion depth (possibly O(2^n) or O(n log n))"
            )
        else:
            complexity = "O(1) - Constant time operations"

        if algorithms:
            analysis.append("Detected Patterns:")
            for alg in algorithms:
                analysis.append("  • {}".format(alg))
            analysis.append("")

        analysis.append(
            "Estimated Time Complexity: {}".format(complexity)
        )

        return "\n".join(analysis)
