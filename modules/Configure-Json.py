import json
import os

# define folder constants
current_dir = os.getcwd()
docs_dir = os.path.dirname(os.path.dirname(current_dir))

# load json file
try:
    with open(os.path.join(docs_dir, "docfx.json"), 'r') as file:
        data = json.load(file)
except FileNotFoundError:
    exit_string = "expected docfx.json at " + (os.path.join(docs_dir, "docfx.json") + ", run docfx first to create docfx.json file")
    print(exit_string)
    os.exit(1)

# adds filter .yml to metadata build
data["metadata"][0]["filter"] = "filter.yml"

# adds filter.yml to be excluded from site building
if "filter.yml" not in data["build"]["content"][0]["exclude"]:
    data["build"]["content"][0]["exclude"].append("filter.yml")
                                                  
# adds site resources
data["build"]["resource"][0]["files"].extend(
    [file for file in ["workflows/**", "logo.svg", "favicon.ico"] if file not in data["build"]["resource"][0]["files"]]
)

# adds overwrite section
data["build"]["overwrite"] = [{"files":["apidoc/**.md"], 
                                 "exclude": ["obj/**", "_site/**"]}]

# adds bonsai templates 
data["build"]["template"].extend(
    [item for item in ["bonsai/template", "template"] if item not in data["build"]["template"]]
)

# adds site footer
data["build"]["globalMetadata"]["_appFooter"] = "&copy; 2024 Bonsai Foundation CIC and Contributors. Made with <a href=\"https://dotnet.github.io/docfx\">docfx</a>"

# adds markdig extensions
data["build"]["markdownEngineProperties"] = {"markdigExtensions": ["attributes", "customcontainers"]}

# adds xref 
data["build"]["xref"] = ["https://bonsai-rx.org/docs/xrefmap.yml"]

# write json file
with open(os.path.join(docs_dir, "docfx.json"), 'w') as file:
    json.dump(data, file, indent=2)