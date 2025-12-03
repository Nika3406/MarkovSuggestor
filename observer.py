from enum import Enum
from copy import deepcopy
import re
from collections import defaultdict, Counter

class Observations(Enum):
    IMPORT = "IMPORT"
    OPEN = "OPEN"
    INPUT = "INPUT"
    BOUNDS = "BOUNDS"
    GENERATE = "GENERATE"
    UNKNOWN = "UNKNOWN"
    FUNC_CALL = "FUNC_CALL"  # function call observation

class HiddenStates(Enum):
    IMPORT = "IMPORT"
    GET_INPUT = "GET_INPUT"
    GET_BOUNDS = "GET_BOUNDS"

# Emission probabilities: labels in emissions[0], then maps mapping string tokens to probabilities
emission_probabilities = [
    [HiddenStates.IMPORT, HiddenStates.GET_INPUT, HiddenStates.GET_BOUNDS], # Labels

    # For IMPORT state
    { "IMPORT" : 0.9, "OPEN" : 0.2, "INPUT" : 0.2, "BOUNDS" : 0.1, "GENERATE" : 0.2, "UNKNOWN" : 0.1 },

    # For GET_INPUT state
    { "IMPORT" : 0.1, "OPEN" : 0.2, "INPUT" : 0.9, "BOUNDS" : 0.1, "GENERATE" : 0.1, "UNKNOWN" : 0.1 },

    # For GET_BOUNDS state
    { "IMPORT" : 0.1, "OPEN" : 0.2, "INPUT" : 0.8, "BOUNDS" : 0.9, "GENERATE" : 0.1, "UNKNOWN" : 0.1 },
]

transition_probabilities = [
    [HiddenStates.IMPORT, HiddenStates.GET_INPUT, HiddenStates.GET_BOUNDS], # Labels

    # From IMPORT
    { HiddenStates.IMPORT.value : 0.9, HiddenStates.GET_INPUT.value : 0.2, HiddenStates.GET_BOUNDS.value : 0.2 },

    # From GET_INPUT
    { HiddenStates.IMPORT.value : 0.1, HiddenStates.GET_INPUT.value : 0.4, HiddenStates.GET_BOUNDS.value : 0.2 },

    # From GET_BOUNDS
    { HiddenStates.IMPORT.value : 0.1, HiddenStates.GET_INPUT.value : 0.2, HiddenStates.GET_BOUNDS.value : 0.4 },
]

# co-occurrence map: observed function -> Counter of next function suggestions
function_cooccurrence = defaultdict(Counter)

# tuning parameters
COOCCURRENCE_LEARNING_RATE = 0.1  # how much to bump co-occur counts when a pairing is observed
MIN_SUGGESTION_SCORE = 0.01       # floor to avoid zero probabilities

FUNC_CALL_RE = re.compile(r'([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+)\s*\(')

def observe_lines(lines):
    """
    Convert code lines into a list of observation-token lists.
    Tokens are simple strings like "IMPORT", "OPEN", "FUNC:os.listdir"
    """
    observed_lines = []

    for line in lines:
        observations = []

        if not line:
            continue
        line_stripped = line.strip()
        if not line_stripped:
            continue
        if line_stripped.startswith('#'):
            continue

        if 'import' in line:
            observations.append("IMPORT")
        if 'open' in line:
            observations.append("OPEN")
        if 'bound' in line:
            observations.append("BOUNDS")
        if 'input' in line:
            observations.append("INPUT")
        if 'generate' in line:
            observations.append("GENERATE")

        # detect dotted function calls like os.listdir(...)
        for m in FUNC_CALL_RE.finditer(line):
            func_name = m.group(1)  # e.g., os.listdir
            observations.append(f"FUNC:{func_name}")

        if len(observations) == 0:
            observations.append("UNKNOWN")

        observed_lines.append(deepcopy(observations))

    return observed_lines

def update_cooccurrence(prev_func, next_func, lr=COOCCURRENCE_LEARNING_RATE):
    """Incrementally update co-occurrence weights between functions."""
    if not prev_func or not next_func:
        return
    # store as plain string keys, accumulate fractional counts
    function_cooccurrence[prev_func][next_func] += lr

def get_cooccurrence_suggestions(prev_func, top_k=5):
    """Return top_k suggestions after prev_func based on cooccurrence weights."""
    if prev_func not in function_cooccurrence:
        return []
    counter = function_cooccurrence[prev_func]
    total = sum(counter.values()) + 1e-9
    ranked = counter.most_common(top_k)
    results = []
    for fn, count in ranked:
        score = max(count / total, MIN_SUGGESTION_SCORE)
        results.append({'function': fn, 'score': score})
    return results

def predict_next_functions(recent_tokens, top_k=5):
    """
    Given recent_tokens (list of strings, e.g., last observed tokens or function names),
    return a ranked list of function name suggestions using co-occurrence and heuristics.
    """
    # search for last FUNC:... token
    last_func = None
    for token in reversed(recent_tokens):
        if token.startswith("FUNC:"):
            last_func = token.split("FUNC:", 1)[1]
            break

    suggestions = []
    if last_func:
        suggestions = get_cooccurrence_suggestions(last_func, top_k=top_k)

    # fallback: if no cooccurrence data, suggest common built-ins or functions from observed tokens
    if not suggestions:
        # simple heuristics
        suggestions = [{'function': 'os.listdir', 'score': 0.2}, {'function': 'os.path.join', 'score': 0.15}]
    return suggestions

# Helper to simulate learning from an observed sequence of lines
def learn_from_observed_lines(observed_lines):
    """
    Walk observed_lines (list of token lists) and update function cooccurrences.
    When a FUNC:foo appears followed later by FUNC:bar within the next few lines,
    increment cooccurrence[foo][bar].
    """
    WINDOW = 3
    for i, obs in enumerate(observed_lines):
        funcs = [t.split("FUNC:",1)[1] for t in obs if t.startswith("FUNC:")]
        if not funcs:
            continue
        for func in funcs:
            # look ahead
            for j in range(i+1, min(i+1+WINDOW, len(observed_lines))):
                next_funcs = [t.split("FUNC:",1)[1] for t in observed_lines[j] if t.startswith("FUNC:")]
                for nf in next_funcs:
                    update_cooccurrence(func, nf)