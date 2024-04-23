#!/usr/bin/env python
# -*- coding: utf-8 -*-

# #########################################################################
# Copyright (c) 2021, UChicago Argonne, LLC. All rights reserved.         #
#                                                                         #
# Copyright 2021. UChicago Argonne, LLC. This software was produced       #
# under U.S. Government contract DE-AC02-06CH11357 for Argonne National   #
# Laboratory (ANL), which is operated by UChicago Argonne, LLC for the    #
# U.S. Department of Energy. The U.S. Government has rights to use,       #
# reproduce, and distribute this software.  NEITHER THE GOVERNMENT NOR    #
# UChicago Argonne, LLC MAKES ANY WARRANTY, EXPRESS OR IMPLIED, OR        #
# ASSUMES ANY LIABILITY FOR THE USE OF THIS SOFTWARE.  If software is     #
# modified to produce derivative works, such modified software should     #
# be clearly marked, so as not to confuse it with the version available   #
# from ANL.                                                               #
#                                                                         #
# Additionally, redistribution and use in source and binary forms, with   #
# or without modification, are permitted provided that the following      #
# conditions are met:                                                     #
#                                                                         #
#     * Redistributions of source code must retain the above copyright    #
#       notice, this list of conditions and the following disclaimer.     #
#                                                                         #
#     * Redistributions in binary form must reproduce the above copyright #
#       notice, this list of conditions and the following disclaimer in   #
#       the documentation and/or other materials provided with the        #
#       distribution.                                                     #
#                                                                         #
#     * Neither the name of UChicago Argonne, LLC, Argonne National       #
#       Laboratory, ANL, the U.S. Government, nor the names of its        #
#       contributors may be used to endorse or promote products derived   #
#       from this software without specific prior written permission.     #
#                                                                         #
# THIS SOFTWARE IS PROVIDED BY UChicago Argonne, LLC AND CONTRIBUTORS     #
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT       #
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS       #f
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL UChicago     #
# Argonne, LLC OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,        #
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,    #
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;        #
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER        #
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT      #
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN       #
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE         #
# POSSIBILITY OF SUCH DAMAGE.                                             #
# #########################################################################
"""
Module to create a slack channel named GUP-# retrieving the information from the scheduling system
"""
import os
import sys
import datetime
import argparse
import pathlib
import datetime as dt

# install dmagic from https://github.com/xray-imaging/DMagic
from dmagic import authorize
from dmagic import scheduling

from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from slackgup import log
from slackgup import config

def init(args):
    if not os.path.exists(str(args.config)):
        config.write(str(args.config))
    else:
        raise RuntimeError("{0} already exists".format(args.config))

def status(args):
    config.show_config(args)

def create_channel_name(args):

    channel_name = None
    proposal_user_emails = []

    now = datetime.datetime.today() + dt.timedelta(args.set)
    log.info("Today's date: %s" % now)

    auth      = authorize.basic()
    run       = scheduling.current_run(auth, args)
    proposals = scheduling.beamtime_requests(run, auth, args)
    
    if not proposals:
        log.error('No valid current experiment')
        return None
    try:
        log.error(proposals['message'])
        return None
    except:
        pass

    proposal = scheduling.get_current_proposal(proposals, args)
    if proposal != None:
        proposal_pi          = scheduling.get_current_pi(proposal)
        pi_last_name         = proposal_pi['lastName']   
        proposal_id          = scheduling.get_current_proposal_id(proposal)
        proposal_user_emails = scheduling.get_current_emails(proposal, False)
        proposal_start_date  = scheduling.get_proposal_starting_date(proposal)

        log.info('GUP proposal_id: %s' % proposal_id)
        log.info('Proposal starting date: %s' % proposal_start_date)
        log.info('Proposal PI: %s' % pi_last_name)
        if args.primary_beamline_contact_email != "Empty":
            proposal_user_emails.append(args.primary_beamline_contact_email)
        if args.secondary_beamline_contact_email != "Empty":
            proposal_user_emails.append(args.secondary_beamline_contact_email)
        if (args.beamline == 'None'):
            channel_name = proposal_start_date + '_' + pi_last_name + '_gup_' + proposal_id
        else: 
            channel_name = args.beamline.replace('-', '_').replace(',', '_') + '_' + proposal_start_date + '_' + pi_last_name + '_gup_' + str(proposal_id)
            log.info('Slack channel name: %s' % channel_name)

    else:
        log.error("There is not a valid proposal on the selected date")

    return channel_name, proposal_user_emails

def slack_gup(args):

    channel_name, proposal_user_emails = create_channel_name(args)

    # Set bot tokens as environment values
    env_path = os.path.join(str(pathlib.Path.home()), '.slackenv')
    load_dotenv(dotenv_path=env_path)
    bot_token = os.environ.get("BOT_TOKEN")
    client = WebClient(token=bot_token)
    try:
        # Call the conversations.create method using the WebClient
        # conversations_create requires the channels:manage bot scope
        result = client.conversations_create(
            # The name of the conversation
            name=channel_name
        )
        log.warning('Created slack channel: %s' % result['channel']['name'])
        log.warning("Please invite to the slack channel %s these users [%s]" % (channel_name, ', '.join(map(str, proposal_user_emails)).strip("'")))

    except SlackApiError as e:
        log.error("Error creating conversation: {}".format(e))
        log.error('Channel [%s] already exists' % channel_name)
        log.warning("If you have not already done so, please invite to the slack channel %s these users [%s]" % (channel_name, ', '.join(map(str, proposal_user_emails)).strip("'")))

    
    # WARNING: options below are only for Business+ and above. 

    # Slack provides a couple of different ways to programmatically invite and provision users to a workspace, 
    # however these options are not available on all plans.

    # - The admin.users.invite method you mentioned and Admin API requires an Enterprise Grid plan 
    # (https://api.slack.com/enterprise/managing), which is why you are running into the error message you captured 
    # in your screenshot.

    # - The SCIM API (https://api.slack.com/scim) can be used by workspaces on our Business+ plan and above to 
    # help provision/de-provision, manage user accounts and groups. The /Users endpoint accepts a POST request to 
    # create a new user on a Workspace - https://api.slack.com/scim#post-users.

    # - Aside from this, there isn't another API or programmatic way to invite users to a Slack Workspace on 
    # our Free or Pro plans, so I'm afraid we do not have an API for your specific use case. Apologies for this, 
    # Francesco. You can confirm which plan you're currently on by looking for the Current subscription 
    # label here: https://my.slack.com/plans

    # client = WebClient(token=bot_token)
    # try:
    #     # Call the conversations.create method using the WebClient
    #     # conversations_create requires the channels:manage bot scope
    #     result = client.conversations_setPurpose(
    #         channel='C02KJHD84CR', 
    #         purpose='purpose'
    #     )
    #     # Log the result which includes information like the ID of the conversation
    #     log.info('Set purpose %s' % result)
    # except SlackApiError as e:
    #     log.error("Error setting purpose: {}".format(e))


    # try:
    #     # Call admin_users_invite method
    #     # admin_users_invite requires the admin.invites:write scope added under
    #     # the User Token Scopes
    #     result = client.admin_users_invite(
    #         token=bot_token, 
    #         channel_ids=channel_name, 
    #         email='decarlof@gmail.com', 
    #         team_id=''
    #     )
    #     # Log the result which includes information like the ID of the conversation
    #     log.info('Slack result %s' % result)
    # except SlackApiError as e:
    #     log.error("Error inviting users to the channel: {}".format(e))

    # try:
    #     # Call conversations_invite
    #     # admin_users_invite requires the admin.invites:write scope added under
    #     # the User Token Scopes
    #     result = client.conversations_invite(
    #         token=bot_token, 
    #         channel='C02H3BP1LRG',
    #         users='U024RA4D0UB' 
    #     )
    #     # Log the result which includes information like the ID of the conversation
    #     log.info('Slack result %s' % result)
    # except SlackApiError as e:
    #     log.error("Error inviting users to a conversation: {}".format(e))

    # try:
    #     # Call users_lookupByEmail
    #     # admin_users_invite requires the users:read.eamil scope added under
    #     # the Bot Token Scopes
    #     result = client.users_lookupByEmail(
    #         token=bot_token, 
    #         email='decarlof@gmail.com',
    #     )
    #     # Log the result which includes information like the ID of the conversation
    #     log.info('Slack result %s' % result)
    # except SlackApiError as e:
    #     log.error("Error users_lookupByEmail: {}".format(e))

def show(args):
    channel_name, proposal_user_emails = create_channel_name(args)
    log.warning('Run ** slack gup ** to create %s.' % channel_name)

def main():
    home = os.path.expanduser("~")
    logs_home = home + '/logs/'

    # make sure logs directory exists
    if not os.path.exists(logs_home):
        os.makedirs(logs_home)

    lfname = logs_home + 'dmagic_' + datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d_%H:%M:%S") + '.log'
    log.setup_custom_logger(lfname)

    parser = argparse.ArgumentParser()
    parser.add_argument('--config', **config.SECTIONS['general']['config'])
    show_params = config.SLACKGUP_PARAMS
    tag_params = config.SLACKGUP_PARAMS
    slack_params = config.SLACKGUP_PARAMS

    cmd_parsers = [
        ('init',        init,           (),                "Create configuration file"),
        ('status',      status,         show_params,       "Show slack status"),
        ('show',        show,           show_params,       "Show user and experiment info from the APS schedule"),
        ('gup',         slack_gup,      slack_params,      "Create a slack channel using called YYYY_MM_DD_PI-last-name_gup_##### and share it with all users listed in the proposal"),
    ]

    subparsers = parser.add_subparsers(title="Commands", metavar='')

    for cmd, func, sections, text in cmd_parsers:
        cmd_params = config.Params(sections=sections)
        cmd_parser = subparsers.add_parser(cmd, help=text, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        cmd_parser = cmd_params.add_arguments(cmd_parser)
        cmd_parser.set_defaults(_func=func)

    args = config.parse_known_args(parser, subparser=True)

    try:
        # load args from default (config.py) if not changed
        args._func(args)
        # config.show_config(args)
        # undate globus.config file
        sections = config.SLACKGUP_PARAMS
        config.write(args.config, args=args, sections=sections)
    except RuntimeError as e:
        log.error(str(e))
        sys.exit(1)

if __name__ == '__main__':
    main()
