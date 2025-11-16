"""
Sample Python file for testing CodeSuggester
This script demonstrates various os module operations
"""

import os
import sys

def list_directory_contents(path='.'):
    """List all files and directories in the given path"""
    print(f"Contents of {path}:")
    print("-" * 50)
    
    # Get all items in directory
    items = os.listdir(path)
    
    # Separate files and directories
    files = []
    directories = []
    
    for item in items:
        full_path = os.path.join(path, item)
        
        if os.path.isfile(full_path):
            files.append(item)
        elif os.path.isdir(full_path):
            directories.append(item)
    
    # Display directories
    print("\nDirectories:")
    for dir_name in directories:
        print(f"  [DIR]  {dir_name}")
    
    # Display files
    print("\nFiles:")
    for file_name in files:
        file_path = os.path.join(path, file_name)
        size = os.path.getsize(file_path)
        print(f"  [FILE] {file_name} ({size} bytes)")
    
    print(f"\nTotal: {len(directories)} directories, {len(files)} files")


def find_python_files(root_path='.'):
    """Find all Python files in directory tree"""
    python_files = []
    
    # Walk through directory tree
    for dirpath, dirnames, filenames in os.walk(root_path):
        for filename in filenames:
            if filename.endswith('.py'):
                full_path = os.path.join(dirpath, filename)
                python_files.append(full_path)
    
    return python_files


def get_system_info():
    """Get system information"""
    print("\nSystem Information:")
    print("-" * 50)
    
    # Current working directory
    cwd = os.getcwd()
    print(f"Current Directory: {cwd}")
    
    # User name
    try:
        username = os.getlogin()
        print(f"User: {username}")
    except:
        print("User: Unable to determine")
    
    # Process ID
    pid = os.getpid()
    print(f"Process ID: {pid}")
    
    # Environment variable
    path_env = os.getenv('PATH', 'Not set')
    print(f"PATH: {path_env[:100]}...")


def main():
    """Main execution function"""
    print("=" * 50)
    print("File System Analyzer")
    print("=" * 50)
    
    # Get current directory
    current_dir = os.getcwd()
    
    # List contents
    list_directory_contents(current_dir)
    
    # Find Python files
    print("\n\nSearching for Python files...")
    py_files = find_python_files(current_dir)
    
    if py_files:
        print(f"Found {len(py_files)} Python file(s):")
        for py_file in py_files[:10]:  # Show first 10
            print(f"  - {py_file}")
        
        if len(py_files) > 10:
            print(f"  ... and {len(py_files) - 10} more")
    else:
        print("No Python files found.")
    
    # Show system info
    get_system_info()
    
    print("\n" + "=" * 50)
    print("Analysis complete!")


if __name__ == "__main__":
    main()