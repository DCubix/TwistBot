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
		self.maxMessageBeforeMine = 20
		self.messageCount = 0
		self.maxWords = 6
		self.learn = False

		self.subject = []#DB.randomWords(self.maxWords)
		await self.changeStatus('nothing')

	async def on_message(self, message):
		if message.author == self.user:
			return

		DB.saveUser(message.author.name, message.author.display_name)

		is_dm = message.channel.type == 'private'

		cmdmsg = message.content.lower()
		if 'twist' in cmdmsg:
			if 'thinking' in cmdmsg and 'about' in cmdmsg:
				subs = 'nothing' if len(self.subject) == 0 else ', '.join(self.subject)
				await message.channel.send("I'm thinking about `{0}` right now.".format(subs))
				return
			elif 'word' in cmdmsg and 'random' in cmdmsg:
				words = ' '.join(DB.randomWords(random.randint(2, 5)))
				await message.channel.send(words)
				return

		def _cleanup(x):
			return re.sub(r'[\W\-\?!\']+', '', x)

		msg = discord.utils.escape_mentions(message.content)

		# Cleanup
		msg = re.sub(r'<@.*>', '<name>', msg).strip() # Mentions
		msg = re.sub(r'<:.*>', '', msg).strip() # Custom emoji
		msg = re.sub(re.compile(r'```.*```', re.DOTALL), '', msg).strip() # Code
		msg = re.sub(re.compile(r'twist.*?(?:\W|$)', re.IGNORECASE), '<name> ', msg).strip() # "Twist"

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

		for w in groupedWords:
			DB.saveTrigger(w.replace("'", "`"), msg.replace("'", "`"))
			if w not in self.words.keys(): self.words[w] = 0
			self.words[w] += 1

		sortedWords = collections.OrderedDict(sorted(self.words.items(), key=lambda kv: kv[1], reverse=True))
		if len(sortedWords.items()) >= self.maxWords:
			print("CONTEXT: " + repr(list(sortedWords.items())[:self.maxWords]))
			self.subject = list(sortedWords.keys())[:self.maxWords]
			await self.changeStatus('"{0}"'.format(self.subject[0]))

		shouldSendMessage = random.randint(0, 1000) < 300 #self.messageCount % self.maxMessageBeforeMine == 0
		self.messageCount += 1

		if not self.learn and len(self.subject) >= self.maxWords and shouldSendMessage:
			subs = list(map(_cleanup, groupedWords + self.subject))
			lst = DB.getResponse(subs)
			if len(lst) > 0:
				msg = random.choice(lst)
				msg = msg.replace("`", "'")

				if '<name>' in msg:
					randName = DB.randomName().split()[0]
					msg = msg.replace('<name>', randName if randName is not None else random.choice(['dude', 'man', 'bruh', 'bro', 'lad']))

				typingTimeSecs = len(msg) * 0.1
				async with message.channel.typing():
					await asyncio.sleep(1 + typingTimeSecs)
				if not is_dm:
					await message.channel.send(msg)
				else:
					await message.author.send(msg)

				#self.subject = []
				#await self.changeStatus('nothing')
				#self.words = {}

client = TwistBot()
tok = ''
with open('__tok.dat', 'r') as f:
	tok = f.read().strip(' \n\r')
client.run(tok)
DB.close()
