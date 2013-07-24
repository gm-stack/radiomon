#!/usr/bin/env python
from flask import *
app = Flask(__name__)
application = app
import logging, sys
logging.basicConfig(stream=sys.stderr)
import MySQLdb, MySQLdb.cursors
import datetime
from collections import defaultdict
import ConfigParser
config = ConfigParser.ConfigParser()
config.read(app.root_path + "/radiomon.conf")

@app.before_request
def before_request():
	g.conn = conn = MySQLdb.connect(host=config.get("mysql","host"),
			user=config.get("mysql","user"),
			passwd=config.get("mysql","passwd"),
			db=config.get("mysql","db"), 
			cursorclass=MySQLdb.cursors.DictCursor, charset='utf8')
	g.cursor = g.conn.cursor()

def time_to_minutes(time):
	hours = time[0:2]
	minutes = time[2:4]
	return (int(hours)*60)+int(minutes)

def gengraph(date,day):
	MINUTES_PER_DAY=60*24 # 1440, 1 minute per pixel. Each slice of recording should therefore be 5 pixels wide... but that's not going to happen
	content = ""
	if len(day) == 0:
		return """<td class="space" width="1440">"""
	# initial space
	first = time_to_minutes(day[0])
	content += """<td class="space" width="%i">&nbsp;</td>""" % first
	#items
	for i in range(len(day)-1):
		now = time_to_minutes(day[i])
		next = time_to_minutes(day[i+1])
		content += """<td class="signal" id="%s"></td>""" % (date+"-"+day[i])
		width = ((next-now)-5)
		if (width > 0):
			content += """<td width="%i" class="space"></td>""" % width
	# now handle the last
	last = time_to_minutes(day[-1])
	content += """<td class="signal" id="%s"></td>""" % (date+"-"+day[-1])
	content += """<td class="space" width="%i">&nbsp;</td>""" % (MINUTES_PER_DAY-(last+5))
	return content


def render_day_view(day):
	g.cursor.execute("select SUBSTRING(datetime,9,4) as time from transmissioninfo where SUBSTRING(datetime,1,8) = %(date)s order by time asc", {'date': day})
	res = g.cursor.fetchall()
	txlist = map(lambda x: x['time'] , res)
	txs = defaultdict(list)
	for trans in txlist:
		hour = int(trans[:2])
		txs[hour].append(trans)
	return render_template("day_view.html", day=day, datetime=datetime, gengraph=gengraph, txs=txs, txlist=txlist)

@app.route('/')
def index():
	g.cursor.execute("select distinct SUBSTRING(datetime,1,8) as date from transmissioninfo order by date asc")
	res = g.cursor.fetchall()
	recdays = map(lambda x: x['date'] , res)
	return render_template("index.html", recdays=recdays, render_day_view=render_day_view)

def realtime_to_seconds(realtime):
	realtime = realtime.split(":")
	return (int(realtime[0])*3600) + (int(realtime[1])*60) + int(realtime[2])

def seconds_to_realtime(seconds):
	hours = int(seconds/3600)
	minutes = int((seconds - (hours*3600))/60)
	secs = int(seconds) % 60
	return "%.2i:%.2i:%.2i" % (hours,minutes,secs)

def gen_timeline_bar(date,time):
	content = """<img src="static/redbar.png" id="redline"/><table class="graph" width="1440"><tr>"""
	results = g.cursor.execute("SELECT txinfo FROM transmissioninfo WHERE datetime = %(datetime)s", {'datetime': date+time})
	if results == 0:
		return "not found in db"
	results = g.cursor.fetchone()['txinfo']
	data = results.split("\n")
	if "" in data: data.remove("")
	data2 = []
	for chunk in data: # start,end,length,realtime at *end* of recording
		chunk = chunk.split(",")
		data2.append(chunk)
	start_time = realtime_to_seconds(data2[0][3]) - int(float(data2[0][2])) #int("2.4") gives us an error, but int(2.4) simply rounds down.
	end_time = realtime_to_seconds(data2[-1][3]) 
	length = end_time - start_time
	pixels_per_second = 1440.0/float(length);
	lengths = []
	lengths_total = 0.0
	starts = []
	starts_total = 23.0
	# A new file is created if the start of this recording is more than 5 minutes after the start of the previous recording, not 5 minutes total duration.
	# so with a 30 second long recording right at 4:59, the file is longer
	for i in range(len(data2)):
		thisrec = data2[i]
		thislength = float(thisrec[2])
		lengths_total += thislength
		lengths.append(lengths_total)
		pixelswide = int(pixels_per_second * float(thisrec[2]))
		starts.append(starts_total)
		starts_total += pixelswide
		content += """<td class="playersignal" id="signal_%i" width="%i"></td>""" % (i,pixelswide)
		if not i == len(data2)-1:
			nextrec = data2[i+1]
			this_rt_end = realtime_to_seconds(thisrec[3])
			next_rt_start = realtime_to_seconds(nextrec[3]) - float(nextrec[2])
			gaplen = float(next_rt_start - this_rt_end) * pixels_per_second
			#print "this ends at %i, next starts at %i, gaplen %i" % (this_rt_end, next_rt_start, gaplen)
			content += """<td width="%i" class="space"></td>""" % (gaplen)
			starts_total += gaplen
			# realtime end of this one to realtime start of next one
	content += """</tr></table>
	<table class="graph" width="1440"><tr><td class="start_time">%s</td><td class="end_time">%s</td></tr></table>""" % (seconds_to_realtime(start_time), seconds_to_realtime(end_time))
	return {"timebar": content, "pps": pixels_per_second, "lengths": lengths, "starts": starts}

@app.route("/timeline/<time>")
def timeline(time):
	query = time.split("-")
	return json.dumps(gen_timeline_bar(query[0],query[1]))

@app.route('/details/<time>', methods=['GET', 'POST'])
def details(time):
	if request.method == "GET":
		results = g.cursor.execute("SELECT comments,lastedit FROM transmissioninfo WHERE datetime = %(datetime)s", {'datetime': time})
		if results == 0: return {'comment': "Not found in database"}
		res = g.cursor.fetchone()
		return json.dumps({'comment': res['comments'], 'user': res['lastedit']})
	elif request.method == "POST":
		results = g.cursor.execute("UPDATE transmissioninfo SET comments = %(comments)s , lastedit = %(lastedit)s WHERE datetime = %(datetime)s LIMIT 1", 
								{'datetime': request.form['datetime'], 'comments': request.form["tac"], 'lastedit': 'test'})
		return json.dumps({'message': "Update successful"})
