import os
from file_manager import FileManager
from markov import HiddenMarkovModel
from code_explainer import CodeExplainer

# Setup paths
PATH = os.path.dirname(__file__)
INPUT_FILE = PATH + '/sample_projects/project1/main.py'

print("="*60)
print("CODE EXPLAINER - Setup and Test")
print("="*60)

# Step 1: Build function database (run once)
print("\n[Step 1] Building function database...")
from embedder import build_os_library_database

try:
    build_os_library_database()
except Exception as e:
    print(f"Database already exists or error: {e}")

# Step 2: Initialize the explainer
print("\n[Step 2] Initializing Code Explainer...")
explainer = CodeExplainer('os_function_database.json')

# Step 3: Test with sample file
print(f"\n[Step 3] Analyzing file: {INPUT_FILE}")

if os.path.exists(INPUT_FILE):
    explanation = explainer.explain_file(INPUT_FILE)
    
    # Print explanation
    print("\n" + explanation)
    
    # Save to file
    output_file = PATH + '/explanation_output.txt'
    explainer.save_explanation(explanation, output_file)
else:
    print(f"Error: Input file not found: {INPUT_FILE}")
    print("\nTesting with sample code instead...")
    
    # Test with inline code
    sample_code = """import os

# Get current directory
current_dir = os.getcwd()
print(f"Current directory: {current_dir}")

# List all files
files = os.listdir(current_dir)

# Process each file
for filename in files:
    full_path = os.path.join(current_dir, filename)
    
    if os.path.isfile(full_path):
        print(f"File: {filename}")
    elif os.path.isdir(full_path):
        print(f"Directory: {filename}")
"""
    
    explanation = explainer.explain_code(sample_code)
    print("\n" + explanation)

print("\n" + "="*60)
print("Complete! You can now use the Sublime Text plugin.")
print("="*60)