import os
from file_manager import FileManager
from markov import HiddenMarkovModel
from observer import observe_lines, emission_probabilities

# Reading input Python file (obserable state)
PATH = os.path.dirname(__file__)
INPUT_FILE_PATH = PATH + '/sample_projects/project1/main.py'

observable_states = FileManager(INPUT_FILE_PATH)

observable_lines = observable_states.get_lines()

observed_lines = observe_lines(observable_lines)

print("Observed lines:", observed_lines)

# Calculating hidden states
hidden_states = HiddenMarkovModel.emit(observed_lines, emission_probabilities)
print("Hidden states:", hidden_states)

# Calculating prediction
prediction = HiddenMarkovModel.transform(hidden_states)
print("Next hidden state:", prediction)