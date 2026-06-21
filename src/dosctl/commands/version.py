import click

from .. import __version__


@click.command()
def version():
    """Show the version of dosctl."""
    click.echo(f"dosctl {__version__}")
