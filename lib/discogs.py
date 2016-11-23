#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

import urllib2, urllib
import json

USER_AGENT = "Radio1 Comments/0.1a +http://irumble.com/radio1comments"

class Discogs(object):
	"""easy API for Discogs"""
	def __init__(self, **arg):
		self.twitter = False

		if "artist" in arg.keys():
			self.get_artist(arg["artist"])
		if "search_artist" in arg.keys():
			self.search_artist(q = arg["search_artist"].encode("utf-8"))
	def setup_artist(self, id):
		"""
		sets up based on an artist id
		"""

		url = "http://api.discogs.com/artists/" + id
		try:
			request = urllib2.Request(url)
			request.add_header("User-Agent", USER_AGENT)
			#request.add_header("Accept-encoding","gzip,deflate")
			#request.add_header("Accept","text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8")
			
			response = urllib2.urlopen(request)
			data = json.loads(response.read())
			self.artist = data["name"]
			
			if "urls" in data.keys():
				for url in data["urls"]:
					if "twitter" in url:
						self.twitter_url = url
						self.twitter = "@" + self.twitter_url.replace("https://","").replace("http://","").replace("www.","").replace("twitter.com/","").replace("/","")
		except:
			self.twitter = False
			self.twitter_url = False
			print "discogs setup_artist error"
	def search_artist(self, **args):
		q = urllib.urlencode(args)
		url = "http://api.discogs.com/database/search?%s&type=artist" % (q)		
		
		request = urllib2.Request(url)
		request.add_header("User-Agent", USER_AGENT)
		response = urllib2.urlopen(request)
		data = json.loads(response.read())

		for result in data["results"]:
			if result["title"].encode("utf-8").lower() == args["q"].lower():
				self.artist = result["title"]
				
				self.setup_artist(id = str(result["id"]))				
				
	def get_twitter(self):
		return self.twitter	

if __name__ == '__main__':
	d = Discogs(search_artist = "Johnny \"Hammond\" Smith")
	print d.get_twitter()