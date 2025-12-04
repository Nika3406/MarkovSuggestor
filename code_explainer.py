"""
CodeExplainer - Bridge version that delegates heavy work to external venv
Python 3.3 compatible (no f-strings, no subprocess.run)
"""

import os
import sys
import subprocess
import time
import json

# Path to external venv (same as CodeSuggester)
VENV_PYTHON = "/Users/zurabishvelidze/Desktop/venv1/bin/python3.11"

plugin_dir = os.path.dirname(os.path.abspath(__file__))


class CodeExplainerBridge(object):
    """
    Lightweight front-end that sends all heavy tasks (HMM, embedder,
    code parsing, etc.) to venv1, just like CodeSuggester.
    """

    ###########################################################################
    # INTERNAL PROCESS CALLER — IDENTICAL TO CodeSuggester.call_venv_script()
    ###########################################################################
    def _call_venv(self, script_code, timeout=10):
        """Execute code inside venv1 and return stdout (Python 3.3 safe)."""
        try:
            process = subprocess.Popen(
                [VENV_PYTHON, "-c", script_code],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=plugin_dir
            )

            start = time.time()
            while process.poll() is None:
                if time.time() - start > timeout:
                    process.kill()
                    return "ERROR: venv timeout"
                time.sleep(0.1)

            stdout, stderr = process.communicate()
            out = stdout.decode("utf-8", "ignore")
            err = stderr.decode("utf-8", "ignore")

            if process.returncode == 0:
                return out.strip()
            else:
                return "ERROR:\n" + err + "\n" + out

        except Exception as e:
            return "ERROR calling venv: " + str(e)

    ###########################################################################
    # PUBLIC API: explain_code()
    # This now only sends the code to venv1 where real CodeExplainer runs.
    ###########################################################################
    def explain_code(self, code_string):
        """Send code to real CodeExplainer inside venv1."""
        # Escape string for Python -c
        safe = code_string.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")

        script = """
import sys
sys.path.insert(0, '{plugin_dir}')

# Load heavy modules IN THE VENV ONLY
from code_explainer_heavy import CodeExplainer as RealExplainer

code = "{safe}"
ex = RealExplainer()
result = ex.explain_code(code)
print(result)
""".format(plugin_dir=plugin_dir, safe=safe)

        return self._call_venv(script, timeout=25)


###############################################################################
# BACKWARD COMPATIBILITY: maintain old class name
###############################################################################
class CodeExplainer(CodeExplainerBridge):
    pass
