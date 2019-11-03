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
		self.maxMessageBeforeMine = 10
		self.messageCount = 0
		self.learn = True
		self.subject = []
		self.firstTime = True

		await self.changeStatus('nothing')

	async def on_message(self, message):
		if message.author == self.user:
			return

		def _cleanup(x):
			return re.sub(r'[^0-9a-zA-Z_\-]+', '', x)

		words = message.content.lower().split()
		words = list(map(_cleanup, words))

		for w in words:
			if len(w) < 2 or w in self.exclude:
				continue
			if w not in self.words.keys():
				self.words[w] = 0
			self.words[w] += 1

			SubjectDAO.put(w, message.content)

		shouldChangeSubject = random.randint(0, 100) >= 60 # 60% of chance to change the subject

		self.messageCount += 1
		if self.messageCount >= self.maxMessageBeforeMine:
			self.messageCount = 0

			sortedWords = collections.OrderedDict(sorted(self.words.items(), key=lambda kv: kv[1], reverse=True))
			top2 = list(sortedWords.keys())[:2]
			print(top2)

			if shouldChangeSubject or self.firstTime:
				await self.changeStatus('{0} and {1}'.format(top2[0], top2[1]))
				self.subject = top2
				self.firstTime = False

#https://discordapp.com/api/oauth2/authorize?client_id=626879584666779648&permissions=117760&scope=bot
			if not self.learn:
				l0 = SubjectDAO.fetch(self.subject[0])
				l1 = SubjectDAO.fetch(self.subject[1])
				lst = l0 + l1

				if len(lst) > 0:
					msg = random.choice(lst)
					await message.channel.send(msg.replace("`", "'"))

client = TwistBot()
tok = ''
with open('__tok.dat', 'r') as f:
	tok = f.read()
client.run(tok)
DB.close()
