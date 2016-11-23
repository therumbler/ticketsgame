#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
import urllib2
import json
import re
import time
from urllib import urlencode
from caching import Caching

class Ticketfly():
    def __init__(self):
        self.base_url = "http://www.ticketfly.com/api/"
        self.caching = Caching()

    def get(self, endpoint, **params):
        querystring = urlencode(params)
        url = "%s%s?%s" % (self.base_url, endpoint, querystring)
        #print url
        response_text = self.caching.get(url)
        if response_text:
            return json.loads(response_text)
        response = urllib2.urlopen(url)
        return json.load(response)

    def get_event_by_id(self, event_id):
        """
        Convenience method
        """
        response = self.get("events/event.json", eventId = event_id)
        #print response
        event = False
        if response["status"] != "error":
            if response["totalResults"] > 0:
                #print response
                event = response["events"][0]
        return event

    def get_prices(self, event_id):
        event = self.get("events/event.json", eventId = event_id)
        if len(event["events"]) == 0:
            return False
        ticket_price = event["events"][0]["ticketPrice"].replace(",", "")
        #print ticket_price
        if len(ticket_price)== 0:
            return False
        if "at the door" in ticket_price.lower():
            #print ticket_price.encode("utf-8")
            #price = re.search(ur"(?<=[•,] \$)\d*(?= at)", ticket_price).group(0)
            pattern = ur"(?<=[•,-] \$)\d*(?= (at|\())"
            try:
                price = re.search(pattern, ticket_price.lower()).group(0)
            except AttributeError, e:
                pattern = r'(?<=\$)\d+'
                price = re.search(pattern, ticket_price).group(0)     
            price_min = float(price)
            price_max = float(price)
        elif "-" in ticket_price:
            try:
                price_min = re.search(r'(?<=\$).*(?=\ -)', ticket_price).group(0)
                #print price_min
                price_max = re.search(r'(?<=\- \$)\d*', ticket_price).group(0)
            except AttributeError, e:
                pattern = r'(?<=\$)\d+'
                prices = re.findall(pattern, ticket_price)
                if len(prices) > 0:
                    price_min = min([float(p) for p in prices])
                    price_max = max([float(p) for p in prices])
                else:
                    return False
            #print price_min, price_max
           
        else:
            price = ticket_price.replace("$", "")
            try:
                price_min = float(price)
                price_max = float(price)
            except ValueError, e:
                #major fail
                return False

        
        if type(price_min) != float:
            price_min = price_min.replace(",", "")
            price_max = price_max.replace(",", "")

        try:
            float(price_min)
        except ValueError, e:
            price = re.search(r'\d+', price_min).group(0)
            price_min = float(price)
            price_max = float(price)
        
        return {
            "price_min": float(price_min),
            "price_max": float(price_max)
        }
        #print json.dumps(event, indent = 4)

    def get_ticket_details(self, event_id):
        details = {
            "price_min": False,
            "price_max": False,
            "status": "Unknown" # Sold Out, Available or Unknown
        }

        prices = self.get_prices(event_id)
        if prices:
            details["price_min"] = prices["price_min"]
            details["price_max"] = prices["price_max"]

        event = self.get_event_by_id(event_id)
        #print json.dumps(event, indent = 4)
        if not event:
            return False
        #print json.dumps(event, indent = 4)
        if event["eventStatusCode"] == "BUY":
            details["status"] = "Available"
        elif event["eventStatusCode"] == "SOLD_OUT":
            details["status"] = "Sold Out"
        return details

def main():    
    tf = Ticketfly()
    print tf.get_ticket_details(event_id = "1264857")
    
    """
    for event_id in range(1292229, 1353855):
        response = tf.get("events/event.json", eventId = event_id)
        #print response
        if response["status"] != "error":
            if response["totalResults"] > 0:
                #print response
                event = response["events"][0]
                if event["eventStatusCode"] not in ["BUY", "OFF_SALE", "CUSTOM"]:
                    print event_id, event["eventStatusCode"]
                time.sleep(1)
        #print json.dumps(event, indent = 4)
       
        """
       
if __name__ == '__main__':
    main()