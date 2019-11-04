import discord, collections, random, re, asyncio, time
from db import DB, SubjectDAO

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
		self.maxWords = 6
		self.learn = False

		self.subject = SubjectDAO.randomSubject(self.maxWords)
		await self.changeStatus('{0}'.format(self.subject[0].upper()))

	async def on_message(self, message):
		if message.author == self.user:
			return

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
		for w in words:
			if len(w) < 2 or w in excludes:
				continue
			if w not in self.words.keys():
				self.words[w] = 0
			self.words[w] += 1

			SubjectDAO.put(w, msg)

		shouldSendMessage = random.randint(0, 100) <= 30

		# shouldPickRandomSubject = random.randint(0, 100) <= 5
		# if shouldPickRandomSubject:
		# 	self.subject = SubjectDAO.randomSubject(self.maxWords)
		# 	print(self.subject)
		# 	await self.changeStatus('{0}'.format(self.subject[0].upper()))

		self.messageCount += 1
		if self.messageCount >= self.maxMessageBeforeMine:
			self.messageCount = 0
			print(self.words)

			await asyncio.sleep(10)

			sortedWords = collections.OrderedDict(sorted(self.words.items(), key=lambda kv: kv[1], reverse=True))
			if len(sortedWords.keys()) >= self.maxWords:
				top = list(sortedWords.keys())[:self.maxWords]

				self.words = {}

				self.subject = top
				await self.changeStatus('{0}'.format(top[0].upper()))
				print(self.subject)

		if self.messageCount >= 0 and self.messageCount <= self.maxMessageBeforeMine // 2:
			if not self.learn and shouldSendMessage and len(self.subject) >= self.maxWords:
				subs = list(map(_cleanup, self.subject))

				lst = SubjectDAO.fetchMulti(subs + words)
				if len(lst) > 0:
					msg = random.choice(lst)
					await asyncio.sleep(5)
					await message.channel.send(msg.replace("`", "'"))

client = TwistBot()
tok = ''
with open('__tok.dat', 'r') as f:
	tok = f.read().strip(' \n\r')
client.run(tok)
DB.close()
