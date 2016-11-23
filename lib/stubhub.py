#!/usr/bin/python2.7
import urllib2
from caching import Caching

class StubHub():
    def __init__(self, token):
        self.token = token
        self.base_url = "https://api.stubhub.com/"
        self.caching = Caching()

def main():
    token = "euoDx_TAcyt5zf2Iu2MUruT4S2oa"
    s = StubHub(token)

if __name__ == '__main__':
    main()