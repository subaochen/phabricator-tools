"""Process the arguments for a single repository and execute."""
# =============================================================================
# CONTENTS
# -----------------------------------------------------------------------------
# abdi_processrepoargs
#
# Public Functions:
#   do
#   fetch_if_needed
#
# -----------------------------------------------------------------------------
# (this contents block is generated, edits will be lost)
# =============================================================================

from __future__ import absolute_import

import phlsys_conduit

import abdmail_mailer
import abdt_classicnaming
import abdt_compositenaming
import abdt_conduit
import abdt_errident
import abdt_git
import abdt_rbranchnaming
import abdt_tryloop

import abdi_processrepo
import abdi_repoargs


def do(repo, unused_repo_name, args, conduits, url_watcher, mail_sender):
    _do(repo, args, conduits, url_watcher, mail_sender)


def _flatten_list(hierarchy):
    for x in hierarchy:
        # recurse into hierarchy if it's a list
        if hasattr(x, '__iter__') and not isinstance(x, str):
            for y in _flatten_list(x):
                yield y
        else:
            yield x


def _do(repo, args, conduits, url_watcher, mail_sender):

    fetch_if_needed(
        url_watcher,
        abdi_repoargs.get_repo_snoop_url(args),
        repo,
        args.repo_desc)

    arcyd_conduit = _connect(conduits, args)

    admin_emails = set(_flatten_list(args.admin_emails))

    # TODO: this should be a URI for users not conduit
    mailer = abdmail_mailer.Mailer(
        mail_sender,
        admin_emails,
        args.repo_desc,
        args.instance_uri)

    branch_url_callable = None
    if args.branch_url_format:
        def make_branch_url(branch_name):
            return args.branch_url_format.format(
                branch=branch_name,
                repo_url=args.repo_url)
        branch_url_callable = make_branch_url

    branch_naming = abdt_compositenaming.Naming(
        abdt_classicnaming.Naming(),
        abdt_rbranchnaming.Naming())

    branches = abdt_git.get_managed_branches(
        repo,
        args.repo_desc,
        branch_naming,
        branch_url_callable)

    abdi_processrepo.process_branches(branches, arcyd_conduit, mailer)


def fetch_if_needed(url_watcher, snoop_url, repo, repo_desc):

    did_fetch = False

    # fetch only if we need to
    if not snoop_url or url_watcher.peek_has_url_recently_changed(snoop_url):
            abdt_tryloop.tryloop(
                repo.checkout_master_fetch_prune,
                abdt_errident.FETCH_PRUNE,
                repo_desc)
            did_fetch = True

    if did_fetch and snoop_url:
        # consume the 'newness' of this repo, since fetching succeeded
        url_watcher.has_url_recently_changed(snoop_url)

    return did_fetch


def _connect(conduits, args):

    key = (
        args.instance_uri, args.arcyd_user, args.arcyd_cert, args.https_proxy)
    if key not in conduits:
        # create an array so that the 'connect' closure binds to the 'conduit'
        # variable as we'd expect, otherwise it'll just modify a local variable
        # and this 'conduit' will remain 'None'
        # XXX: we can do better in python 3.x (nonlocal?)
        conduit = [None]

        def connect():
            # nonlocal conduit # XXX: we'll rebind in python 3.x, instead
            conduit[0] = phlsys_conduit.Conduit(
                args.instance_uri,
                args.arcyd_user,
                args.arcyd_cert,
                https_proxy=args.https_proxy)

        abdt_tryloop.tryloop(
            connect, abdt_errident.CONDUIT_CONNECT, args.instance_uri)

        conduit = conduit[0]
        arcyd_conduit = abdt_conduit.Conduit(conduit)
        conduits[key] = arcyd_conduit
    else:
        arcyd_conduit = conduits[key]

    return arcyd_conduit


# -----------------------------------------------------------------------------
# Copyright (C) 2013-2014 Bloomberg Finance L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ------------------------------ END-OF-FILE ----------------------------------
