import discord, collections, random, re, asyncio, time
from db import DB

async def cmdSetMode(bot, message, args):
    mode = args[0]
    if mode in ['NORMAL', 'BASIC', 'ADVANCED']:
        bot.mode = mode
    else:
        await message.channel.send('The mode "{0}" is invalid.'.format(mode))

async def cmdThinking(bot, message, args):
    subs = 'nothing' if len(bot.subject) == 0 else ', '.join(bot.subject)
    await message.channel.send("I'm thinking about `{0}`.".format(subs))

async def cmdRndWords(bot, message, args):
    words = ' '.join(list(map(lambda x: x.replace("`", "'"), DB.randomWords(random.randint(1, 8)))))
    await message.channel.send(words)

async def cmdList(bot, message, args):
    cmds = ', '.join(list(bot.commands.keys()))
    await message.channel.send('These are the available commands, {0}: `{1}`'.format(message.author.display_name.split()[0], cmds))

async def cmdNewContext(bot, message, args):
    bot.subject = DB.randomWords(bot.maxWords)
    for w in bot.subject:
        bot.words[w] = random.uniform(1, 2)
    await bot.changeStatus('{0}'.format(bot.subject[0]))

async def cmdClrContext(bot, message, args):
    bot.subject = []
    bot.words = {}
    await bot.changeStatus('nothing')