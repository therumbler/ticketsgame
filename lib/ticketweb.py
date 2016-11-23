#!/usr/bin/python2.7
import urllib2
import re
import json
from caching import Caching

class Ticketweb():
    def __init__(self):
        self.caching = Caching()

    def get_event(self, event_id):
        url = "http://www.ticketweb.ca/t3/sale/SaleEventDetail?dispatch=loadSelectionData&eventId=%s" % event_id
        #url = "http://www.ticketweb.ca/t3/sale/SaleEventDetail?dispatch=loadSelectionData&eventId=%s" % event_id
        response = self.caching.check_cache(url)
        if response:
            if type(response) == str or type(response) == unicode:
                response = json.loads(response)
            return response
        try:
            response = urllib2.urlopen(url, timeout = 15)
        except urllib2.URLError, e:
            # a timeout
            return False
        html = response.read()
        event = self.get_linked_data(html)
        self.caching.save_cache(url, event, response.getcode())
        return event
        
    def get_linked_data(self, html):
        pattern = r'(?<=<script type="application/ld\+json">).*(?=</script>)'
        try:
            response = re.search(pattern, html).group(0)
        except AttributeError, e:
            #something went wrong
            return False

        return json.loads(response)

    def get_event_id_from_url(self, url):
        pattern = r'(?<=eventId\%3D)\d+'
        try:
            event_id = re.search(pattern, url).group(0)
        except AttributeError, e:
            pattern = r'(?<=eventId%253D).*?(?=\%25)'
            try:
                event_id = re.search(pattern, url).group(0)
            except AttributeError, e:
                return False
            
        return event_id

    def get_ticket_details_by_id(self, event_id):
        event = self.get_event(event_id)
        print "got event"
        price_max = 0
        price_min = 10000000
        status = "Unknown"
        if not event:
            return False

        if "offers" not in event.keys():
            return False

        for offer in event["offers"]:
            try:
                price = float(offer["price"])
                if price > price_max:
                    price_max = price
                if price < price_min:
                    price_min = price
            except KeyError, e:
                #must be high/low
                if float(offer["highprice"]) > price_max:
                    price_max = float(offer["highprice"])
                if float(offer["lowprice"]) < price_min:
                    price_min = float(offer["lowprice"])
                #print json.dumps(offer, indent = 4)

            if "availability" in offer.keys():
                if offer["availability"] == "InStock":
                    status = "Available"
                if offer["availability"] == "SoldOut":
                    status = "Sold Out"
        return {
            "price_min": price_min,
            "price_max": price_max,
            "status": status
            }

    def get_ticket_details_by_url(self, url):
        event_id = self.get_event_id_from_url(url)
        #print event_id
        if not event_id:
            return False
        return self.get_ticket_details_by_id(event_id)

    def crawl_text_file(self):
        filepath = "../etc/ticketweburls.txt"
        with open(filepath) as f:
            url = f.readline().strip()
            while url:
                print url.strip()
                
                if "ticketweb.ca" in url or "ticketweb.com" in url:
                    event_id = self.get_event_id_from_url(url)
                    print self.get_ticket_details_by_id(event_id)
                    
                url = f.readline()

def main():
    t = Ticketweb()
    #t.crawl_text_file()
    #response = t.get_ticket_details(6828825)
    url = "http://ticketmaster.evyy.net/c/219208/264167/4272?u=http%3A%2F%2Fwww.ticketweb.com%2Ft3%2Fsale%2FSaleEventDetail%3Fdispatch%3DloadSelectionData%26eventId%3D6418225&clickref=67%7E13789035%7E20452120%7E%7E"
    url = "http://ticketmaster.evyy.net/c/219208/264167/4272?u=http%3A%2F%2Fwww.ticketweb.ca%2Ft3%2Fsale%2FSaleEventDetail%3FeventId%3D6819935%26dispatch%3DloadSelectionData&clickref=67%7E15617514%7E%7E%7E"
    url = "http://ticketmaster.evyy.net/c/219208/271177/4272?u=http%3A%2F%2Fwww.ticketweb.com%2Ft3%2Fsale%2FSaleEventDetail%3Fdispatch%3DloadSelectionData%26eventId%3D6887585%26REFERRAL_ID%3Dtmfeed&clickref=67%7E16156390%7E23564558%7E%7E"
    url = "http://www.awin1.com/cread.php?clickref=67~16608608~~~&awinmid=3589&awinaffid=97249&p=http%3A%2F%2Fwww.ticketweb.co.uk%2Fevent%2Flunacre-schtum-ep-launch-tickets%2F254163"
    url = "http://ticketmaster.evyy.net/c/219208/264167/4272?u=http%3A%2F%2Fwww.ticketmaster.com%2Fpartner_redirect%3Furl%3Dhttp%253A%252F%252Fwww.ticketweb.com%252Ft3%252Fsale%252FSaleEventDetail%253Fdispatch%253DloadSelectionData%2526eventId%253D6500665%2526REFERRAL_ID%253Dtmfeed&subId1=67%7E14166156%7E20688366%7E%7E"
    url = "http://ticketmaster.evyy.net/c/219208/264167/4272?u=http%3A%2F%2Fwww.ticketweb.com%2Ft3%2Fsale%2FSaleEventDetail%3Fdispatch%3DloadSelectionData%26eventId%3D7014935%26REFERRAL_ID%3Dtmfeed&clickref=67%7E16739405%7E24613031%7E%7E"
    url = "http://ticketmaster.evyy.net/c/219208/271177/4272?u=http%3A%2F%2Fwww.ticketweb.com%2Ft3%2Fsale%2FSaleEventDetail%3FeventId%3D7006535%26pl%3Dhighline%26dispatch%3DloadSelectionData%26REFID%3Dhl%26utm_source%3Dhighline%26utm_medium%3Deventlink%26utm_campaign%3Dgza%252Bdza&clickref=67%7E16698126%7E24535034%7E%7E"

    response = t.get_ticket_details_by_url(url)

    #response = t.get_ticket_details_by_id(254163)
    print json.dumps(response, indent = 4)

if __name__ == '__main__':
    main()