# /// script
# requires-python = ">=3.11"
# dependencies = ["griffelib>=2.3", "pyyaml>=6"]
# ///
"""Generates DocFX UniversalReference YAML for the public API of one or more Python packages.

Each package is loaded statically by griffe and is never imported. Its public API is the
`__all__` of the package, or its public members when `__all__` is absent. Every object is
documented under the path of its package, so a class re-exported from a submodule has a single
page.

Docstrings are read in the Google style. A backticked name links to its page when it resolves
to an object documented by the packages, and mkdocstrings cross-references such as
[text][path] link to the object at the specified path.

The table of contents has a node for each package, with its classes below it. For a single
package, --flat-toc lists the classes alone, to include the reference in another table of
contents.

All arguments are optional, and the script can run from any folder of the repository. Search
paths and the output folder are relative to the repository root, and source links point to the
web URL and branch reported by GitHub Actions or by git.

The [tool.docfx-tools] table can specify the package, or a list of packages, and list Sphinx
inventories for linking type names from other packages. It is read from the nearest
pyproject.toml above a search path that declares it, up to the repository root:

    [tool.docfx-tools]
    package = "mypackage"
    inventories = ["https://docs.pydantic.dev/latest/objects.inv"]
"""

import argparse
import os
import re
import subprocess
import sys
import tomllib
import urllib.request
import zlib
from pathlib import Path

import griffe
import yaml

LANG = "python"


class Generator:
    def __init__(self, package, repo=None, branch=None, repo_root=None, inventory=None, uids=None):
        self.package = package
        self.repo = repo
        self.branch = branch
        self.repo_root = Path(repo_root).resolve() if repo_root else None
        self.inventory = inventory or {}
        self.uids = {} if uids is None else uids
        self.objects = {}
        self.references = {}

    def collect(self):
        names = self.package.exports or [
            name for name, member in self.package.members.items() if member.is_public
        ]
        for name in names:
            member = self.package.members[name]
            target = member.final_target if member.is_alias else member
            if target.is_module:
                continue
            uid = f"{self.package.path}.{name}"
            self.objects[uid] = target
            if target.path.startswith(f"{self.package.path}.") or target.path not in self.uids:
                self.uids[target.path] = uid
                if target.is_class:
                    for child_name, child in self.class_members(target):
                        self.uids[child.path] = f"{uid}.{child_name}"

    def class_members(self, cls):
        described = self.attribute_descriptions(cls)
        is_enum = self.is_enum(cls)
        for name, member in cls.members.items():
            if member.is_alias or (member.is_attribute and member.docstring is None and name not in described and not is_enum):
                continue
            if name == "__init__" or not name.startswith("_"):
                yield name, member

    @staticmethod
    def is_enum(cls):
        """Returns whether a class derives directly from an enum type of the standard library."""
        return any(str(getattr(base, "canonical_path", base)).startswith("enum.") for base in cls.bases)

    @staticmethod
    def attribute_descriptions(obj):
        """Returns the descriptions in the Attributes section of a docstring, by attribute name."""
        if obj.docstring is None:
            return {}
        return {
            attribute.name: attribute.description
            for section in obj.docstring.parsed
            if section.kind.value == "attributes"
            for attribute in section.value
        }

    def uid_of(self, path):
        return self.uids.get(path, path)

    def markdown(self, text, scope=None):
        """Links backticked names and mkdocstrings cross-references to their uids."""
        if not text:
            return None
        parts = re.split(r"(```.*?```)", text, flags=re.S)
        for index in range(0, len(parts), 2):
            part = parts[index]
            part = re.sub(
                r"\[([^\]]+)\]\[([\w.]*)\]",
                lambda m: f"[{m.group(1)}](xref:{self.uid_of(m.group(2) or m.group(1).strip('`'))})",
                part,
            )
            part = re.sub(r"(?<![`\[])`([A-Za-z_][\w.]*)`(?![`\]])", lambda m: self.code_link(m, scope), part)
            parts[index] = part
        return "".join(parts)

    def code_link(self, match, scope):
        name = match.group(1)
        candidates = [name, f"{self.package.path}.{name}"]
        if scope is not None:
            candidates.insert(0, f"{scope}.{name}")
        for candidate in candidates:
            if candidate in self.objects:
                return f"[`{name}`](xref:{self.uid_of(self.objects[candidate].path)})"
            if candidate in self.uids.values():
                return f"[`{name}`](xref:{candidate})"
        return match.group(0)

    def type_uid(self, annotation):
        """Returns the uid of an annotation, and adds a reference for a composite one."""
        if annotation is None:
            return None
        if isinstance(annotation, str):
            return annotation
        if isinstance(annotation, griffe.ExprName):
            uid = self.uid_of(annotation.canonical_path)
            self.reference(uid, annotation.name)
            return uid
        spec = []
        for part in annotation.iterate(flat=True):
            if isinstance(part, griffe.ExprName):
                uid = self.uid_of(part.canonical_path)
                self.reference(uid, part.name)
                spec.append({"uid": uid, "name": part.name, "fullName": uid})
            else:
                spec.append({"name": str(part), "fullName": str(part)})
        uid = str(annotation)
        self.references[uid] = {
            "uid": uid,
            "name": uid,
            "fullName": uid,
            "spec.python": spec,
        }
        return uid

    def reference(self, uid, name):
        if uid in self.references:
            return
        reference = {"uid": uid, "name": name, "fullName": uid}
        if uid not in self.uids.values() and uid not in self.objects:
            reference["isExternal"] = True
            href = self.inventory.get(uid)
            if href:
                reference["href"] = href
        self.references[uid] = reference

    def sections(self, obj):
        result = {"summary": [], "parameters": {}, "returns": None, "raises": [], "examples": [], "remarks": []}
        if obj.docstring is None:
            return result
        for section in obj.docstring.parsed:
            kind = section.kind.value
            if kind == "text":
                result["summary"].append(section.value)
            elif kind in ("parameters", "other parameters"):
                for parameter in section.value:
                    result["parameters"][parameter.name] = parameter.description
            elif kind in ("returns", "yields"):
                result["returns"] = " ".join(item.description for item in section.value)
            elif kind == "raises":
                result["raises"].extend(section.value)
            elif kind == "examples":
                for item_kind, value in section.value:
                    if item_kind.value == "examples":
                        result["examples"].append(f"```python\n{value}\n```")
                    else:
                        result["examples"].append(value)
            elif kind == "admonition":
                title = section.title or section.value.kind
                result["remarks"].append(f"> [!NOTE]\n> **{title}**\n>\n> " + section.value.description.replace("\n", "\n> "))
        return result

    def source(self, obj):
        if not (self.repo and self.repo_root and obj.filepath):
            return None
        path = Path(obj.filepath).resolve().relative_to(self.repo_root).as_posix()
        line = obj.lineno or 1
        return {
            "id": obj.name,
            "path": path,
            "startLine": line - 1,
            "href": f"{self.repo}/blob/{self.branch}/{path}#L{line}",
        }

    def item(self, uid, obj, kind, parent, scope=None, description=None):
        docs = self.sections(obj)
        if not docs["summary"] and description:
            docs["summary"].append(description)
        item = {
            "uid": uid,
            "id": uid.rpartition(".")[2],
            "name": uid.rpartition(".")[2],
            "fullName": uid,
            "parent": parent,
            "type": kind,
            "langs": [LANG],
            "summary": self.markdown("\n\n".join(docs["summary"]), scope),
        }
        source = self.source(obj)
        if source:
            item["source"] = source
        if docs["remarks"]:
            item["remarks"] = self.markdown("\n\n".join(docs["remarks"]), scope)
        if docs["examples"]:
            item["example"] = [self.markdown(example, scope) for example in docs["examples"]]
        if docs["raises"]:
            item["exceptions"] = [
                {"type": self.type_uid(entry.annotation), "description": self.markdown(entry.description, scope)}
                for entry in docs["raises"]
            ]
        syntax = {}
        if obj.is_function:
            syntax["content"] = self.signature(uid.rpartition(".")[2], obj, kind)
            parameters = []
            for parameter in obj.parameters:
                if parameter.name in ("self", "cls") and kind in ("method", "constructor"):
                    continue
                entry = {"id": self.parameter_name(parameter)}
                if parameter.annotation is not None:
                    entry["type"] = [self.type_uid(parameter.annotation)]
                description = docs["parameters"].get(parameter.name)
                if description:
                    entry["description"] = self.markdown(description, scope)
                if parameter.default is not None and parameter.kind.value not in ("variadic positional", "variadic keyword"):
                    entry["defaultValue"] = str(parameter.default)
                    entry["optional"] = True
                parameters.append(entry)
            if parameters:
                syntax["parameters"] = parameters
            if obj.returns is not None and kind != "constructor":
                syntax["return"] = {"type": [self.type_uid(obj.returns)]}
                if docs["returns"]:
                    syntax["return"]["description"] = self.markdown(docs["returns"], scope)
        elif obj.is_attribute:
            text = obj.name
            if obj.annotation is not None:
                text += f": {obj.annotation}"
            instance_only = "instance-attribute" in obj.labels and "class-attribute" not in obj.labels
            if obj.value is not None and not instance_only:
                text += f" = {obj.value}"
            syntax["content"] = text
        elif obj.is_class:
            bases = ", ".join(str(base) for base in obj.bases)
            syntax["content"] = f"class {obj.name}({bases})" if bases else f"class {obj.name}"
        if syntax:
            item["syntax"] = syntax
        return {key: value for key, value in item.items() if value is not None}

    def signature(self, name, function, kind):
        parameters = []
        star = False
        for parameter in function.parameters:
            if parameter.name in ("self", "cls") and kind in ("method", "constructor"):
                continue
            if parameter.kind.value == "keyword-only" and not star:
                parameters.append("*")
                star = True
            if parameter.kind.value == "variadic positional":
                star = True
            text = self.parameter_name(parameter)
            if parameter.annotation is not None:
                text += f": {parameter.annotation}"
            if parameter.default is not None and parameter.kind.value not in ("variadic positional", "variadic keyword"):
                text += f" = {parameter.default}" if parameter.annotation is not None else f"={parameter.default}"
            parameters.append(text)
        if kind == "constructor":
            return f"{name.rpartition('.')[0] or function.parent.name}({', '.join(parameters)})"
        returns = f" -> {function.returns}" if function.returns is not None else ""
        return f"def {name}({', '.join(parameters)}){returns}"

    @staticmethod
    def parameter_name(parameter):
        prefix = {"variadic positional": "*", "variadic keyword": "**"}.get(parameter.kind.value, "")
        return prefix + parameter.name

    def package_page(self):
        self.references = {}
        package_uid = self.package.path
        children, items = [], []
        described = self.attribute_descriptions(self.package)
        package = self.item(package_uid, self.package, "package", None)
        package.pop("parent", None)
        package["name"] = package_uid
        package.pop("syntax", None)
        for uid, obj in self.objects.items():
            children.append(uid)
            if obj.is_class:
                summary = self.sections(obj)["summary"]
                self.references[uid] = {
                    "uid": uid,
                    "name": obj.name,
                    "fullName": uid,
                    "parent": package_uid,
                    "summary": self.markdown(summary[0].split("\n\n")[0] if summary else "", uid),
                }
            elif obj.is_function:
                items.append(self.item(uid, obj, "function", package_uid))
            elif obj.is_attribute:
                description = described.get(uid.rpartition(".")[2])
                items.append(self.item(uid, obj, "variable", package_uid, description=description))
        package["children"] = children
        return {"items": [package, *items], "references": list(self.references.values())}

    def class_page(self, uid, cls):
        self.references = {}
        item = self.item(uid, cls, "enum" if self.is_enum(cls) else "class", self.package.path, scope=uid)
        bases = [self.type_uid(base) for base in cls.bases]
        if bases:
            item["inheritance"] = [{"type": base} for base in bases]
        children, members = [], []
        described = self.attribute_descriptions(cls)
        for name, member in self.class_members(cls):
            member_uid = f"{uid}.{name}"
            if name == "__init__":
                kind = "constructor"
            elif member.is_function:
                kind = "property" if "property" in member.labels else "method"
            elif member.is_attribute:
                kind = "field"
            else:
                continue
            entry = self.item(member_uid, member, kind, uid, scope=uid, description=described.get(name))
            if kind == "constructor":
                entry["name"] = cls.name
            members.append(entry)
            children.append(member_uid)
        if children:
            item["children"] = children
        return {"items": [item, *members], "references": list(self.references.values())}

    def toc(self, flat=False):
        classes = [{"uid": uid, "name": obj.name} for uid, obj in self.objects.items() if obj.is_class]
        if flat:
            return classes
        return [{"uid": self.package.path, "name": self.package.path, "items": classes}]

    def write(self, output):
        output = Path(output)
        output.mkdir(parents=True, exist_ok=True)
        pages = {self.package.path: self.package_page()}
        for uid, obj in self.objects.items():
            if obj.is_class:
                pages[uid] = self.class_page(uid, obj)
        for uid, page in pages.items():
            with open(output / f"{uid}.yml", "w", encoding="utf-8", newline="\n") as file:
                file.write("### YamlMime:UniversalReference\n")
                yaml.safe_dump(page, file, sort_keys=False, allow_unicode=True, width=1000)
        return list(pages)


def write_toc(output, items):
    with open(Path(output) / "toc.yml", "w", encoding="utf-8", newline="\n") as file:
        file.write("### YamlMime:TableOfContent\n")
        yaml.safe_dump(items, file, sort_keys=False)


def load_inventory(url):
    """Reads a Sphinx objects.inv inventory into a map from object name to URL."""
    request = urllib.request.Request(url, headers={"User-Agent": "generate-python-api"})
    with urllib.request.urlopen(request) as response:
        data = response.read()
        url = response.geturl()
    lines = data.split(b"\n", 4)
    body = zlib.decompress(lines[4]).decode("utf-8")
    base = url.rsplit("/", 1)[0] + "/"
    result = {}
    for line in body.splitlines():
        match = re.match(r"(.+?)\s+(\S+):(\S+)\s+(-?\d+)\s+(\S+)\s+(.*)", line)
        if not match:
            continue
        name, domain, _, _, location, _ = match.groups()
        if domain != "py":
            continue
        if location.endswith("$"):
            location = location[:-1] + name
        result.setdefault(name, base + location)
    return result


PYTHON_INVENTORY = "https://docs.python.org/3/objects.inv"


def git(*args, cwd=None):
    """Returns the output of a git command, or None when it fails."""
    try:
        result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    except OSError:
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def find_root():
    """Returns the root of the repository that contains the working directory."""
    root = git("rev-parse", "--show-toplevel")
    return Path(root) if root else Path.cwd()


def find_repo(root):
    """Returns the web URL of the repository, from GitHub Actions or the git remote."""
    if os.environ.get("GITHUB_REPOSITORY"):
        server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
        return f"{server}/{os.environ['GITHUB_REPOSITORY']}"
    remote = git("remote", "get-url", "origin", cwd=root)
    if not remote:
        return None
    remote = re.sub(r"^git@([^:]+):", r"https://\1/", remote)
    return remote.removesuffix(".git")


def find_branch(root):
    """Returns the ref used by source links, from GitHub Actions or the checkout."""
    for variable in ("GITHUB_HEAD_REF", "GITHUB_REF_NAME"):
        if os.environ.get(variable):
            return os.environ[variable]
    return git("branch", "--show-current", cwd=root) or "main"


def is_private(directory, root):
    """Returns whether the nearest project above a folder declares a Private trove classifier."""
    root = root.resolve()
    folder = Path(directory).resolve()
    while folder.is_relative_to(root):
        pyproject = folder / "pyproject.toml"
        if pyproject.is_file():
            project = tomllib.loads(pyproject.read_text(encoding="utf-8")).get("project")
            if project is not None:
                return any(classifier.startswith("Private ::") for classifier in project.get("classifiers", []))
        folder = folder.parent
    return False


def find_packages(root, search_paths):
    """Returns every importable package under the search paths, except those of private projects."""
    candidates = []
    for search_path in search_paths:
        pending = [Path(search_path)]
        while pending:
            directory = pending.pop()
            for child in sorted(directory.iterdir()):
                if not child.is_dir() or not child.name.isidentifier():
                    continue
                if (child / "__init__.py").is_file():
                    if not is_private(child, root):
                        candidates.append(".".join(child.relative_to(search_path).parts))
                else:
                    pending.append(child)
    if not candidates:
        raise SystemExit(f"Expected a package under {search_paths}, found none. Specify it explicitly.")
    return candidates


def read_table(pyproject):
    """Returns the [tool.docfx-tools] table of a pyproject.toml file."""
    if not pyproject.is_file():
        return {}
    return tomllib.loads(pyproject.read_text(encoding="utf-8")).get("tool", {}).get("docfx-tools", {})


def read_settings(root, search_paths):
    """Returns the nearest [tool.docfx-tools] table above a search path, up to the repository root."""
    root = root.resolve()
    for search_path in search_paths:
        folder = Path(search_path).resolve()
        while folder.is_relative_to(root):
            settings = read_table(folder / "pyproject.toml")
            if settings:
                return settings
            folder = folder.parent
    return read_table(root / "pyproject.toml")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "packages",
        nargs="*",
        metavar="package",
        help="Import path of a package. Defaults to the packages specified in [tool.docfx-tools], "
        "then to every importable package under the search paths, except those of projects with a "
        "Private trove classifier.",
    )
    parser.add_argument(
        "--search-path",
        action="append",
        metavar="DIR",
        help="Folder to search for the package. Can be repeated. Defaults to src.",
    )
    parser.add_argument(
        "--output",
        metavar="DIR",
        help="Folder for the generated YAML files. Defaults to artifacts/docs/python.",
    )
    parser.add_argument(
        "--repo",
        metavar="URL",
        help="Web URL of the repository for source links. Defaults to the repository reported by "
        "GitHub Actions, then to the origin remote.",
    )
    parser.add_argument(
        "--branch",
        metavar="NAME",
        help="Branch or tag for source links. Defaults to the ref reported by GitHub Actions, "
        "then to the current branch, then to main.",
    )
    parser.add_argument(
        "--repo-root",
        metavar="DIR",
        help="Root of the repository. Defaults to the root reported by git, then to the working directory.",
    )
    parser.add_argument(
        "--inventory",
        action="append",
        default=[],
        metavar="URL",
        help="Additional Sphinx inventory for linking type names. Can be repeated. Adds to the "
        "inventories listed in [tool.docfx-tools] and to the inventory of the Python standard library.",
    )
    parser.add_argument(
        "--flat-toc",
        action="store_true",
        help="List the classes of a single package as the top-level items of the table of contents, "
        "without a node for the package.",
    )
    args = parser.parse_args()

    root = Path(args.repo_root) if args.repo_root else find_root()
    search_paths = [str(root / path) for path in (args.search_path or ["src"])]
    settings = read_settings(root, search_paths)
    output = root / (args.output or "artifacts/docs/python")
    repo = args.repo or find_repo(root)
    branch = args.branch or find_branch(root)
    package_names = args.packages or settings.get("package") or find_packages(root, search_paths)
    if isinstance(package_names, str):
        package_names = [package_names]
    if args.flat_toc and len(package_names) > 1:
        raise SystemExit(f"--flat-toc requires a single package, found {', '.join(package_names)}.")

    inventory = {}
    for url in [PYTHON_INVENTORY, *settings.get("inventories", []), *args.inventory]:
        inventory.update(load_inventory(url))
    loader = griffe.GriffeLoader(search_paths=search_paths, docstring_parser="google")
    packages = [loader.load(package_name) for package_name in package_names]
    uids = {}
    generators = [Generator(package, repo, branch, root, inventory, uids) for package in packages]
    for generator in generators:
        generator.collect()
    pages = [page for generator in generators for page in generator.write(output)]
    write_toc(output, [item for generator in generators for item in generator.toc(args.flat_toc)])
    print(f"Wrote {len(pages)} pages for {', '.join(package_names)} to {output}", file=sys.stderr)


if __name__ == "__main__":
    main()
