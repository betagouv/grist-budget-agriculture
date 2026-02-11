import click
import logging

from grist_budget_agriculture.access import update as update_fct
import grist_budget_agriculture.check_emails_for_bc as check_emails_for_bc
import grist_budget_agriculture.check_emails_for_infbud as check_emails_for_infbud


@click.group()
def cli():
    logging.basicConfig(level=logging.INFO)


@cli.group()
def access():
    pass


@access.command()
def update():
    update_fct()


@cli.group()
def email():
    pass


@email.group()
def check():
    pass


@check.command()
def bc():
    check_emails_for_bc.main()


@check.command()
def infbud():
    check_emails_for_infbud.main()


@check.command()
def all():
    check_emails_for_bc.main()
    check_emails_for_infbud.main()


if __name__ == "__main__":
    cli()
