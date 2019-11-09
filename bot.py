import discord, collections, random, re, asyncio, time
from threading import Thread
from db import DB

STOP_WORDS = ['ourselves', 'hers', 'between', 'yourself', 'but', 'again', 'there', 'about', 'once', 'during', 'out', 'very', 'having', 'with', 'they', 'own', 'an', 'be', 'some', 'for', 'do', 'its', 'yours', 'such', 'into', 'of', 'most', 'itself', 'other', 'off', 'is', 's', 'am', 'or', 'who', 'as', 'from', 'him', 'each', 'the', 'themselves', 'until', 'below', 'are', 'we', 'these', 'your', 'his', 'through', 'don', 'nor', 'me', 'were', 'her', 'more', 'himself', 'this', 'down', 'should', 'our', 'their', 'while', 'above', 'both', 'up', 'to', 'ours', 'had', 'she', 'all', 'no', 'when', 'at', 'any', 'before', 'them', 'same', 'and', 'been', 'have', 'in', 'will', 'on', 'does', 'yourselves', 'then', 'that', 'because', 'what', 'over', 'why', 'so', 'can', 'did', 'not', 'now', 'under', 'he', 'you', 'herself', 'has', 'just', 'where', 'too', 'only', 'myself', 'which', 'those', 'i', 'after', 'few', 'whom', 't', 'being', 'if', 'theirs', 'my', 'against', 'a', 'by', 'doing', 'it', 'how', 'further', 'was', 'here', 'than']


async def messageAllowanceTime(bot):
	while True:
		await asyncio.sleep(1)
		if bot.justSent:
			await asyncio.sleep(30)
			bot.justSent = False

async def decayTask(bot):
	while True:
		await asyncio.sleep(10)

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
			print("CONTEXT: Empty")
			await bot.changeStatus('nothing')

class TwistBot(discord.Client):
	async def changeStatus(self, status):
		activity = discord.Activity(name=status, type=discord.ActivityType.watching)
		await self.change_presence(activity=activity)

	async def on_ready(self):
		DB.connection()
		print('Logged in as {0}.'.format(self.user))

		self.words = {}
		self.maxMessageBeforeMine = 20
		self.messageCount = 0
		self.maxWords = 4
		self.learn = False
		self.justSent = False

		asyncio.create_task(decayTask(self))
		asyncio.create_task(messageAllowanceTime(self))

		self.previousWords = []
		self.subject = []
		await self.changeStatus('nothing')

	async def on_message(self, message):
		if message.author == self.user:
			return

		if DB.userID(message.author.name) is None:
			self.subject = ['hello', message.author.name, 'hi', 'hey']
		DB.saveUser(message.author.name, message.author.display_name)

		is_dm = message.channel.type == 'private'

		cmdmsg = message.content.lower()
		if 'twist' in cmdmsg:
			if 'thinking' in cmdmsg and 'about' in cmdmsg:
				subs = 'nothing' if len(self.subject) == 0 else ', '.join(self.subject)
				await message.channel.send("I'm thinking about `{0}`.".format(subs))
				return
			elif 'word' in cmdmsg and 'random' in cmdmsg:
				words = ' '.join(DB.randomWords(random.randint(2, 5)))
				await message.channel.send(words)
				return

		def _cleanup(x):
			return re.sub(r'[^\w\d\'"]+|_', '', x)

		msg = discord.utils.escape_mentions(message.content)

		# Cleanup
		msg = re.sub(r'<@.*>', '<name>', msg).strip() # Mentions
		msg = re.sub(r'<:.*>', '', msg).strip() # Custom emoji
		msg = re.sub(re.compile(r'```.*```', re.DOTALL), '', msg).strip() # Code
		msg = re.sub(re.compile(r'twist.*?(?:\W|$)', re.IGNORECASE), '<name> ', msg).strip() # "Twist"
		msg = msg.replace("'", "`")

		# Tokenize
		words = msg.lower().split()

		# Remove stop words
		words = list(filter(lambda x: x != '<name>' and x not in STOP_WORDS, words))

		# Clean punctuation
		words = list(map(_cleanup, words))

		# Remove empties
		words = list(filter(lambda x: len(x.strip()) > 0, words))
		excludes = DB.getExcludes()

		for w in words:
			if w in excludes: continue

			DB.saveTrigger(w, msg)

			if w not in self.words.keys(): self.words[w] = 0
			self.words[w] += 1

		shouldSendMessage = random.randint(0, 100) <= 15 and not self.justSent
		if len(self.subject) > 0 and shouldSendMessage:
			self.justSent = True
			subs = self.subject

			lst = DB.getResponse(subs)
			if len(lst) > 0:
				msg = random.choice(lst)
				randName = DB.randomName().split()[0]
				msg = re.sub(re.compile(r'twistbot', re.IGNORECASE), randName, msg)
				randName = DB.randomName().split()[0]
				msg = re.sub(re.compile(r'<name>', re.IGNORECASE), randName, msg)

				typingTimeSecs = len(msg) * 0.1
				async with message.channel.typing():
					await asyncio.sleep(1 + typingTimeSecs)

				if not is_dm:
					await message.channel.send(msg)
				else:
					await message.author.send(msg)

client = TwistBot()
tok = ''
with open('__tok.dat', 'r') as f:
	tok = f.read().strip(' \n\r')
client.run(tok)
DB.close()
