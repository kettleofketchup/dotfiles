from invoke import task


@task
def build(c):
    """Builds the Go project."""
    print("Building Go project...")
    with c.cd("src"):
        c.run("go build -o ../bin/dotfiles .")
    print("Build complete!")
