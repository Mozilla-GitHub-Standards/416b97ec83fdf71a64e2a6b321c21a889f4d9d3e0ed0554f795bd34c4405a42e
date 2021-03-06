import os
import shutil
from git import Repo

import log

logger = log.get_logger(__name__)


class GitSettings(object):
    name = None
    bare = True
    cinnabar = False

    def __init__(self, config):
        self.config = config

    @property
    def root(self):
        return os.path.join(self.config["repo_root"], self.config["paths"]["repos"], self.name)

    @property
    def remotes(self):
        return self.config[self.name]["repo"]["remote"].iteritems()

    def repo(self):
        if not os.path.exists(self.root):
            os.makedirs(self.root)
            repo = Repo.init(self.root, bare=True)
        else:
            repo = Repo(self.root)
            logger.debug("Existing repo found at " + self.root)

        if self.cinnabar:
            repo.cinnabar = Cinnabar(repo)

        return repo

    def configure(self, file):
        r = self.repo()
        shutil.copyfile(file, os.path.normpath(os.path.join(r.git_dir, "config")))
        logger.debug("Config from {} copied to {}".format(file, os.path.join(r.git_dir, "config")))


class Gecko(GitSettings):
    name = "gecko"
    cinnabar = True
    fetch_args = ["mozilla"]


class WebPlatformTests(GitSettings):
    name = "web-platform-tests"
    fetch_args = ["origin", "master", "--no-tags"]


class Cinnabar(object):
    hg2git_cache = {}
    git2hg_cache = {}

    def __init__(self, repo):
        self.git = repo.git

    def hg2git(self, rev):
        if rev not in self.hg2git_cache:
            value = self.git.cinnabar("hg2git", rev)
            if all(c == "0" for c in value):
                raise ValueError("No git rev corresponding to hg rev %s" % rev)
            self.hg2git_cache[rev] = value
        return self.hg2git_cache[rev]

    def git2hg(self, rev):
        if rev not in self.git2hg_cache:
            value = self.git.cinnabar("git2hg", rev)
            if all(c == "0" for c in value):
                raise ValueError("No hg rev corresponding to git rev %s" % rev)
            self.git2hg_cache[rev] = value
        return self.git2hg_cache[rev]

    def fsck(self):
        self.git.cinnabar("fsck")


wrappers = {
    "gecko": Gecko,
    "web-platform-tests": WebPlatformTests,
}
