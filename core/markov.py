import torch
import torch.nn as nn
import numpy as np

class HiddenMarkovModel:
    def __init__(self, observable_states, hidden_states, transition_matrix, emission_matrix):
        """
        Initialize Hidden Markov Model
        
        Args:
            observable_states: List of observable tokens (e.g., ['IMPORT', 'CALL', 'os.listdir'])
            hidden_states: List of intent states (e.g., ['FILE_OP', 'PROCESS_MGMT'])
            transition_matrix: State transition probabilities (hidden to hidden)
            emission_matrix: Emission probabilities (hidden to observable)
        """
        self.observable_states = observable_states if observable_states else []
        self.hidden_states = hidden_states if hidden_states else self._default_hidden_states()
        
        self.n_hidden = len(self.hidden_states)
        self.n_observable = len(self.observable_states) if self.observable_states else 0
        
        # Initialize matrices
        if transition_matrix is not None:
            self.transition = torch.tensor(transition_matrix, dtype=torch.float32)
        else:
            self.transition = self._default_transition_matrix()
        
        if emission_matrix is not None:
            self.emission = torch.tensor(emission_matrix, dtype=torch.float32)
        else:
            self.emission = None  # Will be computed dynamically
        
        # Initial state probabilities
        self.initial = torch.ones(self.n_hidden) / self.n_hidden
    
    def _default_hidden_states(self):
        """Define default intent states"""
        return [
            'FILE_OPERATION',
            'PROCESS_MANAGEMENT',
            'SYSTEM_INFO',
            'PATH_MANIPULATION',
            'ERROR_HANDLING',
            'DATA_PROCESSING',
            'INITIALIZATION'
        ]
    
    def _default_transition_matrix(self):
        """Create default transition matrix with reasonable probabilities"""
        n = self.n_hidden
        
        # Start with uniform + self-loop bias
        trans = torch.ones((n, n)) * 0.05
        
        # Add higher self-loop probabilities
        for i in range(n):
            trans[i, i] = 0.4
        
        # Define logical transitions (example patterns)
        state_map = {state: i for i, state in enumerate(self.hidden_states)}
        
        if 'INITIALIZATION' in state_map and 'FILE_OPERATION' in state_map:
            init_idx = state_map['INITIALIZATION']
            file_idx = state_map['FILE_OPERATION']
            trans[init_idx, file_idx] = 0.3
        
        if 'FILE_OPERATION' in state_map and 'ERROR_HANDLING' in state_map:
            file_idx = state_map['FILE_OPERATION']
            err_idx = state_map['ERROR_HANDLING']
            trans[file_idx, err_idx] = 0.15
        
        # Normalize rows
        trans = trans / trans.sum(dim=1, keepdim=True)
        
        return trans
    
    def viterbi(self, observations):
        """
        Viterbi algorithm to find most likely hidden state sequence
        
        Args:
            observations: List of observed tokens
        
        Returns:
            List of predicted hidden states
        """
        T = len(observations)
        
        if T == 0:
            return []
        
        # Initialize
        viterbi_matrix = torch.zeros((self.n_hidden, T))
        backpointer = torch.zeros((self.n_hidden, T), dtype=torch.long)
        
        # Get emission probabilities for first observation
        obs_idx = self._get_observation_index(observations[0])
        if obs_idx is not None:
            viterbi_matrix[:, 0] = self.initial * self._get_emission_probs(obs_idx)
        else:
            viterbi_matrix[:, 0] = self.initial
        
        # Forward pass
        for t in range(1, T):
            obs_idx = self._get_observation_index(observations[t])
            emission_probs = self._get_emission_probs(obs_idx)
            
            for s in range(self.n_hidden):
                # Calculate probability of being in state s at time t
                trans_probs = viterbi_matrix[:, t-1] * self.transition[:, s]
                viterbi_matrix[s, t] = torch.max(trans_probs) * emission_probs[s]
                backpointer[s, t] = torch.argmax(trans_probs)
        
        # Backtrack
        path = torch.zeros(T, dtype=torch.long)
        path[T-1] = torch.argmax(viterbi_matrix[:, T-1])
        
        for t in range(T-2, -1, -1):
            path[t] = backpointer[path[t+1], t+1]
        
        # Convert to state names
        return [self.hidden_states[int(idx)] for idx in path]
    
    def _get_observation_index(self, observation):
        """Map observation token to index"""
        if self.observable_states and observation in self.observable_states:
            return self.observable_states.index(observation)
        return None
    
    def _get_emission_probs(self, obs_idx):
        """Get emission probabilities for an observation"""
        if self.emission is not None and obs_idx is not None:
            return self.emission[:, obs_idx]
        else:
            # Use rule-based mapping if no emission matrix
            return self._rule_based_emission(obs_idx)
    
    def _rule_based_emission(self, obs_idx):
        """Rule-based emission probabilities based on token patterns"""
        probs = torch.ones(self.n_hidden) * 0.01  # Small baseline
        
        # This will be enhanced by pattern matching in the analyzer
        return probs / probs.sum()
    
    def predict_intent(self, tokens):
        """
        Predict intent states from token sequence
        
        Args:
            tokens: List of code tokens
        
        Returns:
            Dict with state sequence and summary
        """
        if not tokens:
            return {
                'states': [],
                'summary': 'No code tokens found'
            }
        
        # Map tokens to observable states or use direct tokens
        observations = self._map_tokens_to_observations(tokens)
        
        # Get state sequence
        state_sequence = self.viterbi(observations)
        
        # Generate summary
        summary = self._generate_state_summary(state_sequence)
        
        return {
            'states': state_sequence,
            'summary': summary,
            'tokens': tokens,
            'dominant_state': self._get_dominant_state(state_sequence)
        }
    
    def _map_tokens_to_observations(self, tokens):
        """Map code tokens to observation space"""
        mapped = []
        
        for token in tokens:
            # Use pattern matching to categorize tokens
            if 'os.' in token.lower():
                if any(x in token.lower() for x in ['listdir', 'walk', 'scandir', 'mkdir', 'remove']):
                    mapped.append('FILE_OP_TOKEN')
                elif any(x in token.lower() for x in ['getpid', 'getcwd', 'getenv']):
                    mapped.append('SYSTEM_INFO_TOKEN')
                elif any(x in token.lower() for x in ['path.join', 'path.exists', 'path.dirname']):
                    mapped.append('PATH_TOKEN')
                else:
                    mapped.append(token)
            else:
                mapped.append(token)
        
        return mapped
    
    def _generate_state_summary(self, state_sequence):
        """Generate human-readable summary of state sequence"""
        if not state_sequence:
            return "No states detected"
        
        # Count state occurrences
        state_counts = {}
        for state in state_sequence:
            state_counts[state] = state_counts.get(state, 0) + 1
        
        # Find dominant state
        dominant = max(state_counts, key=state_counts.get)
        
        summary = f"Primary intent: {dominant.replace('_', ' ').title()}\n"
        summary += f"Total operations: {len(state_sequence)}\n"
        summary += f"State transitions: {len(set(state_sequence))}"
        
        return summary
    
    def _get_dominant_state(self, state_sequence):
        """Get the most frequent state"""
        if not state_sequence:
            return None
        
        state_counts = {}
        for state in state_sequence:
            state_counts[state] = state_counts.get(state, 0) + 1
        
        return max(state_counts, key=state_counts.get)