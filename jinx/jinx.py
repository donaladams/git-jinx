from collections import namedtuple
from datetime import datetime
from shlex import split as s
import subprocess


REMOTE_NAME = "origin"
REMOTE_BRANCH = "master"
REMOTE_REF = "{}/{}".format(REMOTE_NAME, REMOTE_BRANCH)
CURRENT_BRANCH = s("git rev-parse --abbrev-ref HEAD")
DIFF_INDEX = s("git diff-index {} --numstat".format(REMOTE_REF))
FETCH_REMOTE = s("git fetch {} {}".format(REMOTE_NAME, REMOTE_BRANCH))
ENCODING = "utf-8"


User = namedtuple("User", ["name", "email"])


ChangeSummary = namedtuple("ChangeSummary", ["additions", "deletions", "path"])


class ChangeReport(object):

    def __init__(self, user, local_branch, remote_branch, changes, report_time):
        self.user = user
        self.local_branch = local_branch
        self.remote_branch = remote_branch
        self.changes = changes
        self.report_time = report_time

    def __str__(self):
        return (
            "ChangeReport(" +
            "user={}".format(self.user) +
            ", local_branch={}".format(self.local_branch) +
            ", remote_branch={}".format(self.remote_branch) +
            ", changes={}".format(self.changes) +
            ", report_time={}".format(self.report_time) + ")"
        )


def get_config(path):
    output = subprocess.check_output(
        s("git config {}".format(path))
    )
    return output.strip().decode(ENCODING)


def get_git_user():
    """Get the user's local git user info."""
    name = get_config("user.name")
    if not name:
        raise ValueError("Must specify 'user.name' in .gitconfig")

    email = get_config("user.email")
    if not email:
        raise ValueError("Must specify 'user.email' in .gitconfig")

    return User(name=name, email=email)


def get_current_branch():
    """Return the name of the current branch."""
    output = subprocess.check_output(CURRENT_BRANCH)
    return output.strip().decode(ENCODING)


def get_local_changes():
    """Return a list of ChangeSummaries showing what's different
    from the local index and the remote one.
    """

    def to_summary(line):
        """Convert a line of output from the git command to
        a ChangeSummary instance.
        """
        words = line.split()
        return ChangeSummary(
            additions=int(words[0]),
            deletions=int(words[1]),
            path=words[2].decode(ENCODING)
        )

    output = subprocess.check_output(DIFF_INDEX)
    lines = output.strip().split(b"\n")
    summaries = [to_summary(line) for line in lines]
    return summaries


def check_remote_branch():
    """Check the remote branch exists and fetch it"""
    result = subprocess.run(FETCH_REMOTE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if result.returncode != 0:
        raise RuntimeError(
            "Unable to fetch remote branch {}. Are you sure this remote and branch exists?".format(
                REMOTE_BRANCH
            )
        )
    return REMOTE_BRANCH


def build_change_report():
    """Build a report of the local changes with respect to the remote branch."""
    report_time = datetime.utcnow()
    remote_branch = check_remote_branch()
    changes = get_local_changes()
    user = get_git_user()
    local_branch = get_current_branch()

    return ChangeReport(
        user=user,
        local_branch=local_branch,
        remote_branch=remote_branch,
        changes=changes,
        report_time=report_time
    )


report = build_change_report()

print(report)
