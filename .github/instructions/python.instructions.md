---
applyTo: "*.py
---

# goal 

Use python invoke to create a tasks.py in folders  that will create collections for the context and then create individual tasks for each file 


i want to be able to run inv linux.languages.fonts to run the scripts in there


# Paths
use the root folders paths.py to create paths to directory in a single file and reference these else where


# Context.run

be sure to have `with c.cd(paths.SOME_FOLDER):` context when running commands in certain folder if necessary

# Task Organization

Tasks should be organized into individual files based on their functionality. For example, all tasks related to `go` should be in a `go.py` file. These individual task files should then be imported into a `tasks.py` file within the same directory, which will then create a collection of tasks.

## Platform Specific Tasks

There will be collections for platform-specific installs. Tools may have additional steps to install things, so it's important to create derivative functions and add them to a collection.

For example, the `go` task `install_go()` might be the same for Ubuntu 18-22, but for Ubuntu 24 there's an additional step. In this case, we would create a `install_go_ubuntu_24()` which will add the new step and reuse `install_go()` within it if applicable.

### Example

`scripts/linux/languages/go.py`:
```python
from invoke import task

@task
def install(c):
    """Installs Go."""
    # ... installation logic ...

@task
def install_ubuntu_24(c):
    """Installs Go on Ubuntu 24."""
    install(c)
    # ... additional steps for Ubuntu 24 ...
```

`scripts/linux/languages/tasks.py`:
```python
from invoke import Collection
from . import go

ns = Collection("languages")
go_collection = Collection.from_module(go)
ns.add_collection(go_collection, "go")
```

