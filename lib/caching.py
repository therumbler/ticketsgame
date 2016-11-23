#!/usr/bin/python2.7
import os
import md5
import urllib2
import json
import time
from datetime import datetime

class Caching():
	"""
	a very basic caching class. 
	Only work with GET requests, not POST
	also only works with JSON responses
	"""

	def __init__(self):
		self.date = self.get_date()

	def get(self, url):
		response_text = self.check_cache(url)
		if not response_text:
			try:
				response = urllib2.urlopen(url)
				response_text = response.read()
				response_code = response.getcode()
			except urllib2.HTTPError, e:
				response_code = e.code
				response_text = e.read()
				if (response_code == 400 and "Rate limit exceeded" in response_text)\
					or (response_code >= 500 and "musicbrainz.org" in url):
					#likely a bandsintown rate limit
					print "HTTPError %s %s" % (response_code, url)
					print "Waiting, and will try again"
					time.sleep(15)
					return self.get(url)	
			except urllib2.URLError, e:
				response_text = "URLError: %s" % str(e)
				response_code = 500
			except socket.timeout, e:
				#timeout. we're blocked?
				print "timeout for", url
				time.sleep(30)
				return self.get(url)
			self.save_cache(url, response_text, response_code)

		return response_text

	def get_path(self):	
		if "/lib" in os.getcwd():
			path = "../etc/appcache/%s/" % self.get_date()
		else:
			path = "etc/appcache/%s/" % self.get_date()
		return path

	def get_date(self):
		return datetime.now().strftime("%Y%m%d")

	def get_md5_hash(self, url):
		m = md5.new()
		m.update(url)
		md5_hash = m.hexdigest()
		return md5_hash

	def check_cache(self, url):
		path = self.get_path()
		if not os.path.isdir(path):
			os.mkdir(path)

		#add the filename to the path
		md5_hash = self.get_md5_hash(url)
		path += "%s.json" % md5_hash		

		if os.path.isfile(path):			
			with open(path) as f:
				data = json.load(f)

			if type(data) == list:
				response_text= json.dumps(data)
			elif "response_text" in data.keys():
				if type(data["response_text"]) == list:
					response_text = json.dumps(data["response_text"])
				else:
					response_text = data["response_text"]
			else:
				response_text = json.dumps(data)

			if type(data) == dict and "error" in data.keys():
				if data["error"] == 400:
					#most likely a rate limit error
					#lets make the request again
					return False
				elif data["error"] == 503:
					#Most likely a musicbrainz error
					return False
				else:
					return response_text
			else:
				return response_text			

		return False

	def save_cache(self, url, response_text, response_code = 200):
		path = self.get_path()

		if not os.path.isdir(path):
			os.mkdir(path)
		#add the filename to the path
		md5_hash = self.get_md5_hash(url)
		path += "%s.json" % md5_hash

		data = {
			"url": url,
			"response_text": response_text,
			"response_code": response_code
		}
		with open(path, "w") as f:
			f.write(json.dumps(data, indent = 4))
		return True

def main():
	"testytestytest"
	caching = Caching()
	url = "https://musicbrainz.org/ws/js/artist?q=Keegan+Mcinroe"
	url = "https://musicbrainz.org/ws/js/artist?q=Jamie+Jams&fmt=json"
	url = "https://musicbrainz.org/ws/js/artist?q=The+Clone+Roses&fmt=json"
	url = "https://musicbrainz.org/ws/js/artist?q=The+Third+Kind+NYC&fmt=json"
	print caching.get(url)#.encode("utf-8")

if __name__ == '__main__':
	main()
