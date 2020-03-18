import sqlite3, random

dbsql = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS tb_subject(
	id integer primary key,
	data text
);

CREATE TABLE IF NOT EXISTS tb_user(
	id integer primary key,
	name text,
	display_name text
);

CREATE TABLE IF NOT EXISTS tb_response(
	id integer primary key,
	data text,
	date_time real
);

CREATE TABLE IF NOT EXISTS tb_trigger(
	subject integer,
	response integer,
	date_time real,
	FOREIGN KEY(subject) REFERENCES tb_subject(id),
	FOREIGN KEY(response) REFERENCES tb_response(id)
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
			DB.conn = sqlite3.connect('data.db')
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
	def randomName():
		sql = "SELECT display_name FROM tb_user ORDER BY random() LIMIT 1"
		cursor = DB.connection().cursor()
		cursor.execute(sql)
		recs = cursor.fetchall()
		rets = []
		for r in recs:
			rets.append(r[0])
		cursor.close()
		return rets[0] if len(rets) > 0 else random.choice(['buddy', 'bruh', 'dude', 'lad'])

	@staticmethod
	def getDisplayName(name):
		uid = DB.userID(name)
		if uid is None:
			return random.choice(['buddy', 'bruh', 'dude', 'lad', 'pal', 'man'])
		sql = "SELECT display_name FROM tb_user WHERE name = '{0}'".format(name)
		cursor = DB.connection().cursor()
		cursor.execute(sql)
		recs = cursor.fetchall()
		rets = []
		for r in recs:
			rets.append(r[0])
		cursor.close()
		return rets[0] if len(rets) > 0 else random.choice(['buddy', 'bruh', 'dude', 'lad'])

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
	def subjectID(w):
		w = w.replace("'", "`")
		sql = "SELECT id FROM tb_subject WHERE data = '{0}'".format(w)
		cursor = DB.connection().cursor()
		cursor.execute(sql)
		recs = cursor.fetchall()
		rets = []
		for r in recs:
			rets.append(r[0])
		cursor.close()
		return rets[0] if len(rets) > 0 else None

	@staticmethod
	def responseID(s):
		s = s.replace("'", "`")
		sql = "SELECT id FROM tb_response WHERE data = '{0}'".format(s)
		cursor = DB.connection().cursor()
		cursor.execute(sql)
		recs = cursor.fetchall()
		rets = []
		for r in recs:
			rets.append(r[0])
		cursor.close()
		return rets[0] if len(rets) > 0 else None

	@staticmethod
	def saveSubject(w):
		cursor = DB.connection().cursor()
		w = w.replace("'", "`")
		sql = """
INSERT INTO tb_subject('data')
SELECT '{0}'
WHERE NOT EXISTS(SELECT 1 FROM tb_subject WHERE data = '{0}')
		"""
		cursor.execute(sql.format(w))
		DB.conn.commit()
		gid = cursor.lastrowid
		cursor.close()
		return gid

	@staticmethod
	def saveResponse(sent):
		cursor = DB.connection().cursor()
		sent = sent.replace("'", "`")
		sql = """
INSERT INTO tb_response('data', 'date_time')
SELECT '{0}', julianday('now')
WHERE NOT EXISTS(SELECT 1 FROM tb_response WHERE data = '{0}')
		"""
		cursor.execute(sql.format(sent))
		DB.conn.commit()
		gid = cursor.lastrowid
		cursor.close()
		return gid

	@staticmethod
	def saveTrigger(sub, resp):
		wid = DB.subjectID(sub)
		sid = DB.responseID(resp)

		if wid is None: wid = DB.saveSubject(sub)
		if sid is None: sid = DB.saveResponse(resp)

		sql = "INSERT INTO tb_trigger('subject', 'response', 'date_time') VALUES({0}, {1}, julianday('now'))".format(wid, sid)
		cursor = DB.connection().cursor()
		cursor.execute(sql)
		DB.conn.commit()
		cursor.close()

	@staticmethod
	def saveTriggers(triggers):
		cursor = DB.connection().cursor()
		for word, sentence in triggers:
			wid = DB.subjectID(word)
			sid = DB.responseID(sentence)
			if wid is None: wid = DB.saveSubject(word)
			if sid is None: sid = DB.saveResponse(sentence)
			sql = "INSERT INTO tb_trigger('subject', 'response', 'date_time') VALUES({0}, {1}, julianday('now'))".format(wid, sid)
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
	def getResponse(data): 
		# BASIC = Use n-grams on the words table only
		# NORMAL = Use n-grams on sentences only
		# ADVANCED = Use n-grams on both word and sentence tables

		if len(data) == 0: return None

		sql = """
SELECT DISTINCT
	s.data AS response
FROM tb_trigger t
	INNER JOIN tb_subject w ON w.id == t.subject
	INNER JOIN tb_response s ON s.id == t.response
WHERE (
		"""

		ngtest = " OR ".join(list(map(lambda x: "(w.data LIKE '%{0}%')\n".format(x.replace("'", "`")), data)))
		sql += ngtest

		sql += "\n) ORDER BY RANDOM() LIMIT 1"

		cursor = DB.connection().cursor()
		cursor.execute(sql)
		recs = cursor.fetchall()
		rets = []
		for r in recs:
			rets.append(r[0])
		cursor.close()
		return list(map(lambda x: x.replace("`", "'"), rets))[0] if len(rets) > 0 else None
