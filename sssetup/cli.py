import click

from .core import Status, Linker, FatalError


@click.group()
def cli():
    pass


@cli.command(short_help='Display status of secret storage setup.')
@click.option('--verbose', '-v', is_flag=True, default=False)
def status(verbose):
    status = Status(verbose)
    for message in status.messages():
        click.echo(message)


@cli.command(short_help='Link system packages into the current virtualenv.')
@click.option('--verbose', '-v', is_flag=True, default=False)
@click.pass_context
def link(ctx, verbose):
    try:
        linker = Linker(verbose)
        if linker.run():
            click.echo('linking successful, run the status command to verify')
        for message in linker.messages():
            click.echo(message)
    except FatalError as e:
        ctx.fail(str(e))
