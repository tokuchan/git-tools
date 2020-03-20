import click
import sh
import re
from io import StringIO

from sh.contrib import git

@click.command()
@click.argument('ticket')
@click.argument('name')
def feature(ticket, name):
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
        return 1
    return 0

@click.command()
@click.option('--name','-n', help='The name of the branch to finish. Must start with "feature/".')
def finish(name):
    '''
    USAGE
        git-finish [-n/--name= <name>]

    DESCRIPTION
        Set the current branch's upstream to point to old, then rename it,
        substituting the "feature" prefix for "old", so it no longer appears in
        "git features".
    '''
    buf = StringIO()
    if not name:
        name = str(git.branch("--show-current")).strip()

    if re.match('^feature/', name):
        new_name=re.sub('^feature', 'finished', name)
        click.echo(f"Finishing {name} by renaming it to {new_name}")
        try:
            git.branch(u="old", _err_to_out=True, _out=buf)
            git.branch("-m", name, new_name, _err_to_out=True, _out=buf)
            git.checkout("master")
        except sh.ErrorReturnCode:
            click.echo("Something went wrong!")
            click.echo(buf.getvalue())
            return 1
    else:
        click.echo('Branch name does not start with "feature/"')
        return 1
    return 0
