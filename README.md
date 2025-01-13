# docfx-tools

A repository of docfx tools for Bonsai package documentation:
- Docfx Workflow Container template patching the modern template to provide stylesheets and scripts for rendering custom workflow containers with copy functionality. 
- Docfx API TOC template that groups nodes by operator type in the table of contents(TOC) on API pages.
- Docfx API template that revamps the API page to enhance user-friendliness.
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
## Using API template

Modify `docfx.json` to include the api template in the template section (note both the workflow container and API template have to be added separately).

```json
"template": [
  "default",
  "modern",
  "bonsai/template", 
  "bonsai/template/api", 
  "template"
]
```
In addition, the images and custom css styles need to be added to the resources section.

```json
"resource": [
    {
    "files": [
        "logo.svg",
        "favicon.ico",
        "images/**",
        "workflows/**",
        "bonsai/template/api/images/**",
        "bonsai/template/api/styles/**"
    ]
    }
]
```
To add individual operator workflows for the API pages, open Bonsai, add the operator, and save each individual operator workflow as `OperatorName.bonsai` (case sensitive) in `docs/workflows/operators`.


## Powershell Scripts - Exporting workflow images

Exporting SVG images for all example workflows can be automated by placing all `.bonsai` files in a `workflows` folder and calling the below script pointing to the bin directory to include. A bonsai environment is assumed to be available in the `.bonsai` folder in the repository root.

```ps1
.\modules\Export-Image.ps1 "..\src\PackageName\bin\Release\net472"
```