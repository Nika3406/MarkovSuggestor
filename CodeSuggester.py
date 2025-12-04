"""
CodeSuggester - Bridge version that uses external venv Python
Compatible with Sublime Text's Python 3.3
"""

import sublime
import sublime_plugin
import json
import os
import subprocess
import sys
import time

# Path to your venv Python
VENV_PYTHON = "/Users/zurabishvelidze/Desktop/venv1/bin/python3.11"

# Add package to path
plugin_dir = os.path.dirname(os.path.abspath(__file__))


class CodeSuggesterListener(sublime_plugin.EventListener):
    """Main listener for code suggestions"""
    
    def __init__(self):
        super(CodeSuggesterListener, self).__init__()
        self.database = None
        self.load_database()
    
    def load_database(self):
        """Load the embedding database (just the JSON, no Python execution needed)"""
        try:
            db_path = os.path.join(plugin_dir, "os_function_database.json")
            
            if os.path.exists(db_path):
                with open(db_path, 'r') as f:
                    self.database = json.load(f)
                print("CodeSuggester: Loaded {} functions".format(len(self.database.get('entries', []))))
            else:
                print("CodeSuggester: Database not found at {}".format(db_path))
        except Exception as e:
            print("CodeSuggester: Error loading database: {}".format(str(e)))
    
    def call_venv_script(self, script_code, timeout=5):
        """Execute Python code using venv and return the result"""
        try:
            # Use Popen instead of run (Python 3.3 compatible)
            process = subprocess.Popen(
                [VENV_PYTHON, "-c", script_code],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=plugin_dir
            )
            
            # Wait for process with timeout
            start_time = time.time()
            while process.poll() is None:
                if time.time() - start_time > timeout:
                    process.kill()
                    print("CodeSuggester: venv call timed out")
                    return None
                time.sleep(0.1)
            
            # Get output
            stdout, stderr = process.communicate()
            
            # Decode bytes to string (Python 3.3 compatible)
            stdout_str = stdout.decode('utf-8').strip()
            stderr_str = stderr.decode('utf-8')
            
            if process.returncode == 0:
                return stdout_str
            else:
                print("CodeSuggester venv error: {}".format(stderr_str))
                return None
                
        except Exception as e:
            print("CodeSuggester: venv call failed: {}".format(str(e)))
            return None
    
    def get_hmm_suggestions(self, lines):
        """Get suggestions from HMM using venv"""
        # Escape quotes in lines
        lines_str = repr(lines)
        
        script = """
import sys
sys.path.insert(0, '{}')
from markov import HiddenMarkovModel
from observer import observe_lines, emission_probabilities, transition_probabilities
import json

lines = {}
observed = observe_lines(lines)
if observed:
    hidden_states = HiddenMarkovModel.emit(observed, emission_probabilities, transition_probabilities)
    predicted = HiddenMarkovModel.transform(hidden_states)
    print(json.dumps(predicted if predicted else []))
else:
    print('[]')
""".format(plugin_dir, lines_str)
        
        result = self.call_venv_script(script, timeout=3)
        if result:
            try:
                return json.loads(result)
            except:
                return []
        return []
    
    def find_similar_functions(self, query, top_k=5):
        """Find similar functions using embedder via venv"""
        script = """
import sys
sys.path.insert(0, '{}')
from sublimePlugin.embedderSublime import FunctionEmbedder
import json

embedder = FunctionEmbedder()
db_path = '{}os_function_database.json'
if embedder.load_database(db_path):
    results = embedder.find_similar_functions('{}', top_k={})
    print(json.dumps(results))
else:
    print('[]')
""".format(plugin_dir, plugin_dir, query.replace("'", "\\'"), top_k)
        
        result = self.call_venv_script(script, timeout=5)
        if result:
            try:
                return json.loads(result)
            except:
                return []
        return []
    
    def on_query_completions(self, view, prefix, locations):
        """Provide code completions"""
        # Only for Python files
        if not view.match_selector(locations[0], "source.python"):
            return None
        
        if not self.database:
            return None
        
        suggestions = []
        
        try:
            # Get file content for HMM context
            file_content = view.substr(sublime.Region(0, view.size()))
            lines = file_content.split('\n')
            
            # Get HMM suggestions (runs in background, non-blocking)
            if len(lines) > 0:
                # Only use HMM for longer files to avoid delays
                if len(lines) > 5:
                    hmm_suggestions = self.get_hmm_suggestions(lines[-20:])
                    for pred in hmm_suggestions[:3]:
                        func_name = pred.get('function', '')
                        score = pred.get('score', 0)
                        if func_name:
                            suggestions.append((
                                "{}\tHMM: {:.2f}".format(func_name, score),
                                func_name
                            ))
            
            # Add simple prefix-based suggestions from database
            if prefix and len(prefix) > 1:
                # Simple string matching (no embeddings needed, fast)
                entries = self.database.get('entries', [])
                matches = []
                for entry in entries:
                    name = entry.get('name', '')
                    if name.lower().startswith(prefix.lower()):
                        matches.append(entry)
                
                # Add top 5 matches
                for entry in matches[:5]:
                    name = entry.get('name', '')
                    sig = entry.get('signature', '')
                    suggestions.append((
                        "{}\t{}".format(name, sig[:50]),
                        name
                    ))
            
            return suggestions if suggestions else None
            
        except Exception as e:
            print("CodeSuggester completion error: {}".format(str(e)))
            return None
    
    def on_hover(self, view, point, hover_zone):
        """Show function info on hover"""
        if hover_zone != sublime.HOVER_TEXT:
            return
        
        if not view.match_selector(point, "source.python"):
            return
        
        if not self.database:
            return
        
        try:
            # Get word under cursor
            word_region = view.word(point)
            word = view.substr(word_region)
            
            if len(word) < 2:
                return
            
            # Search database for exact or close match
            entries = self.database.get('entries', [])
            best_match = None
            
            for entry in entries:
                name = entry.get('name', '')
                if name == word or name.endswith('.' + word) or word in name:
                    best_match = entry
                    break
            
            if best_match:
                name = best_match.get('name', '')
                sig = best_match.get('signature', '')
                desc = best_match.get('description', '')[:300]
                
                # Build HTML popup
                html = """
                <body id="code-suggester-popup">
                    <style>
                        body {{
                            font-family: system;
                            margin: 10px;
                            padding: 10px;
                        }}
                        .function-name {{
                            font-weight: bold;
                            color: #569CD6;
                            font-size: 1.1em;
                        }}
                        .signature {{
                            color: #4EC9B0;
                            margin: 5px 0;
                        }}
                        .description {{
                            color: #D4D4D4;
                            margin-top: 10px;
                            white-space: pre-wrap;
                        }}
                    </style>
                    <div class="function-name">{}</div>
                    <div class="signature">{}</div>
                    <div class="description">{}</div>
                </body>
                """.format(name, sig, desc)
                
                view.show_popup(
                    html,
                    sublime.HIDE_ON_MOUSE_MOVE_AWAY,
                    point,
                    max_width=500
                )
        
        except Exception as e:
            print("CodeSuggester hover error: {}".format(str(e)))


class ExplainCodeCommand(sublime_plugin.TextCommand):
    """Command to explain selected code using venv"""
    
    def run(self, edit):
        print("CodeSuggester: ExplainCodeCommand.run() called!")
        
        # Get selection or entire file
        selection = self.view.sel()
        if selection and len(selection) > 0:
            region = selection[0]
            if not region.empty():
                code = self.view.substr(region)
                print("CodeSuggester: Explaining selected code ({} chars)".format(len(code)))
            else:
                code = self.view.substr(sublime.Region(0, self.view.size()))
                print("CodeSuggester: Explaining entire file ({} chars)".format(len(code)))
        else:
            code = self.view.substr(sublime.Region(0, self.view.size()))
            print("CodeSuggester: Explaining entire file ({} chars)".format(len(code)))
        
        if not code:
            sublime.status_message("No code to explain")
            print("CodeSuggester: No code to explain")
            return
        
        # Create the explanation window FIRST
        window = self.view.window()
        if not window:
            sublime.error_message("No window available")
            print("CodeSuggester: No window available")
            return
        
        # Create new view immediately
        explanation_view = window.new_file()
        explanation_view.set_name("Code Explanation - Processing...")
        explanation_view.set_scratch(True)
        explanation_view.run_command('append', {'characters': 'Analyzing your code, please wait...\n\n'})
        
        sublime.status_message("Analyzing code...")
        print("CodeSuggester: Starting async explanation...")
        
        # Run explanation in background
        sublime.set_timeout_async(lambda: self._explain_async(code, explanation_view), 0)
    
    def _explain_async(self, code, explanation_view):
        """Generate explanation asynchronously using venv"""
        print("CodeSuggester: _explain_async started")
        try:
            # Escape the code for passing to Python
            code_escaped = code.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
            
            script = """
import sys
sys.path.insert(0, '{}')

# Try to import code_explainer from different possible locations
try:
    from code_explainer import CodeExplainer
except ImportError:
    try:
        from sublimePlugin.code_explainer import CodeExplainer
    except ImportError:
        print("ERROR: Could not find code_explainer module")
        print("Searched in: {}")
        import os
        print("Files in plugin dir:", os.listdir('{}'))
        sys.exit(1)

code = \"\"\"{}\"\"\"
explainer = CodeExplainer()
explanation = explainer.explain_code(code)
print(explanation)
""".format(plugin_dir, plugin_dir, plugin_dir, code_escaped)
            
            print("CodeSuggester: Starting venv process...")
            
            # Use Popen instead of run (Python 3.3 compatible)
            process = subprocess.Popen(
                [VENV_PYTHON, "-c", script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=plugin_dir
            )
            
            # Wait for process with timeout
            start_time = time.time()
            timeout = 30
            while process.poll() is None:
                if time.time() - start_time > timeout:
                    process.kill()
                    print("CodeSuggester: Process timed out")
                    sublime.set_timeout(lambda: self._show_error(explanation_view, "Explanation timed out after 30 seconds"), 0)
                    return
                time.sleep(0.1)
            
            print("CodeSuggester: Process completed with returncode: {}".format(process.returncode))
            
            # Get output
            stdout, stderr = process.communicate()
            stdout_str = stdout.decode('utf-8')
            stderr_str = stderr.decode('utf-8')
            
            if process.returncode == 0:
                explanation = stdout_str
                print("CodeSuggester: Got explanation ({} chars)".format(len(explanation)))
                sublime.set_timeout(lambda: self._show_explanation(explanation_view, explanation), 0)
            else:
                # Combine stderr and stdout so we don't lose useful messages
                combined = ""
                if stderr_str.strip():
                    combined += stderr_str
                if stdout_str.strip():
                    if combined:
                        combined += "\n--- stdout ---\n"
                    combined += stdout_str

                error = combined.strip() if combined.strip() else "Unknown error (no output from venv process)"
                print("CodeSuggester: Error: {}".format(error))
                sublime.set_timeout(lambda: self._show_error(explanation_view, error), 0)

        except Exception as e:
            error_msg = "Error: {}".format(str(e))
            print("CodeSuggester: Exception: {}".format(error_msg))
            sublime.set_timeout(lambda: self._show_error(explanation_view, error_msg), 0)
    
    def _show_explanation(self, view, explanation):
        """Show explanation in the view"""
        print("CodeSuggester: Showing explanation")
        view.set_name("Code Explanation")
        view.set_read_only(False)
        # Clear the "processing" message
        view.run_command('select_all')
        view.run_command('left_delete')
        # Add the explanation
        view.run_command('append', {'characters': explanation})
        view.set_read_only(True)
        sublime.status_message("Explanation complete!")
    
    def _show_error(self, view, error):
        """Show error in the view"""
        print("CodeSuggester: Showing error")
        view.set_name("Code Explanation - Error")
        view.set_read_only(False)
        # Clear the "processing" message
        view.run_command('select_all')
        view.run_command('left_delete')
        # Add the error
        view.run_command('append', {'characters': 'Error generating explanation:\n\n{}'.format(error)})
        view.set_read_only(True)
        sublime.status_message("Explanation failed")
    
    def is_enabled(self):
        enabled = self.view.match_selector(0, "source.python")
        print("CodeSuggester: is_enabled() = {}".format(enabled))
        return enabled


class QuickTestVenvCommand(sublime_plugin.WindowCommand):
    """Quick test to verify venv connection"""
    
    def run(self):
        print("CodeSuggester: QuickTestVenvCommand.run() called!")
        script = """
import sys
print("Python:", sys.version)
print("Path:", sys.executable)

try:
    import sentence_transformers
    print("sentence_transformers: OK")
except:
    print("sentence_transformers: NOT FOUND")

try:
    import torch
    print("torch: OK")
except:
    print("torch: NOT FOUND")
"""
        
        try:
            # Use Popen instead of run (Python 3.3 compatible)
            process = subprocess.Popen(
                [VENV_PYTHON, "-c", script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for completion with timeout
            start_time = time.time()
            while process.poll() is None:
                if time.time() - start_time > 5:
                    process.kill()
                    sublime.error_message("Venv test timed out")
                    return
                time.sleep(0.1)
            
            stdout, stderr = process.communicate()
            result = stdout.decode('utf-8')
            
            sublime.message_dialog("Venv Test Result:\n\n{}".format(result))
        except Exception as e:
            sublime.error_message("Venv test failed: {}".format(str(e)))


def plugin_loaded():
    """Called when plugin loads"""
    print("CodeSuggester: Plugin loaded!")
    print("CodeSuggester: Using venv Python at: {}".format(VENV_PYTHON))
    print("CodeSuggester: Plugin directory: {}".format(plugin_dir))
    
    # Check database
    db_path = os.path.join(plugin_dir, "os_function_database.json")
    if not os.path.exists(db_path):
        print("CodeSuggester: Warning - Database not found at {}".format(db_path))
    else:
        print("CodeSuggester: Database found at {}".format(db_path))
    
    # Verify venv Python exists
    if not os.path.exists(VENV_PYTHON):
        print("CodeSuggester: ERROR - venv Python not found at {}".format(VENV_PYTHON))
    else:
        print("CodeSuggester: venv Python verified at {}".format(VENV_PYTHON))
    
    # Announce command registration
    print("CodeSuggester: Registered command 'explain_code'")
    print("CodeSuggester: Registered command 'quick_test_venv'")


def plugin_unloaded():
    """Called when plugin unloads"""
    print("CodeSuggester: Plugin unloaded")