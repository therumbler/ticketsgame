#!/usr/bin/python2.7
import md5
import os
import json
import time
from datetime import datetime
from lib.songkick import Songkick
from lib.bandsintown import Bandsintown
from lib.musicbrainz import Musicbrainz

class App():
	def __init__(self):
		#Songkick
		api_key ="pLcYktIGaKMeD4RB"
		self.songkick = Songkick(api_key)

		#Bandsintown
		self.bandsintown = Bandsintown(app_id = "ticketsgame")

		#Musicbrainz
		self.musicbrainz = Musicbrainz()

		#get toronto events from Songkick location = "sk:27396"
		#self.events = self.get_events(location = "sk:27396")
		#self.process_events()
		#self.get_event_ids()
		#self.get_event_by_id(88888)

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
		for area in metro_areas:
			self.load_events(area[1])

	def save_event(self, event):
		path = "etc/events/%s.json" % event["id"]
		with open(path, "w") as f:
			f.write(json.dumps(event, indent = 4))

		return True

	def load_events(self, metro_area_id = 27396):
		"""
		returns a list of events from Songkick
		"""
	
		events = self.songkick.get_events_for_location(metro_area_id = metro_area_id, pages = 16)
		
		for e in events:
			event_id = e["id"]
			#check to see if we already have this
			event = self.get_event_by_id(event_id)
			if not event:
				print "we have a new one"
				event = {
					"songkick_response": e,
					"id": e["id"]
				}
				self.save_event(event)
			else:
				# "we've saved this Songkick event before"
				pass
		return events

	def should_process(self, event_id):
		event = self.get_event_by_id(event_id)
		if "bandsintown_response" not in event.keys():
			return True
		if "musicbrainz_response" not in event.keys():
			return True

		return False

	def process_events(self):
		events = self.get_event_ids()
		total_events = len(events)

		processed = 0
		time_process_one = 10
		remaining_time = 1000
		for event_id in events:
			start = time.time()
			print event_id
			if int(event_id) >= 28490969:
				event = self.should_process(event_id)
				self.process_event(event_id)
				#time.sleep(1)

				end = time.time()
				time_process_one =  0.95 * time_process_one  + (0.05 * (end - start))
				remaining_time = (total_events - processed) * time_process_one
			processed += 1

			print "%s completed. %s remaining. est. time: %s minutes" % (processed, (total_events - processed), int(remaining_time / 60))

	def get_event_ids(self):
		"""
		loads the event_ids from etc/events directory
		"""
		event_ids = []
		path = "etc/events/"
		for root, dirs, files in os.walk(path):
			event_ids.extend(e.replace(".json", "") for e in files if e != ".DS_Store")
		return event_ids

	def get_event_by_id(self, event_id):
		"""
		loads event_id.json 
		"""
		path = "etc/events/%s.json" % event_id
		
		try:
			with open(path) as f:
				event = json.load(f)
			return event
		except IOError, e:
			#no file exists
			return False

	def get_bandsintown(self, event):
		if len(event["songkick_response"]["performance"]) == 0:
			return False

		venue = event["songkick_response"]["venue"]
		metro_area = venue["metroArea"]
		#print metro_area
		if "state" in metro_area.keys():
			location = "%s, %s" % (metro_area["displayName"], metro_area["state"]["displayName"])
		else:
			location = "%s, %s" % (metro_area["displayName"], metro_area["country"]["displayName"])
		#print location
		artist = event["songkick_response"]["performance"][0]["displayName"]
		#print artist.encode("utf-8")

		date = event["songkick_response"]["start"]["date"]
		identifier = event["songkick_response"]["performance"][0]["artist"]["identifier"]
		if len(identifier) == 0:
			response = self.bandsintown.search_event(artist = artist.encode("utf-8"), location = location, date = date)
		else:
			mbid = event["songkick_response"]["performance"][0]["artist"]["identifier"][0]["mbid"]
			#print "searching Bandsintown with mbid = %s" % mbid
			
			endpoint = "artists/mbid_%s" % mbid
			response = self.bandsintown.get(endpoint, location = location, date = date)

		return response

	def get_musicbrainz(self, event):
		mbid = False
		#print event["id"]
		if len(event["songkick_response"]["performance"]) == 0:
			return False
		#print event["songkick_response"]["performance"][0]["artist"]
		identifier = event["songkick_response"]["performance"][0]["artist"]["identifier"]
		if len(identifier) == 0:
			artist_name = event["songkick_response"]["performance"][0]["artist"]["displayName"]
			results = self.musicbrainz.search_artist(q = artist_name.encode("utf-8"))
		
			for r in results:
		
				if  r["name"].encode("utf-8").lower() == artist_name.lower():
					mbid = r["gid"]
					break
		else:
			mbid = event["songkick_response"]["performance"][0]["artist"]["identifier"][0]["mbid"]

		if mbid:
			endpoint = "artist/%s" % mbid
			#time.sleep(2)
			response = self.musicbrainz.get(endpoint, inc = "tags+url-rels")

			twitter = self.musicbrainz.get_twitter(response)
			if twitter:
				response["twitter"] = twitter 
			return response
		else:
			return False

	def process_event(self, event_id):
		"""
		"""
		modified = False
		event = self.get_event_by_id(event_id)
		
		if "musicbrainz_response" not in event.keys() or not event["musicbrainz_response"]:
			mb_response = self.get_musicbrainz(event)
			if mb_response:
				event["musicbrainz_response"] = mb_response
				modified = True
		else:
			#there's a valid Musicbrainz response
			#print "musicbrainz_response"
			#print event["musicbrainz_response"]
			if "twitter" not in event["musicbrainz_response"].keys():
				twitter = self.musicbrainz.get_twitter(event["musicbrainz_response"])
				if twitter:
					event["musicbrainz_response"]["twitter"] = twitter
					modified = True
		if "bandsintown_response" not in event.keys():
			bit = self.get_bandsintown(event)
			event["bandsintown_response"] = bit
			modified = True
		elif type(event["bandsintown_response"]) == dict and "error" in event["bandsintown_response"].keys():
			print "previous was error"
			bit = self.get_bandsintown(event)
			if type(bit) == dict and "error" in bit.keys():
				print "Bandsintown Error"
				print bit
				return False
			else:
				event["bandsintown_response"] = bit
				modified = True
		
		if modified:
			self.save_event(event)
		return event
		
	def check_ticket_prices(self):
		events = self.get_event_ids()
		for event_id in events:
			event = self.get_event_by_id(event_id)
			bit = event["bandsintown_response"]
			
			if type(bit) == list and len(bit) > 0:
				bit = bit[0]
				
			ticket_url = bit[0]["ticket_url"]
			if ticket_url and "ticket_details" not in bit[0].keys():
				#print event_id
				#print ticket_url

				prices = self.bandsintown.get_ticket_details(ticket_url)
				
				if prices:
					event["bandsintown_response"][0]["ticket_details"] = prices
					self.save_event(event)
				#response = urllib2
				#print bandsintown

def main():
	app = App()
	#app.check_ticket_prices()
	#app.process_events()
	#app.load_events()
	#response = app.process_event(27776769)

	#app.list_events()
	#response = app.get_event_by_id(27966369)
	#print json.dumps(response, indent = 4)

if __name__ == '__main__':
	main()
