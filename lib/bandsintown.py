#!/usr/bin/python2.7
import urllib2
import json
import re
import time
from caching import Caching
from urllib import urlencode, quote
from ticketmaster import Ticketmaster
from ticketfly import Ticketfly
from ticketweb import Ticketweb
from axs import AXS

class Bandsintown():
	def __init__(self, app_id):
		self.base_url  = "http://api.bandsintown.com/"
		self.app_id = app_id
		#http://api.bandsintown.com/artists/Skrillex/events.json?api_version=2.0&app_id=YOUR_APP_ID
		self.caching = Caching()

	def get(self, endpoint, **params):
		if "app_id" not in params.keys():
			params["app_id"] = self.app_id
		if "format" not in params.keys():
			params["format"] = "json"
		if "date" not in params.keys():
			params["date"] = "upcoming"
		if "api_version" not in params.keys():
			params["api_version"] = "2.0"

		querystring = urlencode(params)

		url = self.base_url
		url += endpoint.replace("%2F", "%20") #replacing perc. encoded slashes with spaces
		url += "?%s" % (querystring)
		
		response_text = self.caching.get(url)
		if response_text:
			
			#if "error" in data.keys():
			#	raise urllib2.HTTPError(url, data["error"], data["response"], )
			return json.loads(response_text)
		else:
			try:
				response_text = urllib2.urlopen(url).read()
			except urllib2.HTTPError, e:
				print "Bandsintown HTTPError"
				response_text = e.read()			
				response = json.dumps({
					"error": e.code,
					"response": response_text
				})
			
			data = json.loads(response_text)
			self.caching.save_cache(url, data)
			time.sleep(4)
			return data

	def search_event(self, artist, location, date = "upcoming"):
		"""
		Convinience method which takes an artist name, a location (city) 
		and an optional date (yyyy-mm-dd) and returns a bunch of events.
		date 		:	yyyy-mm-dd
						or yyyy-mm-dd,yyyy-mm-dd (inclusive range)
		location	:	city,state (US or CA)
						city,country
						lat,lon
						ip address
						use_geoip (will use the ip the request came from)

		"""

		events = []
		artist = quote(artist, safe = '')
		endpoint = "artists/%s/events.json" % artist
	
		response = self.get(endpoint, location = quote(location), date = date)

		#check to see if the city name is in the list, if so, return that
		location_city = re.search(r'.*(?=,)', location).group(0)
		if type(response) == list:
			for event in response:
				if location_city.lower() in event["venue"]["city"].lower():
					ticket_url = event["ticket_url"]
					if ticket_url:
						#print ticket_url
						prices = self.get_ticket_details(ticket_url)
						if prices:
							event["ticket_details"] = prices
					events.append(event)
		else:
			try:
				if "error" in response.keys():
					print response
			except AttributeError, e:
				# not a dict. must be a list
				pass
		
		#none of the events matched the city, return them all
		if len(events) == 0:
			events = response
		return events

	def get_ticket_redirect_url(self, ticket_url):
		"""
		takes a ticket_url and finds the redirect url
		"""
		html = self.caching.get(ticket_url)	
		#find the redirect url in the Javascript

		try:
			pattern = r'(?<=\nwindow.location.replace\(\').*(?=\'\))'
			url = re.search(pattern, html).group(0)
		except AttributeError, e:
			#looks like it's an actual 302 redirect, but without a ticket link.
			return False

		return url



	def get_ticket_details(self, ticket_url):
		#print ticket_url
		if "bandsintown" in ticket_url:
			url = self.get_ticket_redirect_url(ticket_url)
			
		else:
			url = ticket_url
		
		if not url:
			return False
		
		if "ticketweb" in url:
			print "ticketweb"
			tw = Ticketweb() 
			ticket_status = tw.get_ticket_details_by_url(url)
			return ticket_status
		elif "ticketmaster.ca" in url.lower() or "ticketmaster.com" in url.lower() or "ticketmaster.co.uk" in url.lower():
			#i know how to deal with ticketmaster

			tm = Ticketmaster()
			prices = tm.get_ticket_details_by_url(url)
			return prices
		elif "ticketfly" in url:
			try:
				pattern = r'(?<=event/)\d*'
				event_id = re.search(pattern, url).group(0)

			except AttributeError, e:
				# pattern didn't match 
				return False
			tf = Ticketfly()
			prices = tf.get_ticket_details(event_id = event_id)
			return prices
		elif "axs.com" in url:
			axs = AXS()
			details = axs.get_ticket_details(url)
			return details
		else:
			print "i don't know what to do with url ", url
			return False

	def get_event_status(self, event):
		pass

def main():
	bit = Bandsintown("ticketgame") 
	results = bit.get("artists/mbid_c14149eb-877d-460d-9d84-459dd14a3206/events/")
	#results= bit.search_event(artist = "All Boy/All Girl ", location = "Philadelphia, PA", date ="2016-11-17")
	
	url = "http://www.bandsintown.com/event/11325390/buy_tickets?app_id=ticketgame&artist=Berliner+Philharmoniker&came_from=67"
	#url = "http://www.bandsintown.com/event/12317145/buy_tickets?app_id=ticketsgame&artist=Lemaitre&came_from=67"
	#url = "http://www.bandsintown.com/event/12930810/buy_tickets?app_id=ticketsgame&artist=Dragonette&came_from=67"
	#url = "http://www.bandsintown.com/event/13010372/buy_tickets?app_id=ticketsgame&artist=PARTYNEXTDOOR&came_from=67"
	#url = "http://www.bandsintown.com/event/13028420/buy_tickets?app_id=ticketsgame&artist=PARTYNEXTDOOR&came_from=67"
	url = "http://www.bandsintown.com/event/12295467/buy_tickets?app_id=ticketsgame&artist=GHOST&came_from=67"
	#url = "http://www.bandsintown.com/event/13194109/buy_tickets?app_id=ticketsgame&artist=Tim+McGraw&came_from=67"
	#url = "http://www.bandsintown.com/event/12071157/buy_tickets?app_id=ticketsgame&artist=Tambor&came_from=67"
	url = "http://www.bandsintown.com/event/13225834/buy_tickets?app_id=ticketsgame&artist=Seven+Lions&came_from=67"
	url = "http://www.bandsintown.com/event/11106616/buy_tickets?app_id=ticketgame&artist=Amy+Grant&came_from=67"
	url = "http://www.bandsintown.com/event/11413588/buy_tickets?app_id=ticketgame&artist=Zo%C3%AB+Keating&came_from=67"
	url = "http://ticketmaster.evyy.net/c/219208/264167/4272?u=http%3A%2F%2Fticketmaster.com%2Fevent%2F09004F63BAAE3007&subId1=67%7E13452420%7E22553396%7E%7E"
	url = "http://www.bandsintown.com/event/13276569/buy_tickets?app_id=ticketgame&artist=GZA%2FGenius&came_from=67"
	url = "http://www.axs.com/events/324412/robert-glasper-experiment-tickets?aff=usaffsongkick"

	url = "http://ticketmaster.evyy.net/c/219208/264167/4272?u=http%3A%2F%2Fticketmaster.com%2Fevent%2F09004F63BAAE3007&subId1=67%7E13452420%7E22553396%7E%7E"
	url = "http://www.bandsintown.com/event/11325390/buy_tickets?app_id=ticketsgame&artist=Berliner+Philharmoniker&came_from=67"
	results = bit.get_ticket_details(url)
	print json.dumps(results, indent = 4)

if __name__ == '__main__':
	main()
