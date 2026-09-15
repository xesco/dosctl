"""Collection management commands."""

import shutil
from pathlib import Path

import click

from dosctl.collections.factory import get_available_collections
from dosctl.lib.collections_store import (
    add_collection,
    cache_dir_for,
    env_override,
    get_active_name,
    list_collections,
    remove_collection,
    set_active,
)


@click.group()
def col():
    """Manage collections, the places dosctl reads games from.

    The built-in collection 'tdc' is the Total DOS Collection on the
    Internet Archive. Add a directory of zip archives and switch to it:

      dosctl col add mine ~/dos-games

      dosctl col use mine
    """


@col.command(name="add")
@click.argument("name")
@click.argument("source")
@click.option(
    "-t", "--type", "collection_type",
    type=click.Choice(get_available_collections()),
    help="Collection type. Default: local_file for a directory, tdc_release_14 for a URL, "
         "s3 for an s3:// or s3+http(s):// bucket URI.",
)
def col_add(name, source, collection_type):
    """Add collection NAME reading from SOURCE.

    SOURCE is a directory of zip archives, an Internet Archive URL, or an
    S3 bucket URI (s3://bucket or s3+https://host/bucket).
    """
    if collection_type is None:
        if source.startswith(("http://", "https://")):
            collection_type = "tdc_release_14"
        elif source.startswith(("s3://", "s3+http://", "s3+https://")):
            collection_type = "s3"
        else:
            collection_type = "local_file"

    if collection_type == "local_file":
        directory = Path(source).expanduser()
        if not directory.is_dir():
            click.echo(f"Error: Directory '{directory}' not found.", err=True)
            return
        source = str(directory.resolve())

    try:
        add_collection(name, collection_type, source)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        return

    click.echo(f"Collection '{name}' ({collection_type}) added: {source}")
    click.echo(f"Use 'dosctl col use {name}' to switch to it.")


@col.command(name="use")
@click.argument("name")
def col_use(name):
    """Make NAME the collection every command reads."""
    try:
        set_active(name)
    except KeyError:
        click.echo(f"Error: No collection '{name}' found.", err=True)
        return
    click.echo(f"Now using collection '{name}'.")


@col.command(name="list")
def col_list():
    """List the collections; * marks the one in use."""
    active = get_active_name()
    collections = list_collections()
    width = max(len(name) for name in collections)
    click.echo("Collections:")
    for name, entry in collections.items():
        marker = "*" if name == active else " "
        click.echo(f"{marker} {name.ljust(width)}  {entry['type'].ljust(14)}  {entry['source']}")

    override = env_override()
    if override:
        click.echo(
            f"DOSCTL_COLLECTION overrides this: {override['type']} {override['source']}"
        )


@col.command(name="remove")
@click.argument("name")
def col_remove(name):
    """Remove collection NAME. Installed games stay."""
    try:
        was_active = remove_collection(name)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        return
    except KeyError:
        click.echo(f"Error: No collection '{name}' found.", err=True)
        return

    shutil.rmtree(cache_dir_for(name), ignore_errors=True)
    click.echo(f"Collection '{name}' removed.")
    if was_active:
        click.echo("Now using collection 'tdc'.")
