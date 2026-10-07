# docfx-tools

A docfx template for package documentation, patching the modern template to provide stylesheets and scripts for rendering custom workflow containers with copy functionality.

## How to use

To include this template in a docfx website, first clone this repository as a submodule:

```
git submodule add https://github.com/bonsai-rx/docfx-tools bonsai-docfx
```

Then modify `docfx.json` to include the template immediately after the modern template:

```json
    "template": [
      "default",
      "modern",
      "bonsai-docfx/template",
      "template"
    ],
```

Finally, import and call the modules inside your website `template/public` folder.

#### main.css
```css
@import "bonsai.css";
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

## Scripts

This repository also provides helper scripts to automate several content generation steps for package documentation websites.

The PowerShell scripts require [PowerShell 7.4 or later](https://learn.microsoft.com/powershell/scripting/install/install-powershell), which is preinstalled on GitHub-hosted runners. Run them with `pwsh` rather than `powershell`, since `powershell` launches Windows PowerShell 5.1, which is not supported.

### Exporting workflow images

Exporting SVG images for all example workflows can be automated by placing all `.bonsai` files in a `workflows` folder and calling the below script pointing to the bin directory to include. A bonsai environment is assumed to be available in the `.bonsai` folder in the repository root.

```ps1
.\scripts\Export-Image.ps1 "..\src\PackageName\bin\Release\net472"
```

### Generating a Python API reference

The `generate-python-api.py` script writes the API reference of a Python package as DocFX UniversalReference pages. The script declares its own dependencies, so it runs with [uv](https://docs.astral.sh/uv/) without further setup. All arguments are optional and default to values derived from the repository. Run the script with `--help` for details.

```ps1
uv run --locked .\scripts\generate-python-api.py
```

Include the generated files in the `build.content` section of `docfx.json`:

```json
      {
        "src": "../artifacts/docs/python/",
        "dest": "python",
        "files": "**/*.yml"
      }
```

Then add the API reference to the top-level `toc.yml`:

```yml
- name: Python API
  href: ../artifacts/docs/python/
```