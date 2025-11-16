"""
Test script to verify all components work correctly
"""

import os
import sys

def test_imports():
    """Test that all required packages are installed"""
    print("\n" + "="*60)
    print("Testing Package Imports")
    print("="*60)
    
    packages = {
        'torch': 'PyTorch',
        'sentence_transformers': 'Sentence Transformers',
        'numpy': 'NumPy'
    }
    
    all_good = True
    for package, name in packages.items():
        try:
            __import__(package)
            print(f"✓ {name} installed")
        except ImportError:
            print(f"✗ {name} NOT installed - run: pip install {package}")
            all_good = False
    
    return all_good

def test_modules():
    """Test that all custom modules load correctly"""
    print("\n" + "="*60)
    print("Testing Custom Modules")
    print("="*60)
    
    modules = [
        'file_manager',
        'markov',
        'embedder',
        'pseudocode_generator',
        'code_explainer'
    ]
    
    all_good = True
    for module in modules:
        try:
            __import__(module)
            print(f"✓ {module}.py loaded successfully")
        except ImportError as e:
            print(f"✗ {module}.py failed to load: {e}")
            all_good = False
    
    return all_good

def test_file_manager():
    """Test FileManager functionality"""
    print("\n" + "="*60)
    print("Testing FileManager")
    print("="*60)
    
    from file_manager import FileManager
    
    sample_code = """import os
files = os.listdir('.')
for f in files:
    print(f)
"""
    
    try:
        fm = FileManager(sample_code)
        imports = fm.get_imports()
        calls = fm.get_function_calls()
        control = fm.get_control_flow()
        
        print(f"✓ Parsed {len(imports)} imports")
        print(f"✓ Parsed {len(calls)} function calls")
        print(f"✓ Parsed {len(control)} control structures")
        
        return True
    except Exception as e:
        print(f"✗ FileManager test failed: {e}")
        return False

def test_hmm():
    """Test HMM functionality"""
    print("\n" + "="*60)
    print("Testing Hidden Markov Model")
    print("="*60)
    
    from markov import HiddenMarkovModel
    
    try:
        hmm = HiddenMarkovModel(None, None, None, None)
        tokens = ['IMPORT', 'os', 'CALL', 'os.listdir']
        result = hmm.predict_intent(tokens)
        
        print(f"✓ HMM initialized with {hmm.n_hidden} states")
        print(f"✓ Predicted {len(result['states'])} state sequence")
        print(f"✓ Dominant state: {result.get('dominant_state', 'Unknown')}")
        
        return True
    except Exception as e:
        print(f"✗ HMM test failed: {e}")
        return False

def test_embedder():
    """Test embedder functionality"""
    print("\n" + "="*60)
    print("Testing Sentence Embedder")
    print("="*60)
    
    from embedder import FunctionEmbedder
    
    try:
        print("Loading sentence transformer model...")
        embedder = FunctionEmbedder()
        print("✓ Model loaded successfully")
        
        # Test embedding
        test_query = "list files in directory"
        embedding = embedder.model.encode([test_query])[0]
        print(f"✓ Generated embedding with {len(embedding)} dimensions")
        
        # Check for database
        if os.path.exists('os_function_database.json'):
            embedder.load_database('os_function_database.json')
            print(f"✓ Loaded database with {len(embedder.function_database)} functions")
        else:
            print("⚠ Database not found (run embedder.py to create)")
        
        return True
    except Exception as e:
        print(f"✗ Embedder test failed: {e}")
        return False

def test_complete_pipeline():
    """Test the complete explanation pipeline"""
    print("\n" + "="*60)
    print("Testing Complete Pipeline")
    print("="*60)
    
    # Check if database exists
    if not os.path.exists('os_function_database.json'):
        print("⚠ Database not found - building it now...")
        try:
            from embedder import build_os_library_database
            build_os_library_database()
        except Exception as e:
            print(f"✗ Could not build database: {e}")
            return False
    
    try:
        from code_explainer import CodeExplainer
        
        print("Initializing CodeExplainer...")
        explainer = CodeExplainer()
        
        sample_code = """import os

current_dir = os.getcwd()
files = os.listdir(current_dir)

for filename in files:
    if os.path.isfile(filename):
        print(filename)
"""
        
        print("Generating explanation...")
        explanation = explainer.explain_code(sample_code)
        
        print("✓ Explanation generated successfully!")
        print("\nSample output (first 500 chars):")
        print("-" * 60)
        print(explanation[:500] + "...")
        
        return True
    except Exception as e:
        print(f"✗ Complete pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("\n" + "#"*60)
    print("# CodeSuggester System Test Suite")
    print("#"*60)
    
    tests = [
        ("Package Dependencies", test_imports),
        ("Custom Modules", test_modules),
        ("FileManager", test_file_manager),
        ("Hidden Markov Model", test_hmm),
        ("Sentence Embedder", test_embedder),
        ("Complete Pipeline", test_complete_pipeline)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print("\n" + "="*60)
    print(f"Results: {passed}/{total} tests passed")
    print("="*60)
    
    if passed == total:
        print("\n✓ All tests passed! System is ready to use.")
        print("\nNext steps:")
        print("1. Copy files to Sublime Text Packages/CodeSuggester/")
        print("2. Restart Sublime Text")
        print("3. Open a Python file and press Ctrl+Alt+E")
    else:
        print("\n✗ Some tests failed. Please fix the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)