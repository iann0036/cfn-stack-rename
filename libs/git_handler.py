#
##
########################################################################################
#                                                                                      # 
#       git_handler                                                                    #
#                                                                                      #
#       (c) Vamegh Hedayati                                                            #
#                                                                                      #
#       Please see https://github.com/vamegh/pylibs                                    #
#                  https://github.com/vamegh/git_python/blob/master/git/git_handler.py #
#                    for License Information                                           #
#                             GNU/LGPL                                                 #
########################################################################################
##
#
#  git_handler - This handles basic git operations

import os
import sh
import shutil
import logging


class Git_Process(object):
    def __init__(self, clone_path='', remote_repo=''):
        self.path = clone_path
        self.repo = remote_repo
        self.git = sh.git.bake(_cwd=self.path)

    def git_add(self, add_path=None):
        try:
            output = self.git.add(add_path, _cwd=self.path)
            return output
        except (sh.ErrorReturnCode_128, sh.ErrorReturnCode_1) as err:
            logging.info(f"nothing to add here ... :: Skipping :: {add_path}")
            return "fail"

    def git_rm(self, del_path=None):
        try:
            output = self.git.rm(del_path, _cwd=self.path)
            return output
        except (sh.ErrorReturnCode_128, sh.ErrorReturnCode_1) as err:
            logging.info(f"nothing to delete here ... :: Error :: {err}")
            return "fail"

    def git_commit(self, message=None):
        try:
            output = self.git.commit('-m', message)
            return output
        except (sh.ErrorReturnCode_128, sh.ErrorReturnCode_1) as err:
            logging.info("nothing to commit here ... :: Skipping Git Steps :: ")
            return "fail"

    def git_clone(self):
        if os.path.isdir(self.path):
            logging.info(f"Repo: {self.repo} at path: {self.path} already exists, "
                         f"pulling latest updates only")
            return None
        else:
            try:
                output = sh.git.clone(self.repo, self.path)
                return output
            except (sh.ErrorReturnCode_128, sh.ErrorReturnCode_1) as err:
                logging.error(f"Cannot Clone, on macosx make sure to add passphrases "
                              f"before hand running ssh-add ~/.ssh/<rest_of_path_to_ssh_key>")
                exit(1)
            return "done"

    def git_checkout(self, branch=None):
        if branch:
            try:
                output = self.git.checkout(branch)
                return output
            except (sh.ErrorReturnCode_128, sh.ErrorReturnCode_1) as err:
                logging.info(f"Cannot checkout branch, Skipping Git Checkout Step")
                raise ValueError(f"Error Message: {err}")

    def git_branch_on_commit(self, branch=None):
        if branch:
            try:
                output = self.git.checkout("-b", branch, branch)
                return output
            except (sh.ErrorReturnCode_128, sh.ErrorReturnCode_1) as err:
                logging.warning(f"Cannot checkout branch, Skipping Git Branch Step :: Error: {err}")
                raise ValueError(f"Error Message: {err}")

    def git_branch(self, branch=None):
        if branch:
            try:
                output = self.git.checkout("-b", branch)
                return output
            except (sh.ErrorReturnCode_128, sh.ErrorReturnCode_1) as err:
                logging.warning(f"Cannot checkout branch, Skipping Git Branch Step :: Error: {err}")
                raise ValueError(f"Error Message: {err}")

    def git_branch_delete(self, branch=None):
        if branch:
            try:
                output = self.git.branch("-d", branch)
                return output
            except (sh.ErrorReturnCode_128, sh.ErrorReturnCode_1) as err:
                logging.warning(f"Cannot delete branch, Skipping Git Delete Branch Step :: Error: {err}")
                raise ValueError(f"Error Message: {err}")

    def git_show_branch(self):
        try:
            output = self.git.branch("--show-current")
            return output
        except (sh.ErrorReturnCode_128, sh.ErrorReturnCode_1) as err:
            logging.warning(f"Cannot show current branch, Skipping")
            return None

    def git_show_branch_alt(self):
        try:
            output = self.git("rev-parse", "--abbrev-ref", "HEAD")
            return output
        except (sh.ErrorReturnCode_128, sh.ErrorReturnCode_1) as err:
            logging.warning(f"Cannot show current branch, Skipping")
            return None

    def git_branch_track(self, branch=None):
        if branch:
            try:
                output = self.git.branch("-u", "origin/" + branch, branch)
                return output
            except (sh.ErrorReturnCode_128, sh.ErrorReturnCode_1) as err:
                logging.info("Cannot track remote branch, Skipping Git Branch Track Step")
                raise ValueError(f"Error:: {err}")

    def git_push(self, branch=None):
        try:
            output = self.git.push('origin', f'HEAD:refs/heads/{branch}')
            return output
        except (sh.ErrorReturnCode_128, sh.ErrorReturnCode_1) as err:
            logging.info(f"Cannot push to remote branch, Skipping Git Push Step")
            return "fail"

    def git_push_tags(self):
        try:
            output = self.git.push("origin", "--tags")
            return output
        except (sh.ErrorReturnCode_128, sh.ErrorReturnCode_1) as err:
            logging.info(f"Cannot push tags to remote branch, Skipping Git Push Tags Step")
            raise ValueError(f'"Error:: Cannot push tags to remote branch, Skipping')

    def git_pull(self):
        try:
            output = self.git.pull('--rebase')
            return output
        except (sh.ErrorReturnCode_128, sh.ErrorReturnCode_1) as err:
            logging.info(f"Cannot pull remote branch may not exist or changes may need to be committed, "
                         f"Skipping Git Pull Step")
            raise ValueError(f"Error Message: {err}")

    def git_pull_prune(self):
        try:
            output = self.git.pull('--prune')
            return output
        except (sh.ErrorReturnCode_128, sh.ErrorReturnCode_1) as err:
            logging.info(f"Cannot pull remote branch may not exist or changes may need to be committed, "
                         f" Skipping Git Pull Step")
            raise ValueError(f"Error Message: {err}")

    def git_status(self):
        try:
            output = self.git.status
            return output
        except (sh.ErrorReturnCode_128, sh.ErrorReturnCode_1) as err:
            logging.warning(f"Cant get status, Error Message :: {err}")
            return "fail"

    def git_show(self):
        try:
            output = self.git.show
            return output
        except (sh.ErrorReturnCode_128, sh.ErrorReturnCode_1) as err:
            logging.warning(f"Cant show, Error Message :: {err}")
            return "fail"

    def git_tag(self, version=None, message=None):
        try:
            output = self.git.tag("-a", version, "-m", version)
            return output
        except (sh.ErrorReturnCode_128, sh.ErrorReturnCode_1) as err:
            raise ValueError(f'Cannot create tag {version}, Skipping')

    def git_log(self, commits='2'):
        try:
            output = self.git.log("--decorate=short", "--sparse", "-n", commits)
            return output
        except (sh.ErrorReturnCode_128, sh.ErrorReturnCode_1) as err:
            logging.warning(f"Cant show logs, Error Message :: {err}")
            return "fail"

    def __del__(self):
        if os.path.isdir(self.path):
            logging.info(f"Cleaning up repo: {self.repo} in Path: {self.path}")
            # shutil.rmtree(self.path)
