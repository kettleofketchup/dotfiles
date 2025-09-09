# Dotfiles and Development Environment Automation

This repository contains personal dotfiles and a set of scripts to automate the setup of a development environment. The automation is orchestrated using the Python `invoke` library.

## Core Concepts

- **Task Runner**: We use `invoke` as a task runner to execute all setup and installation scripts. The main entry point for all tasks is `tasks.py` in the root directory.
- **Centralized Paths**: All important directory and file paths are defined in `paths.py`. This avoids hardcoded paths and provides a single source of truth. Always use the constants from `paths.py` when you need to reference a location in the filesystem.
- **Use Python to run sh commands**: The actual setup logic is contained within python functions that use `invoke`'s `Context.run()` method to execute shell commands. This allows for better error handling and output management.

## Developer Workflow & Conventions

### `invoke` Task Structure

The `invoke` tasks defined in `tasks.py` should mirror the directory structure of the `scripts/` folder. This is achieved by creating nested `Collection`s.

For example, to install & setup python on linux, you should be able to run a command like:

```sh
inv linux.languages.python.install
```

This requires creating a `linux` collection, which contains a `languages` sub-collection, which in turn contains the `python` collection and a `install` task.

### Creating collections

When creating a new collection in `tasks.py`, follow this pattern:
1.  Import the necessary path from the `paths` module.
2.  Create a `Collection` object for the new collection with a ns_ prefix.
    - ns_collection_name = Collection("collection_name")

3.  Add tasks to the collection using the `@task` decorator.

### Creating Tasks

When creating a new task in `tasks.py` that runs a shell script, follow this pattern:

1.  Import the necessary path from the `paths` module.
2.  Use a `with c.cd(path):` block to ensure the command runs in the correct directory.
3.  Use `c.run()` to execute the script.

**Example `tasks.py` snippet:**

```python
from invoke import task, Collection
from paths import SCRIPTS_LINUX_LANGUAGES
ns_python = Collection("python")

@task
def install(c):
    """Installs Python build dependencies and pyenv."""
    with c.cd(BASE_DIR):
        c.sudo("./apt install python3 python3-pip python3-venv")

python

# In the main namespace/collection
# ...
languages = Collection("languages", python)
linux = Collection("linux", languages)
ns.add_collection(linux)
```

### Key Files & Directories

- `tasks.py`: Main entry point for all `invoke` tasks.
- `paths.py`: Single source of truth for all file and directory paths.
- `scripts/`: Contains all the shell scripts that perform the actual setup work.
- `pyproject.toml`: Defines project dependencies, most importantly `invoke`.
- use `uv add dependency` to add new dependencies.
- try to limit adding new dependencies unless absolutely necessary.

# Execution

To execute the tasks defined in `tasks.py`, use `uv run inv`, with the collection path followed by the task name. For example:

```sh
uv run inv linux.languages.python.install
```

This will run the `install` task for the Python language on Linux.