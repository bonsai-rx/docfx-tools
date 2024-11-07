# README: this script modifies several accessory files that seem to be needed for getting IncludeWorkflows
# recognised in dotnet build. Gnerating individual api yml files for the .bonsai IncludeWorkflows
# isnt enough as the API template relies on certain shared models that don't build correctly
# TODO: add yaml flag and check to prevent modification of already modified files 
# TODO: make it more efficient (too many loops of new entries in each separate function)
# requirements: pyyaml (install with pip install pyyaml)

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

def generate_entries(bonsai_files, src_folder):
    """Generate entries from the list of bonsai files."""
    new_entries = []
    
    for file in bonsai_files:
        name = os.path.splitext(os.path.basename(file))[0]
        namespace = extract_namespace(file, src_folder)
        uid = namespace + "." + name
        operator_description, properties = extract_information_from_bonsai(file, src_folder, 'parse_root')
        
        new_entries.append({
            'namespace': namespace,
            'uid': uid,
            'name': name,
            'file': file,
            'operator_description': operator_description,
            'properties': properties
        })
    
    return new_entries

def get_git_information():
    branch_name = ""
    repo_url = ""
    with open("../.git/HEAD", "r") as f:
        content = f.read().strip()
        if content.startswith("ref:"):
            branch_name = content.split("/")[-1]
    with open("../.git/config", "r") as f:
        for line in f:
            if "url = " in line:
                repo_url = line.split("=", 1)[1].strip()
                break
    return(branch_name, repo_url)


def create_bonsai_yml(bonsai_entries, api_folder, branch_name, repo_url):
    for entry in bonsai_entries:
        bonsai_yml_file = os.path.join(api_folder, entry['uid']+".yml")
        new_bonsai_yml_file = {}
        new_bonsai_yml_file['items']=[{
                'uid': entry['uid'],
                'commentId': "T:"+entry['uid'],
                'id': entry['name'],
                'parent': entry['namespace'],
                'children': [entry['uid'] + "." + x for x in entry['properties']],
                'langs': ['csharp','vb'],
                'name': entry['name'],
                'nameWithType': entry['name'],
                'fullName': entry['uid'],
                'type': "Class",
                'source': {
                    'remote':{
                        'path':entry['file'][3:],
                        'branch':branch_name, 
                        'repo':repo_url
                        }, 
                    'id': entry['name'], 
                    'path': entry['file'],
                    # this isn't accurate but is hardcoded here because I don't think it affects anything
                    'startLine': 9
                    },
                'assemblies': [entry['namespace'].split('.')[0]],
                'namespace': entry['namespace'],
                'summary': entry['operator_description'],
                'syntax':{
                    'content': "public class " + entry['name'],
                    'content.vb': "Public Class " + entry['name']
                },
                # # this isn't applicable for bonsai files but added it in to avoid mref.extension.js errors
                # # TODO: maybe make that section of the code more robust to missing fields
                # 'inheritance': ['System.Object'],
                # 'inheritedMembers': ['System.Object.GetType'],
            }]
        # adds properties
        for property_name, property_description in entry['properties'].items():
            new_bonsai_yml_file['items'].append({
                'uid':entry['uid']+"." + property_name,
                'commentId': 'P:'+ entry['uid']+"." + property_name,
                'id': property_name,
                'parent': entry['uid'],
                'langs': ['csharp','vb'],
                'name': property_name,
                'nameWithType': entry['name']+'.'+property_name,
                'fullName': entry['uid']+'.'+property_name,
                'type':'Property',
                'source': {
                    'remote':{
                        'path':entry['file'][3:],
                        'branch':branch_name, 
                        'repo':repo_url
                        }, 
                    'id': property_name, 
                    'path': entry['file'],
                    # this isn't accurate but is hardcoded here because I don't think it affects anything
                    'startLine': 9
                },
                'assemblies': [entry['namespace'].split('.')[0]],
                'namespace': entry['namespace'],
                'summary': property_description,
                # this should probably be tailored for each property
                'syntax':{
                    'content': 'public float ' + property_name,
                    'parameters': [],
                    'return': {'type': 'System.Single'},
                    'content.vb': "Public Property " + property_name + " As Single"
                },
                'overload': entry['uid']+'.'+ property_name +'*'
            })

        # adds references
        # adds parent reference
        new_bonsai_yml_file['references']=[{
                'uid': entry['namespace'],
                'commentId': "N:"+entry['namespace'],
                'href': entry['namespace'].split('.')[0]+".html",
                'name': entry['namespace'],
                'nameWithType': entry['namespace'],
                'fullName': entry['namespace'],
        }]
        # this section modifies the parent reference to include additional information if the parent isn't the root namespace
        # Works for 2 namespaces (like Bonvision.Collections), will there be instances where theres more than 2?
        if entry['namespace'].split('.')[0] != entry['namespace']:
            new_bonsai_yml_file['references'][0]['spec.csharp'] = [{
                'uid': entry['namespace'].split('.')[0],
                'name': entry['namespace'].split('.')[0],
                'href': entry['namespace'].split('.')[0]+".html"
                },{
                'name':'.'
                },{
                'uid': entry['namespace'],
                'name': entry['namespace'].split('.')[1],
                'href': entry['namespace']+".html"
                }]
            new_bonsai_yml_file['references'][0]['spec.vb'] = [{
                'uid': entry['namespace'].split('.')[0],
                'name': entry['namespace'].split('.')[0],
                'href':entry['namespace'].split('.')[0]+".html"
                },{
                'name':'.'
                },{
                'uid': entry['namespace'],
                'name': entry['namespace'].split('.')[1],
                'href': entry['namespace']+".html"
                }]
        
        # adds return value reference
        new_bonsai_yml_file['references'].append({
                'uid': 'System.Single',
                'commentId': 'T:System.Single',
                'parent': 'System',
                'isExternal': 'true',
                'href': 'https://learn.microsoft.com/dotnet/api/system.single',
                'name': 'float',
                'nameWithType': 'float',
                'fullName': 'float',
                'nameWithType.vb': 'Single',
                'fullName.vb': 'Single',
                'name.vb': 'Single'
        })

        # adds properties overload references
        for property_name, description in entry['properties'].items():
            new_bonsai_yml_file['references'].append({
                'uid':entry['uid']+'.'+ property_name +'*',
                'commentId': 'Overload:'+ entry['uid']+'.'+ property_name,
                'href': entry['uid']+'.html#'+entry['uid'].replace('.', '_')+'_'+property_name,
                'name': property_name,
                'nameWithType': entry['name']+'.'+property_name,
                'fullName': entry['uid']+'.'+property_name,
            })
        
        with open(bonsai_yml_file, 'w') as f:
            f.write("### YamlMime:ManagedReference\n")
            yaml.dump(new_bonsai_yml_file, f, default_flow_style=False, sort_keys=False)

def patch_namespace_files(new_entries, api_folder):
    for entry in new_entries:
        namespace_file = os.path.join(api_folder, entry['namespace']+".yml")
        if os.path.exists(namespace_file):
            pass
        else:
            # generate new namespace.yml file if it isnt present
            # some items in namespace files dont appear as .cs files 
            # for instance bonvision collections has GratingTrial and GratingParameters
            # even though there are no .cs files
            # they are present as classes in CreateGratingTrial and GratingSpecifications specifically
            new_namespace_file = {}
            new_namespace_file["items"]=[{
                'uid': entry['namespace'],
                'commentId': "N:"+entry['namespace'],
                'id': entry['namespace'],
                'children': [],
                'langs': ['csharp','vb'],
                'name': entry['namespace'],
                'nameWithType': entry['namespace'],
                'fullName': entry['namespace'],
                'type': "Namespace",
                'assemblies': [entry['namespace'].split('.')[0]]
            }]
            new_namespace_file["references"]=[]
            with open(namespace_file, 'w') as f:
                f.write("### YamlMime:ManagedReference\n")
                yaml.dump(new_namespace_file, f, default_flow_style=False, sort_keys=False)
        with open(namespace_file, 'r') as f:
            namespace_file_to_amend = yaml.safe_load(f)
            namespace_file_to_amend["items"][0]['children'].append(entry['uid'])
            namespace_file_to_amend["references"].append({
                'uid': entry['uid'],
                'commentId': "T:"+entry['uid'],
                'href': entry['uid']+".html",
                'name': entry['name'],
                'nameWithType': entry['name'],
                'fullName': entry['uid']
            })
        with open(namespace_file, 'w') as f:
            f.write("### YamlMime:ManagedReference\n")
            yaml.dump(namespace_file_to_amend, f, default_flow_style=False, sort_keys=False)
            

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

def extract_information_from_bonsai(entry, src_folder, method, property = None):
    properties = []
    
    tree = ET.parse(entry)
    root = tree.getroot()

    # Get XML namespaces and prefixes
    # Build tags
    xml_namespace = {}
    for event, elem in ET.iterparse(entry, ["start-ns"]):
         xml_namespace[elem[0]] = elem[1]

    default_ns = xml_namespace['']  
    description_tag = f"{{{default_ns}}}Description"
    expression_tag = f"{{{default_ns}}}Expression"  

    if method == "parse_root":
        operator_description = root.find(description_tag).text

        # Find other IncludeWorkflow files to pull externalised mapping properties from
        # This assumes that there might be more than 1 IncludeWorkflow .bonsai file but so far I have only seen 1
        # This for loop is duplicated in the next session, see if its possible to maybe refactor
        include_workflow_list = []
        for expression in root.findall(f".//{expression_tag}", xml_namespace):
            xsi_type = expression.get(f"{{{xml_namespace['xsi']}}}type")
            if xsi_type == "IncludeWorkflow":
                path = expression.get("Path", "No path available") 
                parts = path.split(":")
                # this assumes that there is only 1 folder in the parent namespace, but might need to be modified in case 
                # I could combine the split with a list comprehension, but sometimes the parent namespace has dots in the folder 
                # eg. Bonsai.ML.LinearDynamicalSystems
                subparts = parts[1].split(".")
                file_path = os.path.join(src_folder, parts[0], subparts[0], f"{subparts[1]}.bonsai")
                include_workflow_list.append(file_path)

        # Find all visible 'Properties' based on xsi:type Externalized Mapping"
        # Note - it seems that some properties are hidden which I did not realise.
        # For instance see EventLogger
        property_dict = {}
        for expression in root.findall(f".//{expression_tag}", xml_namespace):
            xsi_type = expression.get(f"{{{xml_namespace['xsi']}}}type")  
            if xsi_type == "ExternalizedMapping":
                for prop in expression.findall(f"{{{default_ns}}}Property"):
                    property_name = prop.get('Name')
                    description = prop.get('Description', False)
                    display_name = prop.get('DisplayName', False)
                    if display_name == False:
                        pass
                    else:
                        property_name = display_name
                    if description == False:
                        for file in include_workflow_list:
                            description = extract_information_from_bonsai(file, src_folder, "parse_sub", property_name)
                    property_dict[property_name] = description
        return operator_description, property_dict
    
    if method == "parse_sub":
        property_dict = {}
        description = False
        for expression in root.findall(f".//{expression_tag}", xml_namespace):
            xsi_type = expression.get(f"{{{xml_namespace['xsi']}}}type")  
            if xsi_type == "ExternalizedMapping":
                for prop in expression.findall(f"{{{default_ns}}}Property"):
                    if property == prop.get('Name') or property == prop.get('DisplayName'):
                        description = prop.get('Description')
        return description

def main():
    src_folder = "../src"  # Adjust if your src folder is in a different location
    toc_path = "api/toc.yml"  # Path to the existing TOC file
    manifest_path ="api/.manifest" 
    api_folder = "api/"

    # Find all .bonsai files in the src folder
    bonsai_files = find_bonsai_files(src_folder)
    print(f"Found {len(bonsai_files)} .bonsai files.")

    # Generate entries from bonsai files
    new_entries = generate_entries(bonsai_files, src_folder)

    # Get git information to populate yml source field
    branch_name, repo_url = get_git_information()

    # Create Bonsai Yml Files
    create_bonsai_yml(new_entries, api_folder, branch_name, repo_url)
    print(f"Successfully created .bonsai yml files in {api_folder}")

    # Patch namespace.yml files
    patch_namespace_files(new_entries, api_folder)

    # Load the existing TOC file
    toc_items = load_existing_toc(toc_path)

    # Patch the TOC with new entries
    patched_toc = patch_toc(toc_items, new_entries)

    # Save the updated TOC file
    save_toc(toc_path, patched_toc)

    # Patch manifest with new entries
    patch_manifest(manifest_path, new_entries)

    print(f"Successfully updated {toc_path}, {manifest_path}, and namespace.yml files")

if __name__ == "__main__":
    main()