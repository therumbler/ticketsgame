#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

import urllib2, urllib
import json
import xml.etree.ElementTree as ET
from caching import Caching

#import zlib, gzip
#from StringIO import StringIO

class Musicbrainz(object):
	"""Looks up an artist to pull in their links 
	on various sites on the internet (mysapce, twitter etc.)
	"""	
	
	def __init__(self, **args):	
		self.base_url =  "https://musicbrainz.org/ws/2/"
		self.urls = False
		self.name = False
		self.mbid = False
		uri = ""
		self.caching = Caching()
		if "artist" in args.keys():
			self.setup_from_artist_id(args["artist"])

		if "search" in args.keys():
			self.search_artist(q = args["search"].encode("utf-8"))

	def get(self, endpoint, **params):
		if "fmt" not in params.keys():
			params["fmt"] = "json"

		querystring = urllib.urlencode(params)

		url = "%s%s?%s" % (self.base_url, endpoint, querystring)
		#print url
		response_text = self.caching.get(url)
		if response_text:
			return json.loads(response_text)
		response = urllib2.urlopen(url)

		return json.load(response) 

	def search_artist(self, **args):
		"""
		Documentation
		https://musicbrainz.org/doc/Development/ws/js
		"""
		if "fmt" not in args:
			args["fmt"] = "json"
		q = urllib.urlencode(args)
		
		uri = "https://musicbrainz.org/ws/js/artist?{0}".format(q)
		print uri
		cached = self.caching.get(uri)
		if cached:
			results =  json.loads(cached)

			if len(results) > 0:
				del results[-1]
			return results

		request = urllib2.Request(uri)
		#request.add_header("Accept-encoding","gzip,deflate")
		request.add_header("Accept","text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8")
		try:
			response = urllib2.urlopen(request)
		except urllib2.HTTPError, e:
			error_string = e.read()
			error_code = e.code
			response = {
				"error": error_code,
				"description": error_string
			}
			print "Musicbrainz HTTPError"
			print response
			return response

		if response.headers.get("Content-Encoding","") == "deflate":
			json_str = zlib.decompressobj(-zlib.MAX_WBITS).decompress(response.read())
		elif response.headers.get("Content-Encoding","") == "gzip":			
			buf = StringIO( response.read())
			f = gzip.GzipFile(fileobj=buf)
			json_str = f.read()
		else:
			json_str = response.read()
		
		#print json_str
		results = json.loads(json_str)
		#remove last item as it's just meta data
		
		del results[-1]
		self.caching.save_cache(uri, results)
		return results
		
		for result in results:
			if result["name"].encode("utf-8").lower() == args["q"].lower():
				self.name = result["name"]
				self.setup_from_artist_id(result["gid"])

		#return json.loads(json_str)

	def setup_from_artist_id(self, mbid):
		uri = "https://musicbrainz.org/ws/2/artist/" + mbid + "?inc=url-rels"
		try:
			request = urllib2.Request(uri)
			response = urllib2.urlopen(request)
			xml = response.read()
			root = ET.fromstring(xml)
		
			self.name = root[0][0].text
			self.type = "artist"
			self.mbid = mbid
			self.urls = {}

			for child in root[0]:
				if "target-type" in child.attrib.keys():
					if child.attrib["target-type"] == "url":
						for url in child:
							key = "twitter" if "twitter.com" in url[0].text else url.attrib["type"]
							#only grab first link for each key
							if key not in self.urls.keys():
								self.urls[key] = url[0].text
		except:
			"musicbrainz error for id", mbid

	def get_twitter(self, data):
		"""
		from an /artist/mbid response, get the twitter handle
		"""

		twitter = False
		for rel in data["relations"]:
			url = rel["url"]["resource"]
			#print type(url)
			if u"twitter" in url.lower():
				twitter = url.replace("https://", "")
				twitter = twitter.replace("http://", "")
				twitter = twitter.replace("www.", "")
				twitter = twitter.replace("twitter.com/", "")
				break

		return twitter

def main():
	#mb = Musicbrainz(artist = "f8fb9acf-9e00-4c37-acce-1fd06abd8c0a")
	print "Content-Type: text/plain;charset=utf-8"
	print ""

	mb = Musicbrainz()

	response = mb.get("artist/bf823474-e438-4917-8976-23891b2b7523", inc = "tags+url-rels")
	#print json.dumps(response, indent = 4)
	#print mb.get_twitter()
	#print mb.name
	#print mb.mbid
	#response = mb.search_artist(q = "All Boy/All Girl")

	#print mb.get_twitter(response)	
	print json.dumps(response, indent = 4)
	#for child in root[0][4]: #url links
		#print "twitter" if "twitter.com" in child[0].text else child.attrib["type"], child[0].text


if __name__ == '__main__':
	main()