from rich.console import Console

console = Console()
print = console.print

def print_success(message: str):
    console.print(f"[bold green]✔ {message}[/bold green]")

def print_error(message: str):
    console.print(f"[bold red]✖ {message}[/bold red]")