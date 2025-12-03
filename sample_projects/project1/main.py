import os

# Get the current working directory
cwd = os.getcwd()
print("Current directory:", cwd)

# List all files and folders in the current directory
items = os.listdir(cwd)
print("Contents:")
for item in items:
    print("-", item)
