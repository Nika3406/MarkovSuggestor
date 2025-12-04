import inspect
import importlib


def extract_library_info(library_name):
    """
    Extract information about a library and save to a text file

    Args:
        library_name: Name of the library (e.g., 'os', 'random', 'math')
    """
    try:
        # Import the library
        module = importlib.import_module(library_name)

        # Create output filename
        output_file = f"{library_name}_info.txt"

        # Open file for writing
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write("=" * 80 + "\n")
            f.write(f"Library: {library_name}\n")
            f.write("=" * 80 + "\n\n")

            # Get module docstring
            module_doc = inspect.getdoc(module)
            if module_doc:
                f.write("MODULE DESCRIPTION:\n")
                f.write("-" * 80 + "\n")
                f.write(module_doc + "\n\n")

            # Get all members (functions, classes, etc.)
            members = inspect.getmembers(module)

            # Separate functions and other members
            functions = []
            classes = []
            other = []

            for name, obj in members:
                # Skip private members (starting with _)
                if name.startswith('_'):
                    continue

                if inspect.isfunction(obj) or inspect.isbuiltin(obj):
                    functions.append((name, obj))
                elif inspect.isclass(obj):
                    classes.append((name, obj))
                else:
                    other.append((name, obj))

            # Write functions section
            f.write("FUNCTIONS:\n")
            f.write("=" * 80 + "\n\n")

            for name, func in functions:
                f.write(f"Function: {name}\n")
                f.write("-" * 80 + "\n")

                # Try to get signature
                try:
                    sig = inspect.signature(func)
                    f.write(f"Signature: {name}{sig}\n")
                except (ValueError, TypeError):
                    f.write(f"Signature: {name}(...)\n")

                # Get docstring
                doc = inspect.getdoc(func)
                if doc:
                    f.write(f"Description:\n{doc}\n")
                else:
                    f.write("Description: No documentation available\n")

                f.write("\n")

            # Write classes section
            if classes:
                f.write("\n" + "=" * 80 + "\n")
                f.write("CLASSES:\n")
                f.write("=" * 80 + "\n\n")

                for name, cls in classes:
                    f.write(f"Class: {name}\n")
                    f.write("-" * 80 + "\n")

                    # Get class docstring
                    doc = inspect.getdoc(cls)
                    if doc:
                        # Only show first paragraph
                        first_para = doc.split('\n\n')[0]
                        f.write(f"Description: {first_para}\n")
                    else:
                        f.write("Description: No documentation available\n")

                    f.write("\n")

            # Write other members section
            if other:
                f.write("\n" + "=" * 80 + "\n")
                f.write("OTHER MEMBERS (constants, variables):\n")
                f.write("=" * 80 + "\n\n")

                for name, obj in other:
                    f.write(f"{name}: {type(obj).__name__}")
                    # Try to show value if it's simple
                    try:
                        if isinstance(obj, (int, str, float, bool)):
                            f.write(f" = {obj}")
                    except:
                        pass
                    f.write("\n")

            # Write summary
            f.write("\n" + "=" * 80 + "\n")
            f.write("SUMMARY:\n")
            f.write("=" * 80 + "\n")
            f.write(f"Total Functions: {len(functions)}\n")
            f.write(f"Total Classes: {len(classes)}\n")
            f.write(f"Other Members: {len(other)}\n")

        print(f"  Information saved to {output_file}")
        print(f"  Functions: {len(functions)}")
        print(f"  Classes: {len(classes)}")
        print(f"  Other members: {len(other)}")

    except ImportError:
        print(f"  Error: Cannot import library '{library_name}'")
        print(f"  Make sure it's installed: pip install {library_name}")
    except Exception as e:
        print(f"✗ Error: {e}")


if __name__ == "__main__":
    # Extract info for 'os' library
    print("Extracting information for 'os' library...\n")
    extract_library_info('os')

    # Uncomment to extract info for other libraries:
    # print("\nExtracting information for 'random' library...\n")
    # extract_library_info('random')

    # print("\nExtracting information for 'math' library...\n")
    # extract_library_info('math')
