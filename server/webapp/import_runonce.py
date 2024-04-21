import sqlite3
import io

db = sqlite3.connect('data.db')
mm = io.open('team-badge-mapping.txt', mode="r", encoding="utf-8").read().strip().splitlines()
for teamname, categ, bt in map(lambda x: x.split("	"), mm):
	print(teamname)

	btnum = int(bt.split("BT")[1])
	if btnum > 36:
		continue

	vis = 1
	cur = db.execute("INSERT INTO scores (teamnum, teamname, highscore, visibility) VALUES (?, ?, ?, ?)", (bt, teamname, 0, vis))
	db.commit()
	cur.close()