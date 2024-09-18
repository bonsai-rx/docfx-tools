import json
import os

# Define folder constants
current_dir = os.getcwd()
docs_dir = os.path.dirname(os.path.dirname(current_dir))

# Load docfx.json file
try:
    with open(os.path.join(docs_dir, "docfx.json"), 'r') as file:
        data = json.load(file)
except FileNotFoundError:
    exit_string = "expected docfx.json at " + (os.path.join(docs_dir, "docfx.json") + ", run docfx first to create docfx.json file")
    print(exit_string)
    os.exit(1)

# Add filtering option to avoid documenting operators that are no longer supported 
# but included in the package for backwards compatibility. Can also be used 
# to hide private classes that are not supposed to be shown to the end user.
# Make sure a filter.yml is created in docs/filter.yml
data["metadata"][0]["filter"] = "filter.yml"

# Exclude filter.yml and apidoc folder from build process
# apidoc- this avoids duplicate UID errors from files in the apidoc
# The overwrite mechanism still works
data["build"]["content"][0]["exclude"].extend(
    [file for file in ["filter.yml","apidoc/**"] if file not in data["build"]["content"][0]["exclude"]]
)
                                                  
# Imports site resources
data["build"]["resource"][0]["files"].extend(
    [file for file in ["workflows/**", "logo.svg", "favicon.ico"] if file not in data["build"]["resource"][0]["files"]]
)

# Use docfx overwrite feature to include individual operator articles in API documentation
data["build"]["overwrite"] = [{"files": ["apidoc/**.md"], "exclude": ["obj/**", "_site/**"]}]

# Adds custom docfx templates for workflow containers
data["build"]["template"].extend(
    [item for item in ["bonsai/template", "template"] if item not in data["build"]["template"]]
)

# Adds site footer
data["build"]["globalMetadata"]["_appFooter"] = "&copy; 2024 Bonsai Foundation CIC and Contributors. Made with <a href=\"https://dotnet.github.io/docfx\">docfx</a>"

# Enable markdig extensions for additional markdown functionality
data["build"]["markdownEngineProperties"] = {"markdigExtensions": ["attributes", "customcontainers"]}

# Enable crossreferencing for Bonsai operator Library
data["build"]["xref"] = ["https://bonsai-rx.org/docs/xrefmap.yml"]

# Write docfx.json file
with open(os.path.join(docs_dir, "docfx.json"), 'w') as file:
    json.dump(data, file, indent=2)

# Script termination message
print("docfx.json modified")