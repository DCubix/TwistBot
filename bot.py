import discord, collections, random, re, asyncio, time
from db import DB

class TwistBot(discord.Client):
	async def changeStatus(self, status):
		activity = discord.Activity(name=status, type=discord.ActivityType.watching)
		await self.change_presence(activity=activity)

	async def on_ready(self):
		DB.connection()
		print('Logged in as {0}.'.format(self.user))

		self.words = {}
		self.maxMessageBeforeMine = 30
		self.messageCount = 0
		self.maxWords = 4
		self.learn = False

		self.subject = DB.randomWords(self.maxWords)
		await self.changeStatus('"{0}"'.format(self.subject[0]))

	async def on_message(self, message):
		if message.author == self.user:
			return
		if message.author.bot:
			return

		is_dm = message.channel.type == 'private'
		print(message.content)

		cmdmsg = message.content.lower()
		if 'thinking' in cmdmsg and 'twist' in cmdmsg and 'what' in cmdmsg:
			subs = 'nothing' if len(self.subject) == 0 else ', '.join(self.subject)
			await message.channel.send("I'm thinking about `{0}` right now.".format(subs))
			return

		def _cleanup(x):
			return re.sub(r'[^0-9a-zA-Z_\-]+', '', x)

		msg = discord.utils.escape_mentions(message.content)
		msg = re.sub(r'<@.*>', '', msg).strip()
		msg = re.sub(r'<:.*>', '', msg).strip()
		msg = re.sub(re.compile(r'```.*```', re.DOTALL), '', msg).strip()
		words = msg.lower().split()
		words = list(map(_cleanup, words))

		excludes = DB.getExcludes()

		# group and filter them
		groupedWords = []
		while len(words) > 0:
			w = words.pop(0).strip()
			if len(w) == 0: continue
			if w in excludes: continue
			while len(w) < 4 and len(words) > 0:
				w += " " + words.pop(0).strip()
			groupedWords.append(w.strip())

		if len(self.words.keys()) >= 100:
			self.subject = DB.randomWords(self.maxWords)
			await self.changeStatus('"{0}"'.format(self.subject[0]))
			self.words = {}

		for w in groupedWords:
			DB.saveTrigger(w, msg)
			if w not in self.words.keys(): self.words[w] = 0
			self.words[w] += 1

		sortedWords = collections.OrderedDict(sorted(self.words.items(), key=lambda kv: kv[1], reverse=True))
		if len(sortedWords.items()) >= self.maxWords:
			await asyncio.sleep(5)
			self.subject = list(sortedWords.keys())[:self.maxWords]
			await self.changeStatus('"{0}"'.format(self.subject[0]))
			print(self.subject)

		shouldSendMessage = random.randint(0, 100) <= 30

		if not self.learn and len(self.subject) >= self.maxWords and shouldSendMessage:
			subs = list(map(_cleanup, groupedWords + self.subject))
			lst = DB.getResponse(subs)
			if len(lst) > 0:
				msg = random.choice(lst)
				typingTimeSecs = len(msg) * 0.1
				async with message.channel.typing():
					await asyncio.sleep(1 + typingTimeSecs)
				if not is_dm:
					await message.channel.send(msg.replace("`", "'"))
				else:
					await message.author.send(msg.replace("`", "'"))

client = TwistBot()
tok = ''
with open('__tok.dat', 'r') as f:
	tok = f.read().strip(' \n\r')
client.run(tok)
DB.close()
