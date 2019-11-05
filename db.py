import sqlite3

dbsql = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS tb_word(
	id integer primary key,
	data text
);

CREATE TABLE IF NOT EXISTS tb_user(
	id integer primary key,
	name text,
	display_name text
);

CREATE TABLE IF NOT EXISTS tb_sentence(
	id integer primary key,
	data text
);

CREATE TABLE IF NOT EXISTS tb_trigger(
	trigger integer,
	response integer,
	FOREIGN KEY(trigger) REFERENCES tb_word(id),
	FOREIGN KEY(response) REFERENCES tb_sentence(id)
);

CREATE TABLE IF NOT EXISTS tb_exclude(
	id integer primary key,
	word text
);
"""

class DB:
	conn = None

	@staticmethod
	def migrateData(db):
		print("Migrating Data...")
		oldcon = sqlite3.connect(db)
		cur = oldcon.cursor()
		cur.execute("SELECT trigger, response FROM tb_subject")
		# [(id, trigger, response), ...]
		recs = cur.fetchall()
		DB.saveTriggers(recs)
		cur.close()
		oldcon.close()
		print("Done!")

	@staticmethod
	def connection():
		if DB.conn is None:
			DB.conn = sqlite3.connect('tb_data.db')
			cursor = DB.conn.cursor()
			for sql in dbsql.split(';'):
				cursor.execute(sql)
			DB.conn.commit()
			cursor.close()

			#DB.migrateData('data.db')

		return DB.conn

	@staticmethod
	def close():
		DB.conn.close()

	@staticmethod
	def userID(name):
		sql = "SELECT id FROM tb_user WHERE name = '{0}'".format(name.replace("'", "`"))
		cursor = DB.connection().cursor()
		cursor.execute(sql)
		recs = cursor.fetchall()
		rets = []
		for r in recs:
			rets.append(r[0])
		cursor.close()
		return rets[0] if len(rets) > 0 else None

	@staticmethod
	def saveUser(name, displayName):
		uid = DB.userID(name)
		cursor = DB.connection().cursor()
		if uid is not None:
			sql = "UPDATE tb_user SET display_name = '{0}' WHERE name = '{1}'".format(displayName.replace("'", "`"), name.replace("'", "`"))
			cursor.execute(sql)
			DB.conn.commit()
			cursor.close()
			return uid
		else:
			sql = "INSERT INTO tb_user('name', 'display_name') VALUES('{0}', '{1}')".format(name.replace("'", "`"), displayName.replace("'", "`"))
			cursor.execute(sql)
			DB.conn.commit()
			gid = cursor.lastrowid
			cursor.close()
			return gid

	@staticmethod
	def getExcludes():
		sql = "SELECT word FROM tb_exclude"
		cursor = DB.connection().cursor()
		cursor.execute(sql)
		recs = cursor.fetchall()
		rets = []
		for r in recs:
			rets.append(r[0])
		cursor.close()
		return rets

	@staticmethod
	def wordID(w):
		w = w.replace("'", "`")
		sql = "SELECT id FROM tb_word WHERE data = '{0}'".format(w)
		cursor = DB.connection().cursor()
		cursor.execute(sql)
		recs = cursor.fetchall()
		rets = []
		for r in recs:
			rets.append(r[0])
		cursor.close()
		return rets[0] if len(rets) > 0 else None

	@staticmethod
	def sentenceID(s):
		s = s.replace("'", "`")
		sql = "SELECT id FROM tb_sentence WHERE data = '{0}'".format(s)
		cursor = DB.connection().cursor()
		cursor.execute(sql)
		recs = cursor.fetchall()
		rets = []
		for r in recs:
			rets.append(r[0])
		cursor.close()
		return rets[0] if len(rets) > 0 else None

	@staticmethod
	def saveWord(w):
		cursor = DB.connection().cursor()
		w = w.replace("'", "`")
		sql = """
INSERT INTO tb_word('data')
SELECT '{0}'
WHERE NOT EXISTS(SELECT 1 FROM tb_word WHERE data = '{0}')
		"""
		cursor.execute(sql.format(w))
		DB.conn.commit()
		gid = cursor.lastrowid
		cursor.close()
		return gid

	@staticmethod
	def saveSentence(sent):
		cursor = DB.connection().cursor()
		sent = sent.replace("'", "`")
		sql = """
INSERT INTO tb_sentence('data')
SELECT '{0}'
WHERE NOT EXISTS(SELECT 1 FROM tb_sentence WHERE data = '{0}')
		"""
		cursor.execute(sql.format(sent))
		DB.conn.commit()
		gid = cursor.lastrowid
		cursor.close()
		return gid

	@staticmethod
	def saveTrigger(word, sentence):
		wid = DB.wordID(word)
		sid = DB.sentenceID(sentence)
		if wid is None: wid = DB.saveWord(word)
		if sid is None: sid = DB.saveSentence(sentence)

		sql = "INSERT INTO tb_trigger('trigger', 'response') VALUES({0}, {1})".format(wid, sid)
		cursor = DB.connection().cursor()
		cursor.execute(sql)
		DB.conn.commit()
		cursor.close()

	@staticmethod
	def saveTriggers(triggers):
		cursor = DB.connection().cursor()
		for word, sentence in triggers:
			wid = DB.wordID(word)
			sid = DB.sentenceID(sentence)
			if wid is None: wid = DB.saveWord(word)
			if sid is None: sid = DB.saveSentence(sentence)
			sql = "INSERT INTO tb_trigger('trigger', 'response') VALUES({0}, {1})".format(wid, sid)
			cursor.execute(sql)
		DB.conn.commit()
		cursor.close()

	@staticmethod
	def randomWords(count):
		sql = "SELECT data FROM tb_word ORDER BY RANDOM() LIMIT " + str(count)
		cursor = DB.connection().cursor()
		cursor.execute(sql)
		recs = cursor.fetchall()
		rets = []
		for r in recs:
			rets.append(r[0])
		cursor.close()
		return list(map(lambda x: x.replace("`", "'"), rets))

	@staticmethod
	def getResponse(triggers):
		opts = ", ".join(list(map(lambda x: "'{0}'".format(x.replace("'", "`")), triggers)))
		sql = """
SELECT DISTINCT
	s.data AS response
FROM tb_trigger t
	INNER JOIN tb_word w ON w.id == t.trigger
	INNER JOIN tb_sentence s ON s.id == t.response
WHERE w.data in ({0})
		""".format(opts)
		cursor = DB.connection().cursor()
		cursor.execute(sql)
		recs = cursor.fetchall()
		rets = []
		for r in recs:
			rets.append(r[0])
		cursor.close()
		return list(map(lambda x: x.replace("`", "'"), rets))