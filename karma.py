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


def get_real_nick(db, who):
    """Find the user's canonical nick by looking for any alias'

    :db: the willie db
    :who: the alias

    :returns: the canonical nick or alias
    """

    # This will recurse until who == who
    real_nick = db.get_nick_value(who, 'karma_nick_alias')
    if real_nick == who or not real_nick:
        return who
    else:
        return get_real_nick(db, real_nick)


def update_karma(db, who, method='+', amount=1):
    """Update karma for specify IRC user.
    :who: nickname of IRC user
    :reason: reason
    :method: '+' or '-'
    :amount: the number of karma you want to add/subtract, default is 1
    """
    nick = get_real_nick(db, who)
    karma = get_karma(db, nick)
    karma = int(karma) if karma else 0
    if method == '+':
        karma += 1
    else:
        karma -= 1

    set_karma(db, nick, karma)


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


@commands('karma_alias')
def karma_alias(bot, trigger):
    """Command to alias a nick with another name.
    """
    alias = trigger.group(3)
    joiner = trigger.group(4)
    target = trigger.group(5)

    if not target or not alias or joiner != 'to':
        bot.say('Whoa there! I need a nick and an alias '
                'like this: !karma_alias real_nick to nick_alias')
        return

    # Move the karma over. First grab the karma
    new_karma = get_karma(bot.db, alias)

    # get our real nick
    target = get_real_nick(bot.db, target)

    # Update our real nick's karma
    update_karma(bot.db, target, '+', new_karma)

    # Remove our old alias' karma
    update_karma(bot.db, alias, '-', new_karma)

    # Update the db alias.
    bot.db.set_nick_value(alias, 'karma_nick_alias', target)

    # Let the user know
    bot.say('Got it! Let it be known that '
            '%s gets karma for %s' % (target, alias))
    bot.say('%s now has %s karma' % (target, get_karma(bot.db, target)))


@commands('karma_aliases')
def karma_list_aliases(bot, trigger):
    nick = trigger.group(3)
    alias = bot.db.get_nick_value(nick, 'karma_nick_alias')
    if alias:
        bot.say('%s is aliased to %s' % (nick, alias))
    else:
        bot.say('%s is not aliased' % (nick))


@commands('karma_rm_alias')
def karma_rm_alias(bot, trigger):
    nick = trigger.group(3)
    bot.db.set_nick_value(nick, 'karma_nick_alias', None)
    bot.say('%s now has no alias' % (nick))


@commands('karma')
def karma(bot, trigger):
    """Command to show the karma status for specify IRC user.
    """
    print('here')
    if trigger.group(2):
        nick = get_nick(trigger)
        karma = get_karma(bot.db, nick)
        bot.say("%s has %s karma" % (nick, karma))
    else:
        bot.say(".karma <nick> - Reports karma status for <nick>.")
