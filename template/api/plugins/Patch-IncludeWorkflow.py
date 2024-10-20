# add yaml flag and check to prevent modification of already modified files 
import os
import yaml
import json
import xml.etree.ElementTree as ET

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
            'file': file,
            'properties': extract_properties(file)
        })
    
    return toc_entries

def save_toc(toc_path, toc_items):
    """Save the patched TOC file."""
    with open(toc_path, 'w') as f:
        # Write the magic header
        f.write("### YamlMime:TableOfContent\n")

        yaml.dump(toc_items, f, default_flow_style=False, sort_keys=False)

def patch_manifest(manifest_path, new_entries):
    with open(manifest_path, 'r') as f:
        manifest_data = json.load(f)
    for entry in new_entries:
        manifest_data[entry['uid']] =  entry['uid']+".yml"
        #generate manifest entries for operator properties
        for key in entry['properties'].keys():
            manifest_data[entry['uid']+"."+key] = entry['uid']+".yml"
    with open(manifest_path, 'w') as f:
        json.dump(manifest_data, f, indent=2, sort_keys=True)

def extract_properties(entry):
    properties = []
    
    tree = ET.parse(entry)
    root = tree.getroot()

    # Get XML namespaces and prefixes
    xml_namespace = {}
    for event, elem in ET.iterparse(entry, ["start-ns"]):
         xml_namespace[elem[0]] = elem[1]

    # Get the default namespace from the XML (no prefix)
    default_ns = xml_namespace['']  

    # Build the full tag name for 'Expression' with the namespace
    expression_tag = f"{{{default_ns}}}Expression"  # e.g., "{https://bonsai-rx.org/2018/workflow}Expression"

    # Find all visible 'Properties' based on xsi:type Externalized Mapping"
    # Note - it seems that some properties are hidden which I did not realise.
    # For instance see EventLogger
    property_dict = {}
    for expression in root.findall(f".//{expression_tag}", xml_namespace):
        xsi_type = expression.get(f"{{{xml_namespace['xsi']}}}type")  
        if xsi_type == "ExternalizedMapping":
            for prop in expression.findall(f"{{{default_ns}}}Property"):
                property_name = prop.get('Name')
                description = prop.get('Description', "No description available.")
                display_name = prop.get('DisplayName', False)
                if display_name == False:
                    property_dict[property_name] = description
                else:
                    property_dict[display_name] = description
    return property_dict


def main():
    src_folder = "../src"  # Adjust if your src folder is in a different location
    toc_path = "api/toc.yml"  # Path to the existing TOC file
    manifest_path ="api/.manifest" 

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

    # Patch manifest
    patch_manifest(manifest_path, new_entries)

    print(f"Successfully updated {toc_path}, {manifest_path}. ")

if __name__ == "__main__":
    main()