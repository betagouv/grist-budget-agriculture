from access import update as update_fct
import click


@click.group()
def cli():
    pass


@cli.group()
def access():
    pass


@access.command()
def update():
    update_fct()


if __name__ == "__main__":
    cli()
