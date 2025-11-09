import os
from file_manager import FileManager
from markov import HiddenMarkovModel

# Reading input Python file (obserable state)
PATH = os.path.dirname(__file__)
INPUT_FILE = PATH + '/sample_projects/project1/main.py'

with open(INPUT_FILE, 'r') as file:
    python_file = file.read()

observable_states = FileManager(python_file)

# Calculating hidden states
hidden_states = HiddenMarkovModel.emit(observable_states)

# Calculating prediction
prediction = HiddenMarkovModel.transform(hidden_states)

# TODO: Replace with code suggestion GUI
print(prediction)