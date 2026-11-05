# github templates

`shadlet create` can scaffold a project from a public or private github
repository, a pinned ref, or a subdirectory inside a repository:

```bash
shadlet create my-app --template owner/repo
shadlet create my-app --template owner/repo#v1.2.0
shadlet create my-app --template owner/repo/examples/dashboard#main
shadlet create my-app --template https://github.com/owner/repo/tree/main/examples/dashboard
```

use a tag or commit ref for reproducible builds. unpinned references use the
repository's current default branch. private repositories can use the
`GITHUB_TOKEN` environment variable or the `--token` option; prefer the
environment variable to avoid exposing tokens in shell history or process
arguments.

## manifest

a template may include `shadlet-template.toml` at its root. the manifest is
validated before the project is considered created. these are the supported
fields:

```toml
[template]
name = "dashboard"
description = "a dashboard starter"
version = "1.2.0"
author = "example team"
min_shadlet = "0.6.0"

[variables]
title = "my dashboard"
project_name = "my-dashboard"
```

| field | behavior |
|---|---|
| `template.name` | required template identity; shown in the create result |
| `template.description` | optional description shown after successful creation |
| `template.version` | semantic version shown in the create result |
| `template.author` | optional author shown in the create result |
| `template.min_shadlet` | minimum semantic version; creation fails if the installed shadlet is older |
| `[variables]` | string defaults substituted in UTF-8 text files using `{{ variable_name }}` |

`project.name` is accepted as a compatibility fallback when `template.name`
is not present; declaring both is an error. fields and sections not listed
above are rejected instead of silently ignored. dependency installation is not
part of the template manifest: put Python dependencies in the generated
`pyproject.toml` and JavaScript dependencies in `package.json` when the project
needs them. `shadlet create` does not install packages or execute
template-provided setup scripts.

declare variables in `[variables]`, then use their names inside text files:

```python
app = ui.App("{{ title }}")
```

override declared defaults during creation with repeatable `--var` options:

```bash
shadlet create acme-dashboard \
  --template owner/repo/examples/dashboard#v1.2.0 \
  --var "title=acme dashboard" \
  --var project_name=acme-dashboard
```

the project name supplied to `shadlet create` automatically overrides a
declared `project_name` variable unless `--var project_name=...` is provided.
unknown variable overrides and declared variables that are never used in a
UTF-8 text file are errors. substitutions apply to UTF-8 text files; binary
assets are left unchanged. placeholders that do not name a declared variable
remain unchanged, so template authors should declare every variable they use.

templates without a manifest remain supported. shadlet writes a default
manifest with the repository identity and version requirements. use a manifest
when the template needs variable substitution or a higher minimum shadlet
version.

## archive and manifest validation

downloads are limited to 50 MiB and extracted content to 100 MiB. archives
containing links, device files, absolute paths, traversal segments, or Windows
drive paths are rejected. symlinks in a local template directory are rejected.
manifest TOML types, semantic versions, supported keys, and variable names are
validated before substitution.

the `--target` directory must not already exist. creation failures are reported
and partial output created by the CLI is removed. template dependencies and
setup scripts are never executed automatically; review remote template source
before running any code it contains.
