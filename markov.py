from file_manager import FileManager
from observer import predict_next_functions, observe_lines

class HiddenMarkovModel:
    @staticmethod
    def emit(observations: list, emissions, transitions):
        """A simple emitter that (for now) returns a decoded sequence of hidden states.
        NOTE: This is a simplified version and intentionally lightweight. It computes
        the most likely hidden state per observation using emission probabilities and
        a simple transition bias when available.
        """
        if not observations:
            return []

        # observations: list of lists of observation tokens (strings)
        # emissions: list where emissions[0] = labels, emissions[1:] = maps from observation->prob
        labels = emissions[0]
        state_maps = emissions[1:]

        # for each observation set, compute score for each state
        hidden_seq = []
        prev_state_idx = None
        for obs in observations:
            best_idx = 0
            best_score = -1.0
            for idx, state_map in enumerate(state_maps):
                score = 1.0
                for o in obs:
                    # fall back to small positive epsilon if missing
                    score *= state_map.get(o, 0.01)
                # incorporate transition bias from prev state if available
                if prev_state_idx is not None and transitions:
                    # transitions[0] is labels, transitions[1:] are maps
                    try:
                        trans_map = transitions[prev_state_idx + 1]
                        # average transition probability to this label key
                        trans_prob = trans_map.get(labels[idx], 1.0)
                        score *= trans_prob
                    except Exception:
                        pass

                if score > best_score:
                    best_score = score
                    best_idx = idx

            hidden_seq.append(labels[best_idx])
            prev_state_idx = best_idx

        return hidden_seq

    @staticmethod
    def transform(hidden_state):
        """Transforms the final hidden state into a suggested observation.
        This is intentionally simple: use observer.predict_next_functions to suggest next functions.
        """
        # hidden_state: list of HiddenStates Enum values (or labels)
        if not hidden_state:
            return None

        # Use the last hidden state label to ask observer for likely next functions
        last = hidden_state[-1]
        # observer.predict_next_functions expects recent function names (strings)
        # but we can pass last as a string label
        suggestions = predict_next_functions([str(last)], top_k=3)
        return suggestions

    @staticmethod
    def _get_max_index(values):
        curr_max = values[0]
        max_indx = 0

        for i, value in enumerate(values):
            if value > curr_max:
                curr_max = value
                max_indx = i
        
        return max_indx