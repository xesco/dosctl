import click
from .commands.list import list_games
from .commands.search import search
from .commands.run import run
from .commands.inspect import inspect
from .commands.delete import delete
from .commands.refresh import refresh

@click.group()
def cli():
    """A command-line tool to manage and play DOS games."""
    pass

cli.add_command(list_games)
cli.add_command(search)
cli.add_command(run)
cli.add_command(inspect)
cli.add_command(delete)
cli.add_command(refresh)

if __name__ == "__main__":
    cli()
