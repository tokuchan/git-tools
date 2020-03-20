import click
import sh

from sh.contrib import git

@click.command()
@click.argument('ticket')
@click.argument('name')
def cli(ticket, name):
    '''
    USAGE
        git-feature <ticket> <name>

    DESCRIPTION
        Create a new GIT branch, tracking master, and setting upstream, named
        following the pattern 'feature/<ticket>-<name>'. Other git-tools tools
        will look for names following this pattern.
    '''
    br_name=f"feature/{ticket}-{name}"
    click.echo(f"Calling git-feature to create {br_name}")
    try:
        print(git.checkout("-t", "-b", br_name, _err_to_out=True))
    except sh.ErrorReturnCode:
        click.echo("Something went wrong!")
    return 0
