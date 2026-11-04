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

Exporting SVG images for all example workflows can be automated by placing all `.bonsai` files in a `workflows` folder and calling the below script pointing to the bin directory to include. A bonsai environment is assumed to be available in the `.bonsai` folder in the repository root. Run `Get-Help` on the script for details.

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

The script documents every package found under the search paths, unless the packages are specified as arguments or in `[tool.docfx-tools]`. Packages of a project that declares a `Private ::` classifier, such as `Private :: Do Not Upload`, are left out. The generated table of contents has a node for each package, with its classes below it.

To add the API reference of a single package as a section of another table of contents, run the script with `--flat-toc` so the classes are listed without a node for the package. Then set `href` to the generated `toc.yml` instead of its folder, and use `topicUid` to open the package page:

```yml
- name: Python API
  href: ../artifacts/docs/python/toc.yml
  topicUid: mypackage
```

## Extending UniversalReference pages

A custom template listed after `bonsai-docfx/template` can transform UniversalReference pages without replacing `UniversalReference.extension.js`. Add a module named `UniversalReference.{name}.js` to the template, where the name is anything other than `common` or `extension`, and assign a `preTransform` or `postTransform` function to `exports`:

```js
exports.postTransform = function (model) {
  return model;
}
```

Then register the module in the `token.json` of the template, under a key that ends in `UniversalReferenceTransform`:

```json
{
  "exampleUniversalReferenceTransform": "UniversalReference.example.js"
}
```

Registered transforms run after the transforms of this template, in the order of their templates in `docfx.json`. Every transform runs on every UniversalReference page, so a transform for one kind of page should return any other page unchanged. A template that declares the same key as an earlier template replaces its transform.

### Rendering a page as tables

A transform can render a page as a set of tables by assigning a `tableReference` object to the model. The page keeps its own title, summary, conceptual content and remarks, and any members left in `children` are listed after the tables. Enum pages of the Python API reference use this to list their values.

```js
model.tableReference = {
  tables: [{
    level: 2,
    id: 'values',
    heading: 'Values',
    intro: '',
    columns: [{ header: 'Name' }, { header: 'Value' }],
    rows: [{ id: 'Red', uid: 'example.Color.Red', cells: [{ html: '<code>Red</code>' }, { html: '1' }] }]
  }]
};
```

Each table is rendered with a section heading of the specified `level`, followed by the `intro` paragraph when it is not empty. A row with a non-empty `uid` becomes the anchor of that UID, so links to it resolve. Every table and row has to define all of its properties, even when empty, since a missing value is looked up on the enclosing objects instead.

The `tableReference` object also accepts three optional properties:

- `aliases`, a list of objects with `id` and `uid`, adds anchors for other UIDs that the page documents.
- `details`, a list of objects with `term` and `description`, renders a row of details below the summary.
- `conceptualHeading` adds a section heading above the conceptual content.