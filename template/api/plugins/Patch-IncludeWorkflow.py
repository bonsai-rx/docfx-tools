# This script generates .yml files for IncludeWorkflow .bonsai operators,
# Adds them to namespace.yml and toc.yml files, 
# And modifies the .manifest file in api/ (not sure if this step is really necessary).
# Requirements: pyyaml as yaml support isn't part of standard python library
# Install pyyaml with `pip install pyyaml`
# TODO: add yaml flag and check to prevent modification of already modified files 
# TODO: add type and input/output 
# TODO: refactor and clean up code 

import os
import yaml
import json
import xml.etree.ElementTree as ET
import re

def find_bonsai_files(src_folder):
    """Search for all .bonsai files in the src folder and return their paths."""
    bonsai_files = []
    for root, _, files in os.walk(src_folder):
        for file in files:
            if file.endswith(".bonsai"):
                bonsai_files.append(os.path.join(root, file))
    return bonsai_files

def extract_namespace(file_path, src_folder):
    """Extract namespace by converting the path to a dotted string."""
    relative_path = os.path.relpath(file_path, src_folder)
    namespace_path = os.path.dirname(relative_path)
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

        # Add new item to the existing namespace
        if namespace in namespace_map:
            namespace_map[namespace]['items'].append(item_data)

        # Create a new namespace entry with proper key order if namespace doesn't exist
        else:
            new_namespace_entry = {
                'uid': namespace,
                'name': namespace,
                'items': [item_data]
            }
            toc_data['items'].append(new_namespace_entry)
            namespace_map[namespace] = new_namespace_entry 

    return toc_data

def generate_entries(bonsai_files, src_folder):
    """Generate entries from .bonsai file list to feed into create_bonsai_yml"""
    new_entries = []

    for file in bonsai_files:
        name = os.path.splitext(os.path.basename(file))[0]
        namespace = extract_namespace(file, src_folder)
        uid = namespace + "." + name
        operator_description, properties = extract_information_from_bonsai(file, src_folder)
        
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
    """Get git information to populate one of the yml fields"""
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
    """Generate .yml file from the .bonsai entries"""
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
                    },
                'assemblies': [entry['name']],
                'namespace': entry['namespace'],
                'summary': entry['operator_description'],
                'syntax':{
                    'content': "[WorkflowElementCategory(ElementCategory.Workflow)]"+"/n"+"public class " + entry['name'],
                    'content.vb': "Public Class " + entry['name']
                },
            }]
        
        # Adds properties
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
                },
                'assemblies': [entry['namespace'].split('.')[0]],
                'namespace': entry['namespace'],
                'summary': property_description,
                # Type Placeholder - needs to be tailored for each property or have it be removed in the template for IncludeWorkflow operators
                'syntax':{
                    'content': 'public placeholder ' + property_name,
                    'parameters': [],
                    'return': {'type': 'Placeholder'},
                    'content.vb': "Public Property " + property_name + " As Placeholder"
                },
                'overload': entry['uid']+'.'+ property_name +'*'
            })

        # Adds namespace references
        new_bonsai_yml_file['references']=[{
                'uid': entry['namespace'],
                'commentId': "N:"+entry['namespace'],
                'href': entry['namespace'].split('.')[0]+".html",
                'name': entry['namespace'],
                'nameWithType': entry['namespace'],
                'fullName': entry['namespace'],
        }]

        # This section modifies the parent reference to include additional information if the parent isn't the root namespace (eg. Bonvision.Collections)
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
        
        # Adds Type value reference (placeholder for now)
        new_bonsai_yml_file['references'].append({
                'uid': 'Placeholder',
                'commentId': 'T:Placeholder',
                'parent': 'System',
                'isExternal': 'true',
                # 'href': 'https://learn.microsoft.com/dotnet/api/system.single',
                'name': 'Placeholder',
                'nameWithType': 'Placeholder',
                'fullName': 'Placeholder',
                'nameWithType.vb': 'Placeholder',
                'fullName.vb': 'Placeholder',
                'name.vb': 'Placeholder'
        })

        # Adds properties overload references
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

def extract_information_from_cs(property_namespace, property_assembly, property_operator, src_folder, property_name):
    filename = os.path.join(src_folder, property_assembly, f"{property_operator}.cs")
    if os.path.exists(filename):
        pass

    # Edge case - Bonsai.ML operators seem to have a difference namespace/assembly configuration
    else:
        namespace_parts = set(property_namespace.split("."))
        assembly_parts = set(property_assembly.split("."))
        difference = list(namespace_parts - assembly_parts)[0]
        filename = os.path.join(src_folder, property_assembly, difference, f"{property_operator}.cs")

    with open(filename, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            # Check if the line is a Description attribute and extract the description text within quotes
            # Do we want to pull from XML summary descriptions for newer operators instead?
            if line.startswith("[Description("):
                description = re.search(r'\[Description\("([^"]*)"\)\]', line).group(1)
            
            # Breaks the loop if it finds the property declaration and returns the latest description
            if "public" in line and re.search(rf"\b{property_name}\b", line):
                break

    return description

def extract_information_from_package(property_namespace, property_assembly, property_operator, property_name):
    filename = os.path.join("../.bonsai", "Bonsai.config")
    description = False
    try:
        with open(filename, "r", encoding="utf-8") as file:
            tree = ET.parse(file)
            root = tree.getroot()

            # Find the AssemblyLocation element with the specified assemblyName
            for assembly_location in root.findall(".//AssemblyLocation"):
                if assembly_location.get("assemblyName") == property_assembly:
                    # Return the location attribute if the assembly is found
                    property_assembly_description_file = os.path.join("../.bonsai", assembly_location.get("location")[:-4] + ".xml")
                    try:
                        with open(property_assembly_description_file, "r", encoding="utf-8") as file2:
                            tree = ET.parse(file2)
                            root = tree.getroot()

                            for member in root.findall(".//member"):
                                if property_namespace == property_assembly:
                                    if member.get("name") == "P:"+property_assembly+"."+property_operator+"."+property_name:
                                        description = member.find("summary").text.strip()
                                else:
                                    if member.get("name") == "P:"+property_namespace+"."+property_operator+"."+property_name:
                                        description = member.find("summary").text.strip()
                    except:
                        print(f"{{{property_name}}} in {{{property_operator}}} in {{{property_assembly_description_file}}} not found. package not installed in .bonsai or missing doc XML")
                        return None
        return description
    except:
        print("Bonsai.config wasn't found, have you installed .bonsai local environment .")
        return None

def extract_information_from_bonsai(entry, src_folder, stop_recursion = False):
    tree = ET.parse(entry)
    root = tree.getroot()

    # Get XML namespaces and prefixes
    xml_namespace = {}
    for event, elem in ET.iterparse(entry, ["start-ns"]):
        xml_namespace[elem[0]] = elem[1]
    
    # Make tags
    default_ns = xml_namespace['']  
    description_tag = f"{{{default_ns}}}Description"
    expression_tag = f"{{{default_ns}}}Expression"  

    # Find description (if no description found should the operator be skipped?)
    if root.find(description_tag) is not None:
        operator_description = root.find(description_tag).text
    else:
        operator_description = "No Description Found"

    # Dictionary to store externalized properties and their descriptions
    xml_list = []
    processed_properties = set()
    include_workflow_list = []
    property_mapping_list = []
    properties_to_keep = []

    # Find relevant elements and store them sequentially in a list
    for expression in root.findall(f".//{expression_tag}", xml_namespace):
        xsi_type = expression.get(f"{{{xml_namespace['xsi']}}}type") 

        if xsi_type == "ExternalizedMapping":
            for prop in expression.findall(f"{{{default_ns}}}Property"):
                property_name = prop.get('Name')
                description = prop.get('Description', False)
                display_name = prop.get('DisplayName', False)

                if description:
                    properties_to_keep.append(display_name)

                xml_list.append({
                    "type": "ExternalizedMapping",
                    "property_name": property_name,
                    "display_name": display_name,
                    "description": description,
                })
        
        if xsi_type == "IncludeWorkflow":
            path = expression.get("Path", "No path available") 
            parts = path.split(":")
            subparts = parts[1].split(".")
            file_path = os.path.join(src_folder, parts[0], subparts[0], f"{subparts[1]}.bonsai")
            include_workflow_list.append(file_path)
            
        # Finds embededded operators to pull parameter descriptions from
        # So far though I have only seen combinators and none of the rest 
        # ':' in xsi_type catches some older operators that aren't enclosed by a Bonsai xsi:type (like io.csvreader)   
        if xsi_type in ("Combinator", "Source", "Transform", "Sink") or ':' in xsi_type:
            if xsi_type in ("Combinator", "Source", "Transform", "Sink"):
                operator_elem = expression.find("*", xml_namespace)
                property_reference = operator_elem.get(f"{{{xml_namespace['xsi']}}}type")
            else:
                operator_elem = expression
                property_reference = xsi_type

            if ':' in property_reference:
                property_namespace = xml_namespace[property_reference.split(':')[0]].split(':')[1].split(';')[0]
                property_assembly = xml_namespace[property_reference.split(':')[0]].split('=')[1]
                property_operator = property_reference.split(':')[1]
                property_list = []
                for child in operator_elem:
                    property_name = child.tag.split("}")[-1] 
                    property_list.append(property_name)

                # Edge cases: These operators have hidden properties that are not exposed in the .bonsai XML
                if property_reference == 'gl:WarpPerspective':
                    property_list.append('Destination')
                if property_reference == 'p2:ModelParameters':
                    property_list.append('StateParameters')
                if property_reference == 'p1:KFModelParameters':
                    property_list.append('P')
                    property_list.append('X')

                if property_list:
                    xml_list.append({
                            "type": "PropertyReference",
                            "property_namespace": property_namespace,
                            "property_assembly": property_assembly,
                            'property_operator': property_operator,
                            'property_list': property_list
                        })
        
        # Edge case: PropertySources have a different XML expression format, need to swap Property Values and even Operator Names
        if xsi_type == "PropertySource":
            if expression.get("TypeArguments").split(',')[0] == "gl:LoadImage":
                edge_case_property_name = expression.find("MemberName",xml_namespace).text
                xml_list.append({
                            "type": "PropertyReference",
                            "property_namespace": 'Bonsai.Shaders',
                            "property_assembly": 'Bonsai.Shaders',
                            'property_operator': 'LoadImage',
                            'property_list': ['Value'],
                            'edge_case':True,
                            'edge_case_property_name': edge_case_property_name
                            })
            
            elif expression.get("TypeArguments").split(',')[0] == "drw:AddTextBox":
                edge_case_property_name = expression.find("MemberName",xml_namespace).text
                xml_list.append({
                            "type": "PropertyReference",
                            "property_namespace": 'Bonsai.Vision.Drawing',
                            "property_assembly": 'Bonsai.Vision',
                            'property_operator': 'AddTextBase',
                            'property_list': ['Value'],
                            'edge_case':True,
                            'edge_case_property_name': edge_case_property_name
                            })
        
        # Edge case: Subject operators do not have XML namespace declaration 
        if xsi_type in ['MulticastSubject', 'SubscribeSubject']:
            xml_list.append({
                            "type": "PropertyReference",
                            "property_namespace": 'Bonsai.Expressions',
                            "property_assembly": 'Bonsai.Core',
                            'property_operator': xsi_type,
                            'property_list': ['Name']
                        })
        
        # Edge case: Format operator does not have XML namespace declaration and property child elements
        if xsi_type in ['Format']:
            xml_list.append({
                            "type": "PropertyReference",
                            "property_namespace": 'Bonsai.Expressions',
                            "property_assembly": 'Bonsai.Core',
                            'property_operator': 'FormatBuilder',
                            'property_list': ['Format', 'Selector']
                        })
        
            
        # Finds properties that have been mapped and are thus hidden or represented by some other property name           
        if xsi_type == "PropertyMapping":
            for prop in expression.findall(f".//{{{default_ns}}}PropertyMappings/{{{default_ns}}}Property"):
                property_name = prop.get('Name')
                property_mapping_list.append(property_name)


    # Remove mapped properties from XML list
    for prop in property_mapping_list[:]:
        if prop in properties_to_keep:
            property_mapping_list.remove(prop)
    
    for prop in xml_list[:]:
        if prop.get("display_name") in property_mapping_list:
            xml_list.remove(prop) 

    # Go through XML list and extract description for relevant properties
    processed_properties = {}
    index = -1
    for potential_property in xml_list[:]:
        index += 1
        if potential_property['type'] == 'ExternalizedMapping':
            if potential_property['description'] == False:

                description = False
                
                # This section checks any embedded IncludeWorkflows to see if the property description is defined there instead 
                if stop_recursion == False:
                    for file in include_workflow_list:
                        _, temp_property= extract_information_from_bonsai(file, src_folder, stop_recursion = True)
                        description = temp_property.get(potential_property['property_name'], False)
                        if description:
                            break
                
                # This section checks any subsequent PropertyReferences to see if the property description is defined there instead 
                if description == False:
                    for potential_source in xml_list[index+1:]:
                        if potential_source['type'] == "PropertyReference":
                            if potential_property['property_name'] in potential_source['property_list']:

                                # Uses a CS file extractor if the PropertyReference is within the library, but the check could be more robust
                                if potential_source['property_assembly'] in entry:
                                    description = extract_information_from_cs(potential_source['property_namespace'], potential_source['property_assembly'], potential_source['property_operator'], src_folder, potential_property['property_name'])
                                    if description:
                                        break
                                
                                # Uses a package file extractor 
                                else:
                                    if potential_source.get('edge_case'):
                                        description = extract_information_from_package(potential_source['property_namespace'], potential_source['property_assembly'], potential_source['property_operator'], potential_source['edge_case_property_name'])
                                    else:
                                        description = extract_information_from_package(potential_source['property_namespace'], potential_source['property_assembly'], potential_source['property_operator'], potential_property['property_name'])
                                    if description:
                                        break
                
                # Bunch of checks to make sure that it only overwrites previous declarations if they are empty and if it itself is not empty.
                if description:
                    if potential_property["display_name"] == False:
                        if not processed_properties.get(potential_property["property_name"]): 
                            processed_properties[potential_property["property_name"]] = description
                    else:
                        if not processed_properties.get(potential_property["display_name"]):
                            processed_properties[potential_property["display_name"]] = description
            else:
                if potential_property["display_name"] == False:
                    processed_properties[potential_property["property_name"]] = potential_property['description']
                else:
                    processed_properties[potential_property["display_name"]] = potential_property['description']
    return(operator_description, processed_properties)

        
def main():
    src_folder = "../src"  # Adjust if your src folder is in a different location
    toc_path = "api/toc.yml"  # Path to the existing TOC file
    manifest_path ="api/.manifest" 
    api_folder = "api/"

    # Find all .bonsai files in the src folder
    bonsai_files = find_bonsai_files(src_folder)
    print(f"Found {len(bonsai_files)} .bonsai files.")

    # Get git information to populate .yml source field
    branch_name, repo_url = get_git_information()

    # Generate entries from .bonsai file list to feed into create_bonsai_yml
    new_entries = generate_entries(bonsai_files, src_folder)

    # Create .bonsai .yml files
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