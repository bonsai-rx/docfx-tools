# docfx-tools

A repository of docfx tools for Bonsai package documentation:
- Workflow Container Template patching the modern template to provide stylesheets and scripts for rendering custom workflow containers with copy functionality.
- IncludeWorkflow Operator Patch that adds support for Bonsai `IncludeWorkflow` Operators
- Powershell Scripts that automate several content generation steps for package documentation websites.

## How to include

To include this repo in a docfx website, first clone this repository as a submodule:

```
git submodule add https://github.com/bonsai-rx/docfx-tools bonsai
```

## Using Workflow Container Template

Modify `docfx.json` to include the template immediately after the modern template:

```json
    "template": [
      "default",
      "modern",
      "bonsai/template",
      "template"
    ],
```

Finally, import and call the modules inside your website `template/public` folder.

#### main.css
```css
@import "workflow.css";
```

#### main.js
```js
import WorkflowContainer from "./workflow.js"

export default {
    start: () => {
        WorkflowContainer.init();
    }
}
```

## Using IncludeWorkflow Operator Patch

This patch adds support for [IncludeWorkflow](https://bonsai-rx.org/docs/api/Bonsai.Expressions.IncludeWorkflowBuilder.html) operators if they are included in your package. This patch requires a [Python](https://www.python.org/) installation and the [PyYAML](https://pypi.org/project/PyYAML/) package.

1) Assuming you already have `Python` installed, install pyyaml: 

```cmd
pip install pyyaml
```

2) Instead of running `dotnet docfx` which executes the standard `docfx` pipeline, run these commands instead to inject the patch:

```cmd
cd docs
dotnet docfx metadata      
python bonsai/template/api/plugins/Patch-IncludeWorkflow.py 
dotnet docfx build         
dotnet docfx serve _site   
```

- The `metadata` command generates [.yaml](https://dotnet.github.io/docfx/docs/dotnet-yaml-format.html) files for standard operators (C# .cs files) as well as the table of contents (TOC).
- The `Patch-IncludeWorkflow.py` file generates `.yaml` files for `IncludeWorkflow` .bonsai operators and modifies the TOC.
- The `build` command generates `.html` files from `.yaml` and places them in a `_site` folder in `docs`.
- The `serve` command serves a local preview of the website from `_site`.

3) The `dotnet docfx` command in the `docs/build.ps1` script that is used to build the `docfx` website on GitHub needs to be modified with:

```ps1
dotnet docfx metadata
python ./bonsai/template/api/plugins/Patch-IncludeWorkflow.py
dotnet docfx build
```

4) Lastly, the GitHub Actions recipe `.github/workflows/docs.yml` needs to have these lines added before the execution of the `build.ps1` script.

```yaml
    - name: Setup Python 
    uses: actions/setup-python@v5
    with: 
        python-version: '3.12'
    
    - name: Setup Pyyaml
    run: pip install pyyaml==6.0.2
```

## Powershell Scripts - Exporting workflow images

Exporting SVG images for all example workflows can be automated by placing all `.bonsai` files in a `workflows` folder and calling the below script pointing to the bin directory to include. A bonsai environment is assumed to be available in the `.bonsai` folder in the repository root.

```ps1
.\modules\Export-Image.ps1 "..\src\PackageName\bin\Release\net472"
```