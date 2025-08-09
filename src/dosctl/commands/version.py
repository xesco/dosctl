import click
from .. import __version__

@click.command()
def version():
    """Show the version of DOSCtl."""
    click.echo(f"DOSCtl {__version__}")
