from enum import Enum
from copy import deepcopy

class Observations(Enum):
    IMPORT = 1
    OPEN = 2
    BOUNDS = 3
    INPUT = 4
    GENERATE = 5
    UNKNOWN = 6

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