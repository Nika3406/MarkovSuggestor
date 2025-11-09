from enum import Enum
from file_manager import FileManager

class HiddenStates(Enum):
    IMPORT = 1
    OPEN = 2
    BOUNDS = 3
    INPUT = 4
    GENERATE = 5
    UNKNOWN = 6

class HiddenMarkovModel:
    def emit(file_manager: FileManager):
        """Emits the obserable states into hidden states

        Args: 
            state (FileManager): The current file state in the Hidden Markov Model
        """
        # NOTE: Was going to use the following code to figure out hidden states
        #       Due to the complexitity of the task, I am temporarly scrapping
        #       this idea and may return to it later if we have enough time

        # for line_number in file_manager.num_of_lines():
        #     functions_used = file_manager.get_functions_used(line_number)
        #     strings = file_manager.get_strings(line_number)
        #     variables = file_manager.get_variables(line_number)
        #     types = file_manager.get_types(line_number)


        # FIXME: This code is not how your suppose to emit, only
        #       using it to get something working temporarly
        meanings = []

        for line in file_manager.get_lines():
            if len(line) == 0:
                continue
            elif line[0] == '#':
                continue
            elif 'import' in line:
                meaning = HiddenStates.IMPORT
            elif 'open' in line:
                meaning = HiddenStates.OPEN
            elif 'bound' in line:
                meaning = HiddenStates.BOUNDS
            elif 'input' in line:
                meaning = HiddenStates.INPUT
            else:
                meaning = HiddenStates.UNKNOWN

            meanings.append(meaning)

        return meanings


    def transform(hidden_state):
        """Transforms the hidden state into a observation
        
        Returns:
            observation (string): The output observation of the Hidden Markov Model
        """
        pass
    