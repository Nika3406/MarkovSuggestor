from enum import Enum
from copy import deepcopy

class Observations(Enum):
    IMPORT = 1
    OPEN = 2
    INPUT = 3
    BOUNDS = 4
    GENERATE = 5
    UNKNOWN = 6

class HiddenStates(Enum):
    IMPORT = 1
    GET_INPUT = 2
    GET_BOUNDS = 3

emission_probabilities = [
    [HiddenStates.IMPORT, HiddenStates.GET_INPUT, HiddenStates.GET_BOUNDS], # Labels

    {Observations.IMPORT : 0.9, Observations.OPEN : 0.2, Observations.INPUT : 0.2, 
     Observations.BOUNDS : 0.1, Observations.GENERATE : 0.2, Observations.UNKNOWN : 0.1},

    {Observations.IMPORT : 0.1, Observations.OPEN : 0.2, Observations.INPUT : 0.9, 
     Observations.BOUNDS : 0.1, Observations.GENERATE : 0.1, Observations.UNKNOWN : 0.1},

    {Observations.IMPORT : 0.1, Observations.OPEN : 0.2, Observations.INPUT : 0.8, 
     Observations.BOUNDS : 0.9, Observations.GENERATE : 0.1, Observations.UNKNOWN : 0.1},
]

transition_probabilities = [
    [HiddenStates.IMPORT, HiddenStates.GET_INPUT, HiddenStates.GET_BOUNDS], # Labels

    # From IMPORT
    {HiddenStates.IMPORT : 0.9, HiddenStates.GET_INPUT : 0.2, HiddenStates.GET_BOUNDS : 0.2},

    # From GET_INPUT
    {HiddenStates.IMPORT : 0.1, HiddenStates.GET_INPUT : 0.4, HiddenStates.GET_BOUNDS : 0.2},

    # From GET_BOUNDS
    {HiddenStates.IMPORT : 0.1, HiddenStates.GET_INPUT : 0.2, HiddenStates.GET_BOUNDS : 0.4},
]

def observe_lines(lines):
    observed_lines = []

    for line in lines:
        observations = []

        if len(line) == 0:
            continue
        elif line[0] == '#':
            continue
        if 'import' in line:
            observations.append(Observations.IMPORT)
        if 'open' in line:
            observations.append(Observations.OPEN)
        if 'bound' in line:
            observations.append(Observations.BOUNDS)
        if 'input' in line:
            observations.append(Observations.INPUT)
        if len(observations) == 0:
            observations.append(Observations.UNKNOWN)

        observed_lines.append(deepcopy(observations))

    return observed_lines