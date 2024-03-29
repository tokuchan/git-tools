import functools as fts
import itertools as its
import os
import re
from io import StringIO
from pathlib import Path

import click
import sh
import toolz.functoolz as ftz
import toolz.itertoolz as itz
from sh.contrib import git
from toolz.curried import filter, map


@click.command()
@click.option(
    "--branch", "-b", help="Default = HEAD. Specify a branch to get children for."
)
@click.option(
    "--recursive/--no-recursive",
    "-r/-R",
    help="Recursively include children of children.",
)
@click.option(
    "--show-upstream/--no-show-upstream",
    "-u/-U",
    help="Show the upstream for each branch, a space, then the branch itself.",
)
def descendants(branch, recursive, show_upstream):
    """
    USAGE
        git-children [--[no]-show-upstream] [--[no]-recursive] [--branch=<branch>]

    DESCRIPTION
	Show the children of this branch. Can recursively show descendents as
        well. Can also show "upstream branch" format, suitable for piping to ``tsort``.
    """
    git_rev_parse = sh.Command("git-rev-parse")
    git_children = git_rev_parse.bake("--abbrev-ref", "HEAD")
    strip_upstreams = map(lambda x: x[1])
    if not branch:
        branch = str(git_children()).strip()

    def get_children(branch):
        git_upstreams = git.branch.bake("--format=%(upstream) %(refname)", "--list")
        strip_strs = map(lambda x: x.strip())
        make_pairs = map(lambda x: tuple(x.split(" ")))
        keep_heads = filter(lambda x: re.match("refs/heads", x[1]))
        strip_branch_refs = map(lambda x: tuple([x[0], re.sub("refs/.*?/", "", x[1])]))
        strip_upstream_refs = map(
            lambda x: tuple([re.sub("refs/.*?/", "", x[0]), x[1]])
        )
        keep_referrents = filter(lambda x: str(branch) == x[0])
        compute_branches = ftz.compose(
            keep_referrents,
            strip_upstream_refs,
            strip_branch_refs,
            keep_heads,
            make_pairs,
            strip_strs,
        )
        return [x for x in compute_branches(git_upstreams())]

    def get_all_children(branch):
        children = get_children(branch)
        return list(itz.mapcat(get_all_children, strip_upstreams(children))) + children

    branches = get_all_children(branch) if recursive else get_children(branch)
    for (upstream, ref) in branches:
        if show_upstream:
            print(f"{upstream} {ref}")
        else:
            print(ref)
    return 0


@click.command()
@click.option(
    "-t",
    "--ticket",
    help="Specify the JIRA ticket to use.",
    default=lambda: os.environ.get("CURRENT_JIRA_TASK", ""),
    prompt=True,
    show_default="CURRENT_JIRA_TASK",
)
@click.option(
    "-p",
    "--project-directory",
    help='Specify the directory "tag" in which "git into" will look.',
    default=lambda: Path.cwd().name,
    prompt=True,
    show_default="current directory",
)
@click.option(
    "-n",
    "--name",
    help="Specify the phrase that describes this feature's reason to exist.",
    default=lambda: os.environ.get("CURRENT_JIRA_DESC", "Senseless change for no good reason."),
    prompt=True,
    show_default="CURRENT_JIRA_DESC",
)
def feature(ticket, project_directory, name):
    """
    USAGE
        git-feature <ticket> <project folder> <name>

    DESCRIPTION
        Create a new GIT branch, tracking master, and setting upstream, named
        following the pattern 'feature/<ticket>__<project folder>__<name>'. Other git-tools tools
        will look for names following this pattern. Spaces in <name> will be replaced with dashes.
    """
    name__interspersed_dashes = "-".join(re.split(r"\s+", name))
    br_name = f"feature/{ticket}__{project_directory}__{name__interspersed_dashes}"
    click.echo(f"Calling git-feature to create {br_name}")
    try:
        print(git.checkout("master", _err_to_out=True))
        print(sh.jira.view(ticket))
        print(git.checkout("-t", "-b", br_name, _err_to_out=True))
        print(git.branch("--set-upstream-to=master", _err_to_out=True))
    except sh.ErrorReturnCode as e:
        click.echo(f"Something went wrong!\n\nException: {e}")
        return 1
    return 0


@click.command()
@click.option(
    "--name", "-n", help='The name of the branch to finish. Must start with "feature/".'
)
def finish(name):
    """
    USAGE
        git-finish [-n/--name= <name>]

    DESCRIPTION
        Set the current branch's upstream to point to old, then rename it,
        substituting the "feature" prefix for "old", so it no longer appears in
        "git features".
    """
    buf = StringIO()
    if not name:
        name = str(git.branch("--show-current")).strip()

    if re.match("^feature/", name):
        new_name = re.sub("^feature", "finished", name)
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
