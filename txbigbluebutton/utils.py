# Copyright: 2011 Steve Challis (http://schallis.com)
# Copyright: 2012-2016 MoinMoin:ReimarBauer
# Copyright: 2016 Davide Colombo
# License: MIT

"""
    txbigbluebutton.utils

    This module contains helper functions to access bigbluebutton servers

"""

import xml.etree.ElementTree as ET
try:
    import ujson as json
except ImportError:
    import json


from hashlib import sha1
from twisted.internet import defer
from txbigbluebutton.http_utils import httpRequest


def decode_json(value):
        try:
            decoded_value = json.loads(value)
        except Exception as e:
            decoded_value = value
        return decoded_value


def parse(response):
    """
    :param reponse: XML Data
    """
    try:
        xml = ET.fromstring(response)
        code = xml.find('returncode').text
        if code == 'SUCCESS':
            return xml
        else:
            return None
    #XXX refactor exception
    except:
        return None


def api_call(salt, query, call):
    """
    builds the hash based on the call, query and salt

    :param salt: The security salt defined for your bigbluebutton instance
    :param query: The query parameters for calling the bigbluebutton resource
    :param call: The bigbluebutton resource name
    """
    prepared = "%s%s%s" % (call, query, salt)
    checksum = sha1(prepared).hexdigest()
    return "%s&checksum=%s" % (query, checksum)


@defer.inlineCallbacks
def get_xml(bbb_api_url, salt, call, query, pre_upload_slide=None):
    """
    gets XML from the bigbluebutton ressource

    :param bbb_api_url: The url to your bigbluebutton instance (including the api/)
    :param salt: The security salt defined for your bigbluebutton instance
    :param call: The bigbluebutton resource name
    :param query: The query parameters for calling the bigbluebutton resource
    :param pre_upload_slide: on create a file could be uploaded
    """

    if call:
        hashed = api_call(salt, query, call)
        url = bbb_api_url + call + '?' + hashed
    else:
        url = bbb_api_url

    if call == "create" and pre_upload_slide is not None:
        xml = ("<?xml version='1.0' encoding='UTF-8'?> <modules> <module name='presentation'> "
               "<document url='%(pre_upload_slide)s'/> </module></modules>" % {"pre_upload_slide": pre_upload_slide})
        headers = {'Content-Type': ['application/xml']}
        response = yield httpRequest(url, xml, headers, 'POST')
        defer.returnValue(parse(response))
    else:
        response = yield httpRequest(url, None, None, 'GET')
        defer.returnValue(parse(response))


def xml_match(xml, match):
    """
    Finds the first subelement matching match and verifies that its text attribute is 'true'

    :param xml: xml as ET instance
    :param match: pattern to lookup by find
    :return: boolean
    """
    if xml is not None:
        return xml.find(match).text == 'true'
    return False
