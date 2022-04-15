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
Module containing routines to access the APS scheduling system.

You must create in your home directory a 
`scheduling.ini <https://github.com/decarlof/data-management/blob/master/config/scheduling.ini>`__ 
configuration file

"""

import os
import pytz 
import datetime as dt

from os.path import expanduser
from dm import BssApsDbApi

from slackgup import log


__author__ = "Francesco De Carlo"
__copyright__ = "Copyright (c) 2021, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['get_current_users',
           'get_current_emails',
           'get_current_pi',
           'get_current_proposal_id',
           ]

dm_api = BssApsDbApi()

def get_current_pi(args):
    """
    Get information about the PI for the current experiment.
    
    Returns
    ------------
    dictionary-like object containing information for PI
    """
    users = get_current_users(args)
    if not users:
        return None
    for u in users:
        if 'piFlag' in u.keys():
            if u['piFlag'] == 'Y':
                return u
    #If we are here, nothing was listed as PI.  Use first user
    return users[0]

def get_current_emails(args, exclude_pi=True):
    """
    Find user's emails currently running at beamline
     
    Parameters
    ----------
    users : dictionary-like object containing user information
    
    
    Returns
    -------
    List of user emails (default: all but PI)       
    """
    emails = []
    
    users = get_current_users(args)
    if not users:
        log.warning("No current valid users")
        return None

    for u in users:
        if exclude_pi and 'piFlag' in u.keys() and u['piFlag'] == 'Y':
            continue
        if 'email' in u.keys() and u['email'] != None:
            emails.append(str(u['email']).lower())
            log.info('Added {0:s} to the e-mail list.'.format(emails[-1]))
        else:            
            log.info("    Missing e-mail for badge {0:6d}, {1:s} {2:s}, institution {3:s}"
                    .format(u['badge'], u['firstName'], u['lastName'], u['institution']))
    log.info("Found valid emails")
    return emails

def get_current_users(args):
    """
    Get users running at beamline currently
    
    Returns
    -------
    users : dictionary-like object containing user information      
    """
    proposal = get_current_proposal(args)
    if not proposal:
        log.warning("No current valid proposal")
        return None
    log.info("Found valid experimenters")
    return proposal['experimenters']


def get_proposal_starting_date(args):
    """
    Get the proposal starting date for the current proposal.

    Returns
    ---------
    proposal starting date as a string
    """
    proposal = get_current_proposal(args)
    if not proposal:
        log.error("No current valid proposal")
        return None
    log.info("Found valid proposal start time")
    return str(dt.datetime.fromisoformat((proposal['startTime'])).strftime("%Y_%m_%d"))

def get_current_proposal_id(args):
    """
    Get the proposal id for the current proposal.

    Returns
    ---------
    proposal ID as an int
    """
    proposal = get_current_proposal(args)
    if not proposal:
        log.error("No current valid proposal")
        return None
    log.info("Found valid proposal id")
    return str(get_current_proposal(args)['id'])

def get_current_proposal(args):
    """
    Get a dictionary-like object with current proposal information.
    If no proposal is active, return None
    
    Returns
    -------------
    dict-like object with information for current proposal
    """
    proposals = dm_api.listProposals()

    time_now = dt.datetime.now(pytz.utc) + dt.timedelta(args.set)

    if (args.set == 0):
        log.info('%s' % time_now)
    else:
        log.warning('Selected date is %s. This is %f days from now. Use --set 0 for  current proposal' % (time_now, args.set))
    for prop in proposals:
        for i in range(len(prop['activities'])):
            prop_start = dt.datetime.fromisoformat(prop['activities'][i]['startTime'])
            prop_end = dt.datetime.fromisoformat(prop['activities'][i]['endTime'])
            if prop_start <= time_now and prop_end >= time_now:
                return prop
    return None

