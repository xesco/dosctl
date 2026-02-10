import click
from .commands.list import list_games
from .commands.search import search
from .commands.play import play
from .commands.inspect import inspect
from .commands.delete import delete
from .commands.refresh import refresh
from . import __version__

@click.group(invoke_without_command=True)
@click.option('-v', '--version', is_flag=True, help='Show the version and exit.')
@click.pass_context
def cli(ctx, version):
    """A command-line tool to manage and play DOS games."""
    if version:
        click.echo(f"DOSCtl {__version__}")
        return
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())

cli.add_command(list_games)
cli.add_command(search)
cli.add_command(play)
cli.add_command(inspect)
cli.add_command(delete)
cli.add_command(refresh)

if __name__ == "__main__":
    cli()
