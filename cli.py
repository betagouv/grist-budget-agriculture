import click
import logging

from access import update as update_fct
import check_emails


@click.group()
def cli():
    logging.basicConfig(level=logging.WARNING)


@cli.group()
def access():
    pass


@access.command()
def update():
    update_fct()


@cli.group()
def email():
    pass


@email.command()
def check():
    check_emails.for_BC()


if __name__ == "__main__":
    cli()
