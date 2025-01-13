# docfx-tools

A repository of docfx tools for Bonsai package documentation:
- Docfx Workflow Container template patching the modern template to provide stylesheets and scripts for rendering custom workflow containers with copy functionality. 
- Docfx API TOC template that groups nodes by operator type in the table of contents(TOC) on API pages.
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
## Using API TOC Template

The local installation of docfx needs to be updated to >= v2.77.0.

```ps1
dotnet tool update docfx
```

Modify `docfx.json` to include the api-toc template (note both the workflow container and API TOC template have to be added separately).

```json
"template": [
  "default",
  "modern",
  "bonsai/template", 
  "bonsai/template/apitoc", 
  "template"
]
```

## Powershell Scripts - Exporting workflow images

Exporting SVG images for all example workflows can be automated by placing all `.bonsai` files in a `workflows` folder and calling the below script pointing to the bin directory to include. A bonsai environment is assumed to be available in the `.bonsai` folder in the repository root.

```ps1
.\modules\Export-Image.ps1 "..\src\PackageName\bin\Release\net472"
```