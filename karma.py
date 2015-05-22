#!/usr/bin/env python
# encoding: utf-8

"""
karma.py - A karma module for willie.
Copyright 2013, Timothy Lee <marlboromoo@gmail.com>
Licensed under the MIT License.
"""

from willie.module import commands

MODULE = 'karma'
WHO = 'who'
KARMA = 'karma'
KARMA_KEY = 'karma'
REASON = 'reason'
DEBUG_LEVEL = 'verbose'

feedback = None
byself = None


def debug_(tag, text, level):
    """Mimic willie.debug function for pytest to use.
    """
    print("[%s] %s" % (tag, text))

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
    # get debug function
    global debug
    debug = bot.debug if bot.debug else debug

    #. get settings
    feedback_, byself_, debug_ = True, False, False

    try:
        config = getattr(bot.config, MODULE)
        feedback_ = is_true(config.feedback)
        byself_ = is_true(config.byself)
    except Exception as e:
        pass
    global feedback, byself
    feedback = feedback_
    byself = byself_


def is_true(value):
    """Return True if value is true

    :value: value
    :returns: True or False

    """
    try:
        return True if value.lower() == 'true' else False
    except Exception:
        return value


def get_karma(db, who):
    """Get karma status from willie.db.get_nick_value.

    :db: bot.db instance
    :who: nickname of IRC user
    :returns: karma

    """
    return db.get_nick_value(who, KARMA_KEY)


def set_karma(db, who, value):
    """Set the karma via willie.db.set_nick_value.
    :db: bot.db instance
    :who: nickname of IRC user
    :value: the new karma value

    :returns: karma
    """
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


def get_nick(trigger):
    return trigger.group(2).strip().split()[0]


@commands('dm', 'demotivate')
def decrement_karma(bot, trigger):
    nick = get_nick(trigger)
    if nick:
        bot.say('You\'re doing horrible work %s!' % nick)
        update_karma(bot.db, nick, '-')


@commands('m', 'motivate', 'thanks', 'thank')
def increment_karma(bot, trigger):
    nick = get_nick(trigger)
    if nick:
        bot.say('You\'re doing good work %s!' % nick)
        update_karma(bot.db, nick, '+')


@commands('karma')
def karma(bot, trigger):
    """Command to show the karma status for specify IRC user.
    """
    if trigger.group(2):
        nick = get_nick(trigger)
        karma = get_karma(bot.db, nick)
        bot.say("%s has %s karma" % (nick, karma))
    else:
        bot.say(".karma <nick> - Reports karma status for <nick>.")
