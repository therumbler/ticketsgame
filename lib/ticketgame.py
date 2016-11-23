#!/usr/bin/python2.7
import json
import os
import time
import platform
from bandsintown import Bandsintown
from musicbrainz import Musicbrainz
from songkick import Songkick

##debug
import cgitb
cgitb.enable()

class Ticketgame():
    """
    ties it all together
    """
    def __init__(self):
        api_key ="pLcYktIGaKMeD4RB"
        self.songkick = Songkick(api_key)

        self.bandsintown = Bandsintown("ticketgame")
        #something
        self.musicbrainz = Musicbrainz()
        
    def get_creation_date(self, path_to_file):
        """
        Try to get the date that a file was created, falling back to when it was
        last modified if that isn't possible.
        See http://stackoverflow.com/a/39501288/1709587 for explanation.
        """
        if platform.system() == 'Windows':
            return os.path.getctime(path_to_file)
        else:
            stat = os.stat(path_to_file)
            try:
                return stat.st_birthtime
            except AttributeError:
                # We're probably on Linux. No easy way to get creation dates here,
                # so we'll settle for when its content was last modified.
                return stat.st_mtime

    def get_path(self):
        path = "etc/events/"
        if "/lib" in os.getcwd():
            path = "../%s" % path

        return path

    def load_events(self):
        response = self.get_metro_areas()

        metro_areas = response["metro_areas"]
        for area in metro_areas:
            self.load_songkick_events(metro_area_id = area["metro_area_id"])

    def load_songkick_events(self, metro_area_id = 27396):
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
                self.process_event(event["id"])
            else:
                # "we've saved this Songkick event before"
                pass
        return events

    def get_metro_areas(self):
        """
        loads a list of metro areas from a json config file
        the data includes the songkick id for each area
        """
        path = self.get_path()
        path = path.replace("events/", "config/")
        path = "%smetro_areas.json" % (path)
        metro_areas= {}
        with open(path) as f:
            metro_areas = json.load(f)

        return metro_areas

    def save_event(self, event):
        path = self.get_path()
        path += "%s.json" % event["id"]
        with open(path, "w") as f:
            f.write(json.dumps(event, indent = 4))

        return True

    def get_event_by_id(self, event_id):
        """
        loads event_id.json 
        """
        path = "%s%s.json" % (self.get_path(), event_id)
        
        try:
            with open(path) as f:
                event = json.load(f)
            created_time = self.get_creation_date(path)
            modified_time = os.path.getmtime(path)
            event["created_time"] = created_time
            event["modified_time"] = modified_time
            event["created_minutes"] = int((time.time() - created_time) / 60)
            event["modified_minutes"] = int((time.time() - modified_time) / 60)
            return event
        except IOError, e:
            #no file exists
            return False

    def get_event_ids(self):
        """
        loads the event_ids from etc/events directory
        """
        event_ids = []
        path = self.get_path()
        for root, dirs, files in os.walk(path):
            event_ids.extend(e.replace(".json", "") for e in files if e != ".DS_Store")

        return event_ids

    def event_to_csv(self, event):
        #print event
        title = '"%s"' % event["songkick_response"]["displayName"]
        popularity = event["songkick_response"]["popularity"]
        ticket_status = ''
        ticket_type = ''
        price_min = ''
        price_max = ''
        metro_area = '"%s"' % event["songkick_response"]["venue"]["metroArea"]["displayName"]
        tags = '""'
        date =  '"%s"' % event["songkick_response"]["start"]["date"]
        if "ticket_details" in event.keys():
            if event["ticket_details"]:
                if "status" in event["ticket_details"].keys():
                    ticket_status = '"%s"' % event['ticket_details']["status"]
                if "price_min" in event["ticket_details"].keys():
                    price_min = event["ticket_details"]["price_min"]
                    price_max = event["ticket_details"]["price_max"]
        """
        if "bandsintown_response" in event.keys():
            bit = event["bandsintown_response"]
            #print bit
            if bit and len(bit) > 0:
                if type(bit) == list:
                    bit = bit[0]
                
                ticket_status = '"%s"' % str(bit.get("ticket_status"))
                ticket_type = '"%s"' % str(bit.get("ticket_type"))
                if "ticket_details" in bit.keys():
                    price_min = bit["ticket_details"]["price_min"]
                    price_max = bit["ticket_details"]["price_max"]
        """
        if "musicbrainz_response" in event.keys() and event["musicbrainz_response"]:
            mb = event["musicbrainz_response"]
            tags = '"%s"' % ",".join([t["name"]for t in mb["tags"]])
                
        columns = [
            str(event["id"]),
            date,
            title,
            str(popularity),
            ticket_type,
            ticket_status,
            str(price_min),
            str(price_max),
            metro_area,
            tags
        ]

        return ",".join(columns).encode("utf-8").replace(",\"None\"", ",")

    def create_csv(self):
        count = 0

        path = self.get_path()
        path = path.replace("/events", "")
        print path
        filename = path + "ticketsgame.csv"
        header = [
            "id",
            "date",
            "title",
            "popularity",
            "ticket_type",
            "ticket_status",
            "price_min",
            "price_max",
            "area",
            "tags"
        ]
        with open(filename, "w") as f:
            f.write(",".join(header))
            f.write("\n")
            for event_id in self.get_event_ids():
            #for event_id in [27259909]:
                event = self.get_event_by_id(event_id)
                line = self.event_to_csv(event)
                f.write(line)
                f.write("\n")
                count += 1
                #if count > 800:
                #    break
        print "done"

    def check_ticketweb(self):
        event_ids  = self.get_event_ids()
        for event_id in event_ids:
            event = self.get_event_by_id(event_id)
            if "bandsintown_response" in event.keys():
                bit = event["bandsintown_response"]
                if bit and len(bit) > 0:
                    if type(bit) == list:
                        bit = bit[0]

                    if "ticket_url" in bit.keys():
                        url = bit["ticket_url"]
                        if url:
                            #print url
                            redirected_url = self.bandsintown.get_ticket_redirect_url(url)
                            
                            if redirected_url and "ticketweb" in redirected_url:
                                print redirected_url

    def get_bandsintown(self, event):
        if len(event["songkick_response"]["performance"]) == 0:
            print "nope"
            return False

        venue = event["songkick_response"]["venue"]
        metro_area = venue["metroArea"]
        #print metro_area
        location = "%s,%s" % (venue["lat"], venue["lng"])
        
        if "state" in metro_area.keys():
            location = "%s, %s" % (metro_area["displayName"], metro_area["state"]["displayName"])
        else:
            location = "%s, %s" % (metro_area["displayName"], metro_area["country"]["displayName"])
        
        print location
        artist = event["songkick_response"]["performance"][0]["displayName"]
        #print artist.encode("utf-8")

        date = event["songkick_response"]["start"]["date"]
        identifier = event["songkick_response"]["performance"][0]["artist"]["identifier"]
        if len(identifier) == 0:
            print "zero"
            response = self.bandsintown.search_event(artist = artist.encode("utf-8"), location = location, date = date)
        else:
            mbid = event["songkick_response"]["performance"][0]["artist"]["identifier"][0]["mbid"]
            print "searching Bandsintown with mbid = %s" % mbid
            
            endpoint = "artists/mbid_%s/events/search.json" % mbid
            response = self.bandsintown.get(endpoint, location = location, date = date)
            print response ,location, date
        if type(response) == list:
            if len(response)> 0:
                response = response[0]
            else:
                response = False
        return response

    def get_musicbrainz(self, event):
        mbid = False
        #print event["id"]
        if len(event["songkick_response"]["performance"]) == 0:
            return False
        #print event["songkick_response"]["performance"][0]["artist"]
        identifier = event["songkick_response"]["performance"][0]["artist"]["identifier"]
        if len(identifier) == 0:
            print "no identifier"
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
            print endpoint
            response = self.musicbrainz.get(endpoint, inc = "tags+url-rels")

            twitter = self.musicbrainz.get_twitter(response)
            if twitter:
                response["twitter"] = twitter 
            return response
        else:
            return False

    def process_event(self, event_id):
        event = self.get_event_by_id(event_id)

        if event["modified_minutes"] < 120:
            return False

        print "processing", event_id
        if "ticket_details" in event.keys():
            if not event["ticket_details"]:
                return False
            if "status" in event["ticket_details"].keys():
                if event["ticket_details"]["status"] == "Sold Out":
                    return False
                if event["ticket_details"]["status"] == "Available":
                    try:
                        url = event["ticket_details"]["ticket_redirect_url"]
                    except:
                        return False
                    if not url:
                        if type(event["bandsintown_response"]) == list and len(event["bandsintown_response"]) > 0:
                            bit = event["bandsintown_response"][0]
                        elif type(event["bandsintown_response"]) == dict:
                            bit = event["bandsintown_response"]
                        else:
                            #bandsintown must be an empty list
                            return False
                        try:
                            url = bit["ticket_redirect_url"]
                        except KeyError, e:
                            url = bit["ticket_url"]
                            url = self.bandsintown.get_ticket_redirect_url(url)

                        event["ticket_details"]["ticket_redirect_url"] = url
                        print "Saving"
                        self.save_event(event)
                        
                    if url:
                        print "processing", event_id
                        print url
                        ticket_details = self.bandsintown.get_ticket_details(url)
                        if ticket_details:
                            event["ticket_details"] = ticket_details
                            self.save_event(event)
                        return event

        if "ticket_details" not in event.keys():
            print "getting songkick ticket_url"
            ticket_redirect_url = self.songkick.get_ticket_url(event_id)

            event["ticket_details"] = {
                "ticket_redirect_url": ticket_redirect_url
            }
            self.save_event(event)

        if "ticket_details" in event.keys():
            if event["ticket_details"] and "ticket_redirect_url" in event["ticket_details"].keys():
                url = event["ticket_details"]["ticket_redirect_url"]
                
                if url:
                    ticket_details = self.bandsintown.get_ticket_details(url)

                    if ticket_details:
                        print ticket_details
                        ticket_details["ticket_redirect_url"] = url
                    else:
                        ticket_details = {"ticket_redirect_url":url}

                    event["ticket_details"] = ticket_details
                    self.save_event(event)

        if "musicbrainz_response" not in event.keys():
            print "musicbrainz"
            mb = self.get_musicbrainz(event)
            if mb:
                has_processed = True
                time.sleep(1)
                event["musicbrainz_response"] = mb
                self.save_event(event)

        if "bandsintown_response" not in event.keys():
            has_processed = True
            response = self.get_bandsintown(event)
            print response
            if response:
                event["bandsintown_response"] = response
                self.save_event(event)

        if "bandsintown_response" in event.keys():
            if type(event["bandsintown_response"]) == list and len(event["bandsintown_response"]) > 0:
                bit = event["bandsintown_response"][0]
            else:
                bit = event["bandsintown_response"]

            #check for Rate limit exceeded errors
            if type(bit) == dict and ("errors" in bit.keys() or "error" in bit.keys()):
                error_key = "errors" if "errors" in bit.keys() else "error"
                
                if type(bit[error_key]) != int and "Rate limit exceeded" in bit[error_key]:
                    del event["bandsintown_response"]
        
            if type(bit) == dict and "upcoming_event_count" in bit.keys():
                del event["bandsintown_response"]
        

        if "bandsintown_response" in event.keys():
            bit = event["bandsintown_response"]
            if bit and len(bit) > 0:
                if type(bit) == list:
                    bit = bit[0]

                if "ticket_url" in bit.keys():
                    url = bit["ticket_url"]
                    print url
                    if url:
                        print 'getting bandsintown'
                        ticket_url = self.bandsintown.get_ticket_redirect_url(url)
                        if not ticket_url:
                            return event
                        bit["ticket_redirect_url"] = ticket_url
                        event["bandsintown_response"] = bit
                
                        ticket_details = self.bandsintown.get_ticket_details(url)
                        if ticket_details:
                            ticket_details["ticket_redirect_url"] = ticket_url
                        else:
                            ticket_details = {"ticket_redirect_url":ticket_url}

                        event["ticket_details"] = ticket_details
                        self.save_event(event)
        return event

    def process_events(self, start_id = 0, reverse = False):
        event_ids = self.get_event_ids()
        print len(event_ids)
        event_ids = [int(e) for e in event_ids if int(e) >= start_id]
        print len(event_ids)
        
        if reverse:
            event_ids.sort(reverse = reverse)
        total = len(event_ids)
        processed = 0
        time_process_one = 1.43
        remaining_time = 1000

        for event_id in event_ids:
            has_processed = False
            processed += 1

            event = self.get_event_by_id(event_id)
            response = False
           
            start = time.time()
            response = self.process_event(event_id)
            
            if response:

                has_processed = True
                end = time.time()

                time_process_one =  0.99 * time_process_one  + (0.01 * (end - start))
                
                remaining_time = (total - processed) * time_process_one

                if has_processed:
                    print "processed", event_id
                    print "%s completed. %s remaining time: %s minutes" % (processed, (total - processed), int(remaining_time / 60))

    def get_count(self):
        event_ids = self.get_event_ids()

        count = {
            "has_ticket_url": 0,
            "ticketweb": 0,
            "ticketfly": 0,
            "ticketmaster": 0,
            "axs": 0,
            "other": 0,
            "has_bandsintown": 0,
            "total": len(event_ids)
        }

        for event_id in event_ids:
            event = self.get_event_by_id(event_id)

            if "bandsintown_response" in event.keys():
                bit = event["bandsintown_response"]
                if type(bit) == list and len(bit) > 0:
                    bit = bit[0]

                if bit:
                    if "facebook_page_url" not in bit.keys():
                        if "error" not in bit.keys() and "errors" not in bit.keys():
                            count["has_bandsintown"] += 1
                
                if "ticket_details" in event.keys():
                    td = event["ticket_details"]
                    if td and "ticket_redirect_url" in td.keys() and td["ticket_redirect_url"]:
                        ticket_redirect_url = td["ticket_redirect_url"]
                        count["has_ticket_url"] += 1

                        if "ticketweb" in ticket_redirect_url:
                            count["ticketweb"] += 1
                        elif "ticketfly" in ticket_redirect_url:
                            count["ticketfly"] += 1
                        elif "ticketmaster.com" in ticket_redirect_url or "ticketmaster.ca" in ticket_redirect_url:
                            count["ticketmaster"] += 1
                        elif "axs.com" in ticket_redirect_url:
                            count["axs"] += 1
                        else:
                            count["other"] += 1

        return count

def main():
    print "Content-Type: text/plain\n"
    print ""
    t = Ticketgame()
    t.load_events()

    #last_event_id = 27537464
    #t.process_event(28351549)
    t.process_events()
    t.create_csv()
    
    
    #response = t.get_event_by_id(27686144)
    #response = t.get_count()
    #print json.dumps(response, indent = 4)

if __name__ == '__main__':
    main()
