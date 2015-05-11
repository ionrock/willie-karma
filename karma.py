#!/usr/bin/env python
# encoding: utf-8

"""
karma.py - A karma module for willie.
Copyright 2013, Timothy Lee <marlboromoo@gmail.com>
Licensed under the MIT License.
"""

import string
import willie

###############################################################################
# Setup the module
###############################################################################

MODULE = 'karma'
WHO = 'who'
KARMA = 'karma'
KARMA_KEY = 'karma'
REASON = 'reason'
DEBUG_LEVEL = 'verbose'

feedback = None
byself = None

DB = None

def debug_(tag, text, level):
    """Mimic willie.debug function for pytest to use.
    """
    print "[%s] %s" % (tag, text)

debug = debug_

def configure(config):
    """
    +----------+---------+-------------------+
    | [karma]  | example | purpose           |
    +----------+---------+-------------------+
    | feedback | True    | Notify by bot     |
    | byself   | False   | Self (pro|de)mote |
    +----------+---------+-------------------+
    """
    if config.option('Configure karma', False):
        config.interactive_add('karma', 'feedback', 'Notify by bot', 'True')
        config.interactive_add('karma', 'byself', 'Self (pro|de)mote', 'False')

def setup(bot):
    """Setup the database, get the settings.

    :bot: willie.bot.Willie

    """
    #. get debug function
    global debug
    debug = bot.debug if bot.debug else debug

    #. get settings
    feedback_, byself_, debug_ = True, False, False

    try:
        config = getattr(bot.config, MODULE)
        feedback_ = is_true(config.feedback)
        byself_ = is_true(config.byself)
    except Exception, e:
        pass
    global feedback, byself
    feedback = feedback_
    byself = byself_

    #. check database
    if bot.db:
        DB = bot.db
    #     key, name = WHO, KARMA
    #     columns = [key, KARMA, REASON]
    #     if not getattr(bot.db, name):
    #         try:
    #             bot.db.add_table(name, columns, key)
    #         except Exception, e:
    #             debug(MODULE, 'Table init fail - %s' % (e), DEBUG_LEVEL)
    #             raise e
    # else:
    #     msg = "DB init fail, setup the DB first!"
    #     debug(MODULE, msg, DEBUG_LEVEL)
    #     raise Exception(msg)

###############################################################################
# Helper function
###############################################################################

def is_true(value):
    """Return True if value is true

    :value: value
    :returns: True or False

    """
    try:
        return True if  value.lower() == 'true' else False
    except Exception:
        return value


def get_karma(db, who):
    """Get karma status from the table.

    :who: nickname of IRC user
    :returns: (karma, reason)

    """
    return db.get_nick_value(who, KARMA_KEY)


def set_karma(db, who, value):
    return db.set_nick_value(who, KARMA_KEY, value)


def update_karma(db, who, method='+'):
    """Update karma for specify IRC user.

    :who: nickname of IRC user
    :reason: reason
    :method: '+' or '-'

    """
    karma = get_karma(db, who)
    karma = int(karma) if karma else 0
    if method == '+':
        karma += 1
    else:
        karma -= 1

    set_karma(db, who, karma)


def _parse_msg(msg, method='+'):
    """Parse the message.

    :msg: message
    :returns: (who, reason)

    """
    try:
        who = msg.split(method)[0].strip().split().pop()

        if len(reason) == 0:
            reason = None
        #. check if nickname only contain [a-Z_]
        for s in who:
            if s not in "%s_" % string.ascii_letters:
                who = None
                break
    except Exception, e:
        debug(MODULE, "parse message fail - %s." % (e), DEBUG_LEVEL)
        return None, None
    return who


def parse_promote(msg):
    """Parse the message with '++'.

    :msg: message
    :returns: who

    """
    return _parse_msg(msg, method='+')


def parse_demote(msg):
    """Parse the message with '--'.

    :msg: message
    :returns: who

    """
    return _parse_msg(msg, method='-')


def meet_karma(db, trigger, parse_fun, inc_or_dec='+'):
    """Update karma status for specify IRC user

    :bot: willie.bot.Willie
    :trigger: willie.bot.Willie.Trigger

    """
    msg = trigger.bytes
    who = parse_fun(msg)
    if who:
        #. not allow self (pro|de)mote
        if not byself:
            if who == trigger.nick:
                return
        #. update karma
        update_karma(db, who)


###############################################################################
# Event & Command
###############################################################################

@willie.module.rule(r'^[\w][\S]+[\+\+]')
def meet_promote_karma(bot, trigger):
    """Update karma status for specify IRC user if get '++' message.
    """
    return meet_karma(bot.db, trigger, parse_promote, inc_or_dec='+')


@willie.module.rule(r'^[\w][\S]+[\-\-]')
def meet_demote_karma(bot, trigger):
    """Update karma status for specify IRC user if get '--' message.
    """
    return meet_karma(bot.db, trigger, parse_demote, inc_or_dec='-')


@willie.module.commands('karma')
def karma(bot, trigger):
    """Command to show the karma status for specify IRC user.
    """
    if trigger.group(2):
        who = trigger.group(2).strip().split()[0]
        karma = get_karma(bot.db, who)
        bot.say("%s has %s karma" % (who, karma))
    else:
        bot.say(".karma <nick> - Reports karma status for <nick>.")
