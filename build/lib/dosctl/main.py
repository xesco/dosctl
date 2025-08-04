import click
from .commands.refresh import refresh
from .commands.list import list_games

@click.group()
def cli():
    """A command-line tool to manage and play DOS games."""
    pass

cli.add_command(refresh)
cli.add_command(list_games)

if __name__ == "__main__":
    cli()
