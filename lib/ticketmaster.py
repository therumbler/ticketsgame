#!/usr/bin/python2.7
import urllib2
import re
import os
import json
from datetime import datetime
from caching import Caching

class Ticketmaster():
    def __init__(self):
        self.caching = Caching()

    def get_date(self):
        return datetime.now().strftime("%Y%m%d")

    def get_path(self):
        if "/lib" in os.getcwd():
            path = "../etc/appcache/%s/" % self.get_date()
        else:
            path = "etc/appcache/%s/" % self.get_date()
        return path

    def get_html(self, event_id):
        path = self.get_path()
        filename = path + "%s.html" % event_id
      
        try:
            with open(filename) as f:
                html = f.read()
        except IOError, e:
            #file doesn't exist. Let's hit the web
            url = "http://www.ticketmaster.ca/event/%s" % event_id
            try:
                response = urllib2.urlopen(url)
            except urllib2.HTTPError:
                print "error"
                print url, "must be expired"
                return False
            except httplib.IncompleteRead, e:
                print "httplib.IncompleteRead error"
                print "trying again"
                return self.get_html(event_id)
            html = response.read() 

            with open(filename, "w") as f:
                f.write(html)

        return html

    def process_price_list(self, price_list):
        """
        converts strings to floats
        """
        return_values = []
        for p in price_list:
            try:
                p = float(p)
                if p not in return_values:
                    return_values.append(p)
            except ValueError, e:
                print "error"
                pass
        return return_values

    def get_prices(self, html):
        #html = self.get_html(event_id)
        pattern = r'(?<=<strong>CA \$)\d+\.\d+(?=</strong>)'
        prices = re.findall(pattern, html)

        prices = self.process_price_list(prices)
        return prices

    def get_fees(self, html):
        #html = self.get_html(event_id)
        pattern = r'(?<=Ticket \+ CA \$)\d+.\d+(?= Fees)'
        fees = re.findall(pattern, html)

        fees = self.process_price_list(fees)
        return fees

    def get_ticket_prices(self, event_id):
        html = self.get_html(event_id)
        if not html:
            return False
        prices = self.get_prices(html)
   
        price_max = max(prices)
        price_min = min(prices)

        fees = self.get_fees(html)

        if len(fees) ==0:
            fee_max = 0
            fee_min = 0
        else:
            fee_max = max(fees)
            fee_min = min(fees)

        return {
            "status": "Unknown",
            "price_min": price_min + fee_min,
            "price_max": price_max + fee_max
        }

    def get_linked_data(self, event_id):
        html = self.get_html(event_id)
        if not html:
            return False
        pattern = r'(?<="application/ld\+json">).*(?=</script>)'
        try:
            string = re.search(pattern, html).group(0)
        except AttributeError, e:
            #looks like it's a self.location.replace url. (Event is over)
            return False
        data = json.loads(string)
        return data

    def get_event_id_from_url(self, url):
        try:
            pattern = r'(?<=event\%2F).*?(?=[&%])'
            event_id = re.search(pattern, url).group(0)
        except AttributeError, e:
            pattern = r'(?<=event\/).*'
            try:
                event_id = re.search(pattern, url).group(0)
            except AttributeError, e:
                return False
        return event_id

    def get_ticket_details_by_url(self, url):
        #print url
        event_id = self.get_event_id_from_url(url)
        if not event_id:
            return False
        linked_data  = self.get_linked_data(event_id)
        if not linked_data:
            return False
        price_max = 0
        price_min = 9999999
        status = "Sold Out"
        
        for offer in linked_data[0]["offers"]:
            if "availability" in offer.keys():
                if offer["availability"] == "InStock":
                    status = "Available"
            else:
                #I'm assuming since there's at least one offer, it's available
                status = "Available"
            try:
                price = float(offer["price"])
                if price > price_max:
                    price = price_max
                if price < price_min:
                    price = price_min

            except KeyError, e:
                # must be highPrice and lowPrice
                if float(offer["highPrice"]) > price_max:
                    price_max = float(offer["highPrice"])
                if float(offer["lowPrice"]) < price_min:
                    price_min = float(offer["lowPrice"])

        return {
            "status": status,
            "price_min": price_min,
            "price_max": price_max
        }

def main():
    tm = Ticketmaster()
    event_id = "1000514C7B221780"
    #print tm.get_ticket_prices(event_id)
    url = "http://ticketmaster.evyy.net/c/219208/264167/4272?u=http%3A%2F%2Fticketmaster.ca%2Fevent%2F1000514C7B221780&subId1=67%7E16589729%7E24330761%7E%7E"
    url = "http://ticketmaster.evyy.net/c/219208/264167/4272?u=http%3A%2F%2Fticketmaster.com%2Fevent%2F020050A69D743FCD&subId1=67%7E15078512%7E22553344%7E%7E"
    url = "http://http://www.ticketmaster.com/event/1B004F9508999A75"
    url = "http://ticketmaster.evyy.net/c/219208/264167/4272?u=http%3A%2F%2Fwww.ticketmaster.com%2Fpartner_redirect%3Furl%3Dhttp%253A%252F%252Fconcerts.livenation.com%252Fevent%252F1C0050BDAFA82702&subId1=67%7E15312068%7E22506036%7E%7E"
    url = "http://ticketmaster.evyy.net/c/219208/264167/4272?u=http%3A%2F%2Fticketmaster.com%2Fevent%2F1B0050C6F8BF6329&subId1=67%7E15337547%7E22539748%7E%7E"
    url = "http://ticketmaster.evyy.net/c/219208/264167/4272?u=http%3A%2F%2Fticketmaster.com%2Fevent%2F1B0050E80484CE79&subId1=67%7E15639197%7E22899288%7E%7E"
    url = "http://ticketmaster.evyy.net/c/219208/264167/4272?u=http%3A%2F%2Fticketmaster.com%2Fevent%2F09004F63BAAE3007&subId1=67%7E13452420%7E22553396%7E%7E"
    response = tm.get_ticket_details_by_url(url)
    print json.dumps(response, indent = 4)
    #print tm.get_html("1000515CD58BAC39")
    #print float("10.3h")

if __name__ == '__main__':
    main()
