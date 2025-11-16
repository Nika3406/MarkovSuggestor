from file_manager import FileManager
from markov import HiddenMarkovModel
from embedder import FunctionEmbedder
from pseudocode_generator import PseudocodeGenerator
import os

class CodeExplainer:
    def __init__(self, database_path='os_function_database.json'):
        """
        Initialize the complete code explanation pipeline
        
        Args:
            database_path: Path to pre-built function database
        """
        print("Initializing Code Explainer...")
        
        # Initialize embedder
        self.embedder = FunctionEmbedder()
        
        # Try to load existing database
        if os.path.exists(database_path):
            self.embedder.load_database(database_path)
        else:
            print(f"Warning: Database {database_path} not found")
            print("Run embedder.py first to build the database")
        
        # Initialize HMM
        self.hmm = HiddenMarkovModel(
            observable_states=None,
            hidden_states=None,
            transition_matrix=None,
            emission_matrix=None
        )
        
        # Initialize pseudocode generator
        self.generator = PseudocodeGenerator(embedder=self.embedder)
        
        print("✓ Code Explainer ready!")
    
    def explain_code(self, code_string):
        """
        Complete pipeline to explain Python code
        
        Args:
            code_string: Python source code as string
        
        Returns:
            Formatted explanation string
        """
        print("\n" + "="*60)
        print("ANALYZING CODE...")
        print("="*60)
        
        # Step 1: Parse code
        print("\n[1/4] Parsing code structure...")
        file_manager = FileManager(code_string)
        code_summary = file_manager.get_code_summary()
        
        print(f"  ✓ Found {len(code_summary['imports'])} imports")
        print(f"  ✓ Found {len(code_summary['function_calls'])} function calls")
        print(f"  ✓ Found {len(code_summary['control_flow'])} control structures")
        
        # Step 2: HMM intent analysis
        print("\n[2/4] Analyzing code intent with HMM...")
        tokens = code_summary['tokens']
        hmm_result = self.hmm.predict_intent(tokens)
        
        print(f"  ✓ Dominant intent: {hmm_result.get('dominant_state', 'Unknown')}")
        
        # Step 3: Match functions semantically
        print("\n[3/4] Matching functions with semantic embeddings...")
        matched_count = 0
        for call in code_summary['function_calls']:
            match = self.embedder.match_function_call(call)
            if match and match['similarity'] > 0.5:
                matched_count += 1
        
        print(f"  ✓ Matched {matched_count}/{len(code_summary['function_calls'])} functions")
        
        # Step 4: Generate explanation
        print("\n[4/4] Generating pseudocode explanation...")
        explanation = self.generator.generate_explanation(
            code_summary,
            hmm_result,
            code_string
        )
        
        print("  ✓ Explanation generated!")
        print("="*60)
        
        return explanation
    
    def explain_file(self, filepath):
        """
        Explain code from a file
        
        Args:
            filepath: Path to Python file
        
        Returns:
            Formatted explanation string
        """
        if not os.path.exists(filepath):
            return f"Error: File {filepath} not found"
        
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
        
        return self.explain_code(code)
    
    def save_explanation(self, explanation, output_file):
        """Save explanation to file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(explanation)
        
        print(f"\n✓ Explanation saved to {output_file}")


def main():
    """Example usage"""
    # Initialize explainer
    explainer = CodeExplainer()
    
    # Example code to explain
    sample_code = """import os

# Get current directory
current_dir = os.getcwd()

# List all files
files = os.listdir(current_dir)

# Filter directories
for f in files:
    if os.path.isdir(f):
        print(f"Directory: {f}")
"""
    
    # Generate explanation
    explanation = explainer.explain_code(sample_code)
    
    # Print result
    print("\n" + explanation)
    
    # Save to file
    explainer.save_explanation(explanation, "explanation_output.txt")


if __name__ == "__main__":
    main()