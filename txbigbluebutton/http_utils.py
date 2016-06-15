# Copyright: 2016 Davide Colombo
# License: MIT

"""
    txbigbluebutton.http_utils

    This module contains http helper functions to access bigbluebutton servers

"""


from twisted.internet import protocol
from twisted.internet import defer
from twisted.web.http_headers import Headers
from twisted.internet import reactor
from twisted.web.client import Agent
from twisted.web.iweb import IBodyProducer
from zope.interface import implements
from twisted.internet.defer import succeed


class StringProducer(object):
    implements(IBodyProducer)

    def __init__(self, body):
        self.body = body
        self.length = len(body)

    def startProducing(self, consumer):
        consumer.write(self.body)
        return succeed(None)

    def pauseProducing(self):
        pass

    def stopProducing(self):
        pass


class SimpleReceiver(protocol.Protocol):
    def __init__(self, d):
        self.buf = ''
        self.d = d

    def dataReceived(self, data):
        self.buf += data

    def connectionLost(self, reason):
        self.d.callback(self.buf)


def httpRequest(url, values=None, headers=None, method='POST'):

    agent = Agent(reactor)
    data = values
    d = agent.request(method, url, Headers(headers) if headers else None,
                      StringProducer(data) if data else None)

    def handle_response(response):
        if response.code == 204:
            d = defer.succeed('')
        else:
            d = defer.Deferred()
            response.deliverBody(SimpleReceiver(d))
        return d

    def failure(err):
        err.printTraceback()

    d.addCallback(handle_response)
    d.addErrback(failure)
    return d
