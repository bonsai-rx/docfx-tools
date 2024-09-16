# code based on comparing bonsai.gui docfx.json file to a fresh docfx.json (updated 4/27/24)
# might be easier to just copy the docfx.json file but it might change when docfx is updated.
import json
import os

# define folder constants
current_dir = os.getcwd()
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
docs_dir = os.path.join(root_dir,"docs")

# load json file
try:
    with open(os.path.join(docs_dir, "docfx.json"), 'r') as file:
        data = json.load(file)
except FileNotFoundError:
    print("docfx.json not file, run docfx first to create docfx.json file")

# prompt for github website
github_link = input("Please enter the github website")

# adds filter .yml to metadata build
# the structure in the attributes is a bit weird, its a dictionary in a list, so the index [0] is just calling up that dictionary
data["metadata"][0]["filter"] = "filter.yml"

# adds files and folders to be excluded from site building
if "filter.yml" in data["build"]["content"][0]["exclude"]:
    pass
else:
    data["build"]["content"][0]["exclude"].extend(["filter.yml"])
                                                  
if "bonsai/**" in data["build"]["content"][0]["exclude"]:
    pass
else:
    data["build"]["content"][0]["exclude"].extend(["bonsai/**"])

# adds site resources
if "workflows/**" in data["build"]["resource"][0]["files"]:
    pass
else: 
    data["build"]["resource"][0]["files"].extend(["workflows/**"])
    
if "logo.svg" in data["build"]["resource"][0]["files"]:
    pass
else: 
    data["build"]["resource"][0]["files"].extend(["logo.svg"])

if "favicon.ico" in data["build"]["resource"][0]["files"]:
    pass
else: 
    data["build"]["resource"][0]["files"].extend(["favicon.ico"])

# adds overwrite section
data["build"]["overwrite"] = [{"files":["apidoc/**.md"], 
                                 "exclude": ["obj/**", "_site/**"]}]

# adds bonsai templates 
if "bonsai/template" in data["build"]["template"]:
    pass
else:
    data["build"]["template"].extend(["bonsai/template"])
    
if "template" in data["build"]["template"]:
    pass
else:
    data["build"]["template"].extend(["template"])

# adds site footer
data["build"]["globalMetadata"]["_appFooter"] = "&copy; 2024 Bonsai Foundation CIC and Contributors. Made with <a href=\"https://dotnet.github.io/docfx\">docfx</a>"

# adds git contribute section
data["build"]["globalMetadata"]["_gitContribute"] = {"repo": github_link, 
                                                     "branch": "main", 
                                                     "apiSpecFolder": "apidoc"}

# adds markdig extensions
data["build"]["markdownEngineProperties"] = {"markdigExtensions": ["attributes",
                                                                   "customcontainers"]}

# adds xref 
data["build"]["xref"] = ["https://bonsai-rx.org/docs/xrefmap.yml",
                         "https://horizongir.github.io/reactive/xrefmap.yml"]

# write json file
with open(os.path.join(docs_dir, "docfx.json"), 'w') as file:
    json.dump(data, file, indent=2)