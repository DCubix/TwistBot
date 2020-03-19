import discord, collections, random, re, asyncio, time, spacy, itertools
from spacy.lang.en import English
from threading import Thread
from db import DB
import commands

nlp = English()

STOP_WORDS = ['ourselves', 'hers', 'between', 'yourself', 'but', 'again', 'there', 'about', 'once', 'during', 'out', 'very', 'having', 'with', 'they', 'own', 'an', 'be', 'some', 'for', 'do', 'its', 'yours', 'such', 'into', 'of', 'most', 'itself', 'other', 'off', 'is', 's', 'am', 'or', 'who', 'as', 'from', 'him', 'each', 'the', 'themselves', 'until', 'below', 'are', 'we', 'these', 'your', 'his', 'through', 'don', 'nor', 'me', 'were', 'her', 'more', 'himself', 'this', 'down', 'should', 'our', 'their', 'while', 'above', 'both', 'up', 'to', 'ours', 'had', 'she', 'all', 'no', 'when', 'at', 'any', 'before', 'them', 'same', 'and', 'been', 'have', 'in', 'will', 'on', 'does', 'yourselves', 'then', 'that', 'because', 'what', 'over', 'why', 'so', 'can', 'did', 'not', 'now', 'under', 'he', 'you', 'herself', 'has', 'just', 'where', 'too', 'only', 'myself', 'which', 'those', 'i', 'after', 'few', 'whom', 't', 'being', 'if', 'theirs', 'my', 'against', 'a', 'by', 'doing', 'it', 'how', 'further', 'was', 'here', 'than']

async def removeUsersTask(bot):
	while True:
		await asyncio.sleep(60)
		bot.peopleInConvo = []

async def messageAllowanceTime(bot):
	while True:
		await asyncio.sleep(1)
		if bot.justSent:
			await asyncio.sleep(30)
			bot.justSent = False

async def decayTask(bot):
	while True:
		await asyncio.sleep(5)

		todel = []
		for k in bot.words.keys():
			bot.words[k] -= 0.1
			if bot.words[k] <= 0:
				todel.append(k)
		for w in todel:
			del bot.words[w]

		# set subject
		sortedWords = collections.OrderedDict(sorted(bot.words.items(), key=lambda kv: kv[1], reverse=True))
		count = len(sortedWords.items())
		if count > 0:
			ctx = list(sortedWords.items())[:(count if count < bot.maxWords else bot.maxWords)]
			print("CONTEXT: " + str(ctx))

			bot.subject = [k for k, _ in ctx]
			await bot.changeStatus('{0}'.format(bot.subject[0]))
		else:
			bot.subject = []
			await bot.changeStatus('the void')

class TwistBot(discord.Client):

	async def changeStatus(self, status):
		activity = discord.Activity(name=status, type=discord.ActivityType.watching)
		await self.change_presence(activity=activity)

	async def on_ready(self):
		DB.connection()
		print('Logged in as {0}.'.format(self.user))

		self.words = {}
		self.maxWords = 4
		self.justSent = False
		self.lastMention = None
		self.peopleInConvo = []
		self.learning = False

		self.commands = {
			'get_context': commands.cmdThinking,
			'clear_context': commands.cmdClrContext,
			'new_context': commands.cmdNewContext,
			'get_words': commands.cmdRndWords,
			'learning_mode': commands.cmdLearningMode,
			'list_commands': commands.cmdList,
		}

		asyncio.create_task(decayTask(self))
		asyncio.create_task(messageAllowanceTime(self))
		asyncio.create_task(removeUsersTask(self))

		self.previousWords = []
		self.subject = []
		await self.changeStatus('the void')

	async def on_message(self, message):
		if message.author == self.user:
			return

		if DB.userID(message.author.name) is None:
			self.subject = ['hello', message.author.name, 'hi', 'hey']
			DB.saveUser(message.author.name, message.author.display_name)

		is_dm = message.channel.type == 'private'

		mentionedMe = False
		for user in message.mentions:
			if user.id == self.user.id:
				self.lastMention = message.author.name
				mentionedMe = True
				break

		if message.author.name not in self.peopleInConvo:
			self.peopleInConvo.append(message.author.name)

		cmdmsg = re.sub(r'<@.*>', '', message.content).strip()
		if 'twist' in cmdmsg.lower() or mentionedMe:
			self.lastMention = message.author.name
			mentionedMe = True

			spl = cmdmsg.split()
			cmd = spl[0].strip()
			args = spl[1:]

			if cmd in self.commands.keys():
				await self.commands[cmd](self, message, args)
				return

		def _cleanup(x):
			return re.sub(r'[^\w\d\'"]+|_', '', x)

		def _cleanupPunctuation(x):
			return re.sub(r'[\.,\?!:]', '', x).replace("'", "`").strip()

		msg = discord.utils.escape_mentions(message.content)

		# Cleanup
		msg = re.sub(r'<@.*>', '<name>', msg).strip() # Mentions
		msg = re.sub(r'<:.*>', '', msg).strip() # Custom emoji
		msg = re.sub(re.compile(r'```.*```', re.DOTALL), '', msg).strip() # Code
		msg = re.sub(re.compile(r'twist.*?(?=\W|$)', re.IGNORECASE), '<name> ', msg).strip() # "Twist"
		msg = msg.replace("'", "`")

		# Remove <name>
		msg = ' '.join(list(filter(lambda x: x.strip() != '<name>' and len(x.strip()) > 0, msg.split(' '))))

		print(msg.lower(), end=' ')

		# Tokenize
		lst = nlp(msg.lower())
		words = [x.orth_ for x in lst]

		print(words)

		# Remove stop words
		words = list(filter(lambda x: x.strip() not in STOP_WORDS, words))

		# Clean punctuation
		words = list(map(_cleanup, words))

		# Remove empties
		words = list(filter(lambda x: len(x.strip()) > 0, words))
		excludes = DB.getExcludes()

		# Filter exclusion list
		words = list(filter(lambda x: x not in excludes, words))

		for w in words:
			DB.saveTrigger(w, msg)

			if w not in self.words.keys(): self.words[w] = 0
			self.words[w] += 1

		subs = []
		for ng in words: subs.append(ng)
		for ng in self.subject:
			if ng not in subs: subs.append(ng)

		shouldSendMessage = random.randint(0, 100) <= 15 and not self.justSent and not self.learning
		if (len(subs) > 0 and shouldSendMessage) or (len(subs) > 0 and mentionedMe):
			msg = DB.getResponse(subs)
			if msg is not None:
				self.justSent = True

				if self.lastMention is None:
					randName = DB.randomName() if len(self.peopleInConvo) == 0 else random.choice(self.peopleInConvo)
					randName = randName if len(self.peopleInConvo) == 0 else DB.getDisplayName(randName)
					randName = randName.split()[0]
				else:
					randName = DB.getDisplayName(self.lastMention)

				msg = re.sub(re.compile(r'twistbot', re.IGNORECASE), randName, msg)
				msg = re.sub(re.compile(r'<name>', re.IGNORECASE), randName, msg)

				typingTimeSecs = len(msg) * 0.1
				async with message.channel.typing():
					await asyncio.sleep(1 + typingTimeSecs)

				if not is_dm:
					await message.channel.send(msg)
				else:
					await message.author.send(msg)
				self.lastMention = None

client = TwistBot()
tok = ''
with open('__tok.dat', 'r') as f:
	tok = f.read().strip(' \n\r')
client.run(tok)
DB.close()
