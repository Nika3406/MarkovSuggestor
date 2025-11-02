import os
from file_manager import FileManager
from markov import HiddenMarkovModel

OBSERVABLE = None
HIDDEN = None
TRANSFORMATION = None
EMISSION = None

PATH = os.path.dirname(__file__)
INPUT_FILE = PATH + '/sample_projects/project1/main.py'

hmm = HiddenMarkovModel(OBSERVABLE, HIDDEN, TRANSFORMATION, EMISSION)

with open(INPUT_FILE, 'r') as file:
    pythonFile = file.read()

python_file_manager = FileManager(pythonFile)
imports = python_file_manager.get_imports()