from file_manager import FileManager

class HiddenMarkovModel:
    def emit(observations: list, emissions, transitions):
        """Emits the obserable states into hidden states

        Args: 
            state (FileManager): The current file state in the Hidden Markov Model
        """
        # Calculate initial hidden state
        hidden_states_probabilities = []
        for hidden_state in emissions[1:]:
            curr_probability = 1
            for observation in observations[0]:
                curr_probability *= hidden_state[observation]
            hidden_states_probabilities.append(curr_probability)

        max_index = HiddenMarkovModel._get_max_index(hidden_states_probabilities)
        previous_hidden_states = [emissions[0][max_index]]
        #TODO: Need to finish the continuation of emit after initial hidden state

        for i in range(1, len(observations) - 1):
            hidden_states_probabilities = []
            for hidden_state in emissions[1:]:
                curr_probability = 1
                for observation in observations[i]:
                    curr_probability *= hidden_state[observation]
                prev = previous_hidden_states[-1]
                prev_indx = emissions[0].index(prev)
                transitions[prev_indx+1]
                hidden_states_probabilities.append(curr_probability)

    def transform(hidden_state):
        """Transforms the hidden state into a observation
        
        Returns:
            observation (string): The output observation of the Hidden Markov Model
        """
        pass

    def _get_max_index(values):
        curr_max = values[0]
        max_indx = 0

        for i, value in enumerate(values):
            if value > curr_max:
                curr_max = value
                max_indx = i
        
        return max_indx
