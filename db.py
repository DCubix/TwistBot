import sqlite3

class DB:
	conn = None

	@staticmethod
	def connection():
		if DB.conn is None:
			DB.conn = sqlite3.connect('data.db')
			cursor = DB.conn.cursor()

			sql = 'CREATE TABLE IF NOT EXISTS tb_subject(id integer primary key, trigger text, response text)'
			cursor.execute(sql)
			sql = 'CREATE TABLE IF NOT EXISTS tb_exclude(id integer primary key, word text)'
			cursor.execute(sql)

			DB.conn.commit()
			cursor.close()
		return DB.conn

	@staticmethod
	def close():
		DB.conn.close()

	def getExcludes():
		sql = "SELECT word FROM tb_exclude"
		cursor = DB.conn.cursor()
		cursor.execute(sql)
		recs = cursor.fetchall()
		rets = []
		for r in recs:
			rets.append(r[0])
		cursor.close()
		return rets

class SubjectDAO:
	@staticmethod
	def put(trigger, response):
		response = response.replace("'", "`")
		sql = "INSERT INTO tb_subject('trigger', 'response') VALUES('{0}', '{1}')".format(trigger, response)
		cursor = DB.conn.cursor()
		cursor.execute(sql)
		DB.conn.commit()
		cursor.close()

	@staticmethod
	def fetch(trigger):
		sql = "SELECT response FROM tb_subject WHERE trigger LIKE '{0}'".format('%'+trigger+'%')
		cursor = DB.conn.cursor()
		cursor.execute(sql)
		recs = cursor.fetchall()
		rets = []
		for r in recs:
			rets.append(r[0])
		cursor.close()
		return rets