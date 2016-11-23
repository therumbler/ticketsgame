#!/usr/bin/python2.7
import re
import json
from caching import Caching

class AXS():
    def __init__(self):
        self.base_url = "http://www.axs.com/events/"
        self.caching = Caching()

    def get(self, event_id):
        url = self.base_url + event_id
        html = self.caching.get(url)
        return html

    def get_event_id_from_url(self, url):
        pattern = r"(?<=events\/)\d+"
        try:
            event_id = re.search(pattern, url).group(0)
        except AttributeError, e:
            print "AXS Error: i don't know what to do with", url
            return False
        return event_id

    def get_ticket_details(self, url):
        event_id = self.get_event_id_from_url(url)
        if not event_id:
            return False
        html = self.get(event_id)
        #print html.encode("utf-8")
        linked_data = self.get_linked_data(html)
        if not linked_data:
            print "Axs error. linked data not found", url
            return False
        #print json.dumps(linked_data, indent = 4)
        status = "Unknown"
        for o in linked_data["offers"]:
            # if it's been marked as Available previously
            # don't mark it as sold out as there may be
            # multiple offers
            if o["availability"] == "SoldOut" and status != "Available":
                status = "Sold Out"
            if o["availability"] == "InStock":
                status = "Available"

        return {
            "price_min": False,
            "price_max": False,
            "status": status
        }
        
    def get_linked_data(self, html):
        pattern = r'(?<="application/ld\+json">).*?(?=</script>)'
        try:
            string = re.search(pattern, html, re.DOTALL).group(0)
        except AttributeError, e:
            
            #looks like it's a self.location.replace url. (Event is over)
            return False

        #print string.encode("utf-8")
        return json.loads(string)

def main():
    a = AXS()

    url = "http://www.axs.com/events/312132/soft-machine-tickets?aff=ukaffbandsintown"
    url = "http://www.axs.com/events/324863/the-radio-dept-tickets?aff=usaffbandsintown"
    url = "http://www.axs.com/artists/113619/trentemoller-tickets"
    url = "http://www.axs.com/events/326332/atif-aslam-kanika-kapoor-tickets?aff=ukaffbandsintown"
    url = "http://www.axs.com/events/324412/robert-glasper-experiment-tickets?aff=usaffsongkick"
    url = "http://www.axs.com/uk/events/308372/opeth-tickets?skin=wembley"
    response = a.get_ticket_details(url)
    print json.dumps(response, indent = 4)

if __name__ == '__main__':
    main()