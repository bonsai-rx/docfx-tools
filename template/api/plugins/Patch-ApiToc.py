import os
import yaml

def find_bonsai_files(src_folder):
    """Search for all .bonsai files in the src folder and return their paths."""
    bonsai_files = []
    for root, _, files in os.walk(src_folder):
        for file in files:
            if file.endswith(".bonsai"):
                # Store the full path to the bonsai file
                bonsai_files.append(os.path.join(root, file))
    return bonsai_files

def extract_namespace(file_path, src_folder):
    """Extract namespace by converting the path to a dotted string."""
    # Get the relative path from src folder
    relative_path = os.path.relpath(file_path, src_folder)

    # Remove the filename from the path (only keep directories)
    namespace_path = os.path.dirname(relative_path)

    # Replace separators with dots
    namespace = namespace_path.replace(os.sep, '.')

    return namespace

def load_existing_toc(toc_path):
    """Load the existing TOC or display an error message if it doesn't exist."""
    if os.path.exists(toc_path):
        with open(toc_path, 'r') as f:
            return yaml.safe_load(f)
    else:
        raise FileNotFoundError(
            "api/toc.yml not found. Execute this script from the docs directory or run `docfx metadata` first to generate toc.yml."
        )


def patch_toc(toc_data, new_entries):
    """Patch the TOC with new entries."""
    # Create a map of existing namespaces
    namespace_map = {item['uid']: item for item in toc_data['items']}

    # Iterate over the new entries
    for entry in new_entries:
        namespace = entry['namespace']
        item_data = {'uid': entry['uid'], 'name': entry['name']}

        if namespace in namespace_map:
            # Add new item to the existing namespace
            namespace_map[namespace]['items'].append(item_data)
        else:
            # Create a new namespace entry with proper key order
            new_namespace_entry = {
                'uid': namespace,
                'name': namespace,
                'items': [item_data]
            }
            toc_data['items'].append(new_namespace_entry)
            namespace_map[namespace] = new_namespace_entry 
    return toc_data

def generate_toc_entries(bonsai_files, src_folder):
    """Generate TOC entries from the list of bonsai files."""
    toc_entries = []
    
    for file in bonsai_files:
        name = os.path.splitext(os.path.basename(file))[0]
        namespace = extract_namespace(file, src_folder)
        uid = namespace + "." + name
        
        toc_entries.append({
            'namespace': namespace,
            'uid': uid,
            'name': name,
        })
    
    return toc_entries

def save_toc(toc_path, toc_items):
    """Save the patched TOC file."""
    with open(toc_path, 'w') as f:
        # Write the magic header
        f.write("### YamlMime:TableOfContent\n")

        yaml.dump(toc_items, f, default_flow_style=False, sort_keys=False)

def main():
    src_folder = "../src"  # Adjust if your src folder is in a different location
    toc_path = "api/toc.yml"  # Path to the existing TOC file

    # Find all .bonsai files in the src folder
    bonsai_files = find_bonsai_files(src_folder)
    print(f"Found {len(bonsai_files)} .bonsai files.")

    # Generate TOC entries
    new_entries = generate_toc_entries(bonsai_files, src_folder)

    # Load the existing TOC file
    toc_items = load_existing_toc(toc_path)

    # # Patch the TOC with new entries
    patched_toc = patch_toc(toc_items, new_entries)

    # Save the updated TOC file
    save_toc(toc_path, patched_toc)

    print(f"Successfully updated {toc_path}.")

if __name__ == "__main__":
    main()