import discord, collections, random, re, asyncio
from db import DB, SubjectDAO

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
		self.learn = False
		self.subject = SubjectDAO.randomSubject()

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
		msg = re.sub(r'<@.*>', '', msg).strip(' ')
		msg = re.sub(r'<:.*>', '', msg).strip(' ')
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

		shouldSendMessage = random.randint(0, 100) <= 40 # 40% of chance to send a message

		self.messageCount += 1
		if self.messageCount >= self.maxMessageBeforeMine:
			self.messageCount = 0

			await asyncio.sleep(5)

			sortedWords = collections.OrderedDict(sorted(self.words.items(), key=lambda kv: kv[1], reverse=True))
			if len(sortedWords.keys()) >= 4:
				top4 = list(sortedWords.keys())[:4]
				print(top4)

				self.words = {}
				await self.changeStatus('{0}'.format(top4[0].upper()))
				self.subject = top4

		if not self.learn and shouldSendMessage and len(self.subject) >= 4:
			subs = list(map(_cleanup, self.subject))

			lst = SubjectDAO.fetchMulti(subs + words)
			if len(lst) > 0:
				msg = random.choice(lst)
				await asyncio.sleep(2)
				await message.channel.send(msg.replace("`", "'"))

client = TwistBot()
tok = ''
with open('__tok.dat', 'r') as f:
	tok = f.read()
client.run(tok)
DB.close()
