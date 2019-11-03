import discord, collections, random, re
from db import DB, SubjectDAO

class TwistBot(discord.Client):
	async def changeStatus(self, status):
		activity = discord.Activity(name=status, type=discord.ActivityType.watching)
		await self.change_presence(activity=activity)

	async def on_ready(self):
		DB.connection()
		print('Logged in as {0}.'.format(self.user))

		self.words = {}
		self.exclude = DB.getExcludes()
		self.maxMessageBeforeMine = 15
		self.messageCount = 0
		self.learn = False
		self.subject = []
		self.firstTime = True

		await self.changeStatus('nothing')

	async def on_message(self, message):
		if message.author == self.user:
			return

		def _cleanup(x):
			return re.sub(r'[^0-9a-zA-Z_\-]+', '', x)

		msg = discord.utils.escape_mentions(message.content)
		msg = re.sub(r'<@.*>', '', msg).strip(' ')
		words = msg.lower().split()
		words = list(map(_cleanup, words))

		for w in words:
			if len(w) < 2 or w in self.exclude:
				continue
			if w not in self.words.keys():
				self.words[w] = 0
			self.words[w] += 1

			SubjectDAO.put(w, message.content)

		shouldSendMessage = random.randint(0, 100) <= 50 # 50% of chance to send a message

		self.messageCount += 1
		if self.messageCount >= self.maxMessageBeforeMine:
			self.messageCount = 0

			sortedWords = collections.OrderedDict(sorted(self.words.items(), key=lambda kv: kv[1], reverse=True))
			if len(sortedWords.keys()) >= 4:
				top4 = list(sortedWords.keys())[:4]
				print(top4)

				self.words = {}
				await self.changeStatus('{0}'.format(top4[0]))
				self.subject = top4

		elif self.messageCount == 3:
			if not self.learn and shouldSendMessage and len(self.subject) >= 4:
				subs = list(map(_cleanup, self.subject))
				lst = SubjectDAO.fetchMulti(subs)
				if len(lst) > 0:
					msg = random.choice(lst)
					await message.channel.send(msg.replace("`", "'"))

client = TwistBot()
tok = ''
with open('__tok.dat', 'r') as f:
	tok = f.read()
client.run(tok)
DB.close()
