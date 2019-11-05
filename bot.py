import discord, collections, random, re, asyncio, time, nltk, subprocess
from db import DB
from textblob import TextBlob

subprocess.check_output(['python3', '-m', 'textblob.download_corpora'])

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

		self.subject = []
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
				await message.channel.send("I'm thinking about `{0}`.".format(subs))
				return
			elif 'word' in cmdmsg and 'random' in cmdmsg:
				words = ' '.join(DB.randomWords(random.randint(2, 5)))
				await message.channel.send(words)
				return

		def _cleanup(x):
			return re.sub(r'[\W\-\?!\']+', '', x)

		msg = discord.utils.escape_mentions(message.content)

		# Cleanup
		msg = re.sub(r'<@.*>', 'twistbot', msg).strip() # Mentions
		msg = re.sub(r'<:.*>', '', msg).strip() # Custom emoji
		msg = re.sub(re.compile(r'```.*```', re.DOTALL), '', msg).strip() # Code

		msg = TextBlob(msg)

		words = msg.words.lemmatize()
		words = list(filter(lambda x: x != 'twistbot', words))
		words = list(map(lambda x: x.lower(), words))
		print('WORDS: ' + str(words))
		excludes = DB.getExcludes()

		for w in words:

			if w in excludes: continue
			DB.saveTrigger(w.replace("'", "`"), msg.replace("'", "`"))

			if w not in self.words.keys(): self.words[w] = 0
			self.words[w] += 1

		sortedWords = collections.OrderedDict(sorted(self.words.items(), key=lambda kv: kv[1], reverse=True))
		count = len(sortedWords.items())
		if count > 0:
			ctx = list(sortedWords.items())[:(count if count < self.maxWords else self.maxWords)]
			print("CONTEXT: " + str(ctx))

			self.subject = [k for k, _ in ctx]
			await self.changeStatus('"{0}"'.format(self.subject[0]))

		shouldSendMessage = random.randint(0, 1000) < 500 #self.messageCount % self.maxMessageBeforeMine == 0
		# self.messageCount += 1

		if not self.learn and len(self.subject) > 0 and shouldSendMessage:
			subsUc = self.subject + words
			random.shuffle(subsUc)

			subs = list(map(_cleanup, subsUc))
			lst = DB.getResponse(subs)
			if len(lst) > 0:
				msg = TextBlob(random.choice(lst))
				nouns = msg.noun_phrases

				msg = str(msg)

				randName = DB.randomName()
				msg = re.sub(re.compile(r'twistbot', re.IGNORECASE), randName, msg)
				randName = DB.randomName()
				msg = re.sub(re.compile(r'<name>', re.IGNORECASE), randName, msg)

				msg = TextBlob(msg.replace("`", "'"))
				msg.correct()

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
