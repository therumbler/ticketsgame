#!/usr/bin/python2.7
import urllib2
import json
import re
import socket
import time
from urllib import urlencode
from caching import Caching
from cookielib import CookieJar

class Songkick():
	def __init__(self, api_key):
		self.api_key = api_key
		self.base_url = "http://api.songkick.com/api/3.0/"
		self.caching = Caching()

	def get(self, end_point, **params):
		params["apikey"] = self.api_key
		qs = urlencode(params)
		url = self.base_url + end_point + "?" + qs
		response = self.caching.get(url)
		if response:
			return json.loads(response)
		return json.load(urllib2.urlopen(url))

	def get_artist_avatar_url(self, artist_id):
		url = "http://assets.sk-static.com/images/media/profile_images/artists/%s/card_avatar" % artist_id

		response = urllib2.urlopen(url)
		content_length = response.headers.get("Content-Length")
		if int(content_length) > 700:
			#we have something worthwhile
			return url
		else:
			#it's pretty much an empty image. There's no point using it
			return False

	def get_events_for_location(self, metro_area_id, pages = 1):
		"""
		convenience method to return only events, and optional multiple pages.
		"""
		events = []

		end_point = "metro_areas/%s/calendar.json" % metro_area_id
		response = self.get(end_point)
		events.extend(response["resultsPage"]["results"]["event"])

		total_entries = response["resultsPage"]["totalEntries"]
		per_page = response["resultsPage"]["perPage"]

		total_pages = abs(total_entries / per_page)
		
		if total_entries % per_page > 0:
			total_pages += 1
		
		if pages > total_pages:
			pages = total_pages

		for page in range(2, pages + 1):
			response = self.get(end_point, page = page)
			events.extend(response["resultsPage"]["results"]["event"])

		return events

	def get_ticket_url(self, event_id):
		url = "http://www.songkick.com/concerts/%s" % event_id
		
		html = self.caching.get(url)

		ticket_id = self.get_ticket_id(html)
		if not ticket_id:
			return False
		url = "http://www.songkick.com/tickets/%s" % ticket_id
		print "getting", url
		request = urllib2.Request(url)
		
		request.add_header("Accept-Language" ,"en-US,en;q=0.8")
		request.add_header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8")
		request.add_header("Connection", "keep-alive")
		#request.add_header("Host", "songkick.com")
		#request.add_header("Accept-Encoding", "gzip, deflate, sdch")
		request.add_header("Upgrade-Insecure-Requests", 1)
		request.add_header("User-Agent","Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36")
		request.add_header("Referer", "songkick.com")
		request.add_header("Cookie", "split_test_identifier=cf291ceada4c4626cffab7a88a03a695206861f1; source_of_visit=https%3A%2F%2Fwww.google.ca%2F; _skan__id_2=5b9f3d34dba09751.1479414813.1479414813.-; __utmx=88568345.$0:; __utmxx=88568345.$0:1479415406:8035200; _ga=GA1.2.156727821.1479407794; _gat=1; _skweb_session=TkZDTWthZnJmREhGc21YcHVURk5lNlJPUW4rZU9jSTAvc1QySDhHdWdSeTIzKzZsSDhzOUphVVpaYTRhczZoMzN6U0hJcFpXU2NxYmsrQ0ZibTVuS29GZkJkRlpTa3lWcmZmZWxUSHN6NXZzUWRLTHVqTks3bm4yNmkvQzNnemhNUnJISDljVEJFcTU3YkdkNVVTdkY0eG9IMDByZXBrYW0zQ00waE1IemFmdkVQSDBMd2VNa0xoVGE5bmpMeG50Vmw4UlhSa1R4Y3VPNHEzeHY3VGc1RHR3STNDV0pDZm5IeUR0bFh6R1RHdz0tLXg3RHFpVTBLMnVScVJrSDJCc1VKY3c9PQ%3D%3D--a0087787025c08154896d8823790c9db8093e611")
		#print json.dumps(request.headers, indent = 4)

		try:
			#response = urllib2.urlopen(request, timeout = 10)
			cj = CookieJar()
			opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
			#request = urllib2.Request(url)
			response = opener.open(request, timeout = 10)
			#response =	urllib2.build_opener(urllib2.HTTPCookieProcessor).open(request, timeout = 10)
		except urllib2.HTTPError, e:
			#if e.code == 301:
			
			print "HTTPError"
			return e.url
			#print e.code
			#print e.info()
			#print e.read()
			#raise
			
		except socket.timeout, e:
			#timeout. we're blocked?
			print "timeout for", url
			time.sleep(15)
			return False
		except urllib2.URLError, e:
			print "URLError", str(e)
			return False
			#print str(e)
			#raise
		return response.url

	def get_ticket_id(self, html):
		pattern = r'(?<=\/tickets\/)\d*'
		try:
			ticket_id = re.search(pattern, html).group(0)
		except AttributeError, e:
			#event is in the past?
			return False
		return ticket_id
		#print response.url

def main():
	api_key ="pLcYktIGaKMeD4RB"
	sk = Songkick(api_key)

	metro_areas = [
		("Toronto, ON",27396),
		("Atlanta", 4120), 
		("Austin", 9179), 
		("Chicago", 9426), 
		("Dallas", 35129), 
		("Denver", 6404), 
		("Houston", 15073), 
		("London, UK" , 24426), 
		("Los Angeles", 17835), 
		("Miami", 9776), 
		("Nashville",  11104), 
		("New York",7644), 
		("Philadelphia", 5202),
		("Portland", 12283),
		("San Francisco", 26330),
		("Seattle", 2846),
		("Washington DC", 1409)
	]

	#for area in metro_areas:
	#	print sk.get("search/locations.json", query = area[0])

	#events = sk.get("metro_areas/27396/calendar.json", page = 16)
	#events = sk.get_events_for_location(metro_area_id = 27396, pages = 30)
	#events = sk.get("events.json", location = "sk:27396", artist_name = "Bonobo")
	#events = sk.get_events_for_location(metro_area_id = 27396, pages = 3)

	#response = sk.get_ticket_url(26537844)
	response = sk.get("events/27022539.json")
	print json.dumps(response, indent = 4)

if __name__ == '__main__':
	main()