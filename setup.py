#!/usr/bin/env python3
"""
Setup script for CodeSuggester
Automates installation and configuration
"""

import os
import sys
import subprocess
import shutil
import platform

class Colors:
    """ANSI color codes"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Print colored header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}\n")

def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_info(text):
    """Print info message"""
    print(f"{Colors.CYAN}ℹ {text}{Colors.END}")

def check_python_version():
    """Check if Python version is sufficient"""
    print_header("Checking Python Version")
    
    version = sys.version_info
    if version.major >= 3 and version.minor >= 7:
        print_success(f"Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print_error(f"Python {version.major}.{version.minor}.{version.micro} (need 3.7+)")
        return False

def install_dependencies():
    """Install required Python packages"""
    print_header("Installing Dependencies")
    
    packages = ['torch', 'sentence-transformers', 'numpy']
    
    for package in packages:
        print(f"Installing {package}...")
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', package,
                '--quiet', '--disable-pip-version-check'
            ])
            print_success(f"{package} installed")
        except subprocess.CalledProcessError:
            print_error(f"Failed to install {package}")
            return False
    
    return True

def build_database():
    """Build the function database"""
    print_header("Building Function Database")
    
    # Check if os_info.txt exists
    if not os.path.exists('DataSetup/os_info.txt'):
        print_error("os_info.txt not found")
        print_info("Run libraryExtractor.py first")
        return False
    
    # Check if database already exists
    if os.path.exists('os_function_database.json'):
        print_warning("Database already exists")
        response = input("Rebuild? (y/n): ").lower()
        if response != 'y':
            print_info("Skipping database build")
            return True
    
    # Build database
    try:
        print_info("This may take 30-60 seconds...")
        from embedder import build_os_library_database
        build_os_library_database()
        print_success("Database built successfully")
        return True
    except Exception as e:
        print_error(f"Database build failed: {e}")
        return False

def run_tests():
    """Run system tests"""
    print_header("Running System Tests")
    
    if not os.path.exists('test_system.py'):
        print_warning("test_system.py not found, skipping tests")
        return True
    
    try:
        result = subprocess.run([sys.executable, 'test_system.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print_success("All tests passed")
            return True
        else:
            print_error("Some tests failed")
            print(result.stdout)
            return False
    except Exception as e:
        print_error(f"Test execution failed: {e}")
        return False

def get_sublime_packages_path():
    """Get Sublime Text packages directory path"""
    system = platform.system()
    home = os.path.expanduser('~')
    
    if system == 'Darwin':  # macOS
        return os.path.join(home, 'Library/Application Support/Sublime Text 3/Packages')
    elif system == 'Linux':
        return os.path.join(home, '.config/sublime-text-3/Packages')
    elif system == 'Windows':
        return os.path.join(os.getenv('APPDATA'), 'Sublime Text 3', 'Packages')
    else:
        return None

def install_sublime_plugin():
    """Install files to Sublime Text"""
    print_header("Installing Sublime Text Plugin")
    
    # Get Sublime packages path
    packages_path = get_sublime_packages_path()
    
    if not packages_path:
        print_error("Could not determine Sublime Text packages path")
        print_info("Please install manually")
        return False
    
    if not os.path.exists(packages_path):
        print_error(f"Sublime Text packages directory not found: {packages_path}")
        print_info("Is Sublime Text installed?")
        return False
    
    # Create plugin directory
    plugin_path = os.path.join(packages_path, 'CodeSuggester')
    
    if os.path.exists(plugin_path):
        print_warning("Plugin directory already exists")
        response = input("Overwrite? (y/n): ").lower()
        if response != 'y':
            print_info("Skipping plugin installation")
            return True
        shutil.rmtree(plugin_path)
    
    os.makedirs(plugin_path, exist_ok=True)
    print_info(f"Created directory: {plugin_path}")
    
    # Files to copy
    files_to_copy = [
        'CodeSuggester.py',
        'code_explainer.py',
        'embedder.py',
        'file_manager.py',
        'markov.py',
        'pseudocode_generator.py',
        'os_function_database.json',
        'CodeSuggester.sublime-settings',
        'Default.sublime-keymap',
        'Context.sublime-menu'
    ]
    
    # Copy files
    copied = 0
    for filename in files_to_copy:
        if os.path.exists(filename):
            try:
                shutil.copy2(filename, plugin_path)
                print_success(f"Copied {filename}")
                copied += 1
            except Exception as e:
                print_error(f"Failed to copy {filename}: {e}")
        else:
            print_warning(f"File not found: {filename}")
    
    if copied == len(files_to_copy):
        print_success(f"All files installed to {plugin_path}")
        return True
    else:
        print_warning(f"Installed {copied}/{len(files_to_copy)} files")
        return copied > 0

def create_sample_project():
    """Create sample project for testing"""
    print_header("Creating Sample Project")
    
    sample_dir = os.path.join('sample_projects', 'project1')
    os.makedirs(sample_dir, exist_ok=True)
    
    sample_code = """import os

# List files in current directory
files = os.listdir('.')

# Filter for Python files
python_files = [f for f in files if f.endswith('.py')]

# Print results
print(f"Found {len(python_files)} Python files")
for pf in python_files:
    print(f"  - {pf}")
"""
    
    sample_file = os.path.join(sample_dir, 'main.py')
    
    if not os.path.exists(sample_file):
        with open(sample_file, 'w') as f:
            f.write(sample_code)
        print_success(f"Created sample project: {sample_file}")
    else:
        print_info("Sample project already exists")
    
    return True

def print_next_steps():
    """Print what to do next"""
    print_header("Setup Complete!")
    
    print(f"{Colors.GREEN}✓ Installation successful!{Colors.END}\n")
    
    print(f"{Colors.BOLD}Next Steps:{Colors.END}")
    print(f"  1. Restart Sublime Text")
    print(f"  2. Open a Python file")
    print(f"  3. Press {Colors.CYAN}Ctrl+Alt+E{Colors.END} to explain code")
    print()
    print(f"{Colors.BOLD}Keyboard Shortcuts:{Colors.END}")
    print(f"  {Colors.CYAN}Ctrl+Alt+E{Colors.END} - Explain code")
    print(f"  {Colors.CYAN}Ctrl+Alt+C{Colors.END} - Quick panel")
    print(f"  {Colors.CYAN}Ctrl+Alt+I{Colors.END} - Function info")
    print()
    print(f"{Colors.BOLD}Documentation:{Colors.END}")
    print(f"  - QUICKSTART.md - Quick reference")
    print(f"  - INSTALLATION.md - Detailed guide")
    print(f"  - PROJECT_SUMMARY.md - Architecture overview")
    print()

def main():
    """Main setup routine"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║                                                          ║")
    print("║              CodeSuggester Setup Wizard                  ║")
    print("║                                                          ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}\n")
    
    steps = [
        ("Checking Python version", check_python_version),
        ("Installing dependencies", install_dependencies),
        ("Building function database", build_database),
        ("Running tests", run_tests),
        ("Creating sample project", create_sample_project),
        ("Installing Sublime plugin", install_sublime_plugin)
    ]
    
    results = []
    
    for step_name, step_func in steps:
        try:
            result = step_func()
            results.append((step_name, result))
            
            if not result:
                print_error(f"{step_name} failed")
                print_info("Please fix the issue and run setup again")
                return False
        except KeyboardInterrupt:
            print_error("\nSetup interrupted by user")
            return False
        except Exception as e:
            print_error(f"{step_name} crashed: {e}")
            results.append((step_name, False))
            return False
    
    # Print summary
    print_header("Setup Summary")
    
    for step_name, result in results:
        if result:
            print_success(step_name)
        else:
            print_error(step_name)
    
    # All succeeded
    if all(result for _, result in results):
        print_next_steps()
        return True
    else:
        print_error("Setup completed with errors")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_error("\n\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)