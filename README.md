# txbigbluebutton

The work of this project is derivated from https://github.com/schallis/django-bigbluebutton 98f2259fa3 by Steve Challis and 
https://bitbucket.org/ReimarBauer/bigbluebutton-python-api by Reimar Bauer.

It is a wrapper, written in Twisted,  for asynchronous accessing the API of bigbluebutton http://code.google.com/p/bigbluebutton/wiki/API


A simple example:

```
import uuid
from txbigbluebutton import MeetingSetup, Meeting
from twisted.internet import reactor

bbb_url = "http://url_to_bbb_server/bigbluebutton/api/"
bbb_salt = "bbb_salt"
meeting_id = str(uuid.uuid4())
meeting_name = "RoomName"
pwd_att = "password_att"
pwd_mod = "password_mod"

def display(result):
    print result

def join(result, name, pwd):
    print "run join for ", name
    meeting = Meeting(bbb_url, bbb_salt)
    return meeting.join_url(meeting_id, name, pwd)

def get_meetings(result):
    print "get meetings"
    meeting = Meeting(bbb_url, bbb_salt)
    return meeting.get_meetings()

def is_running(result):
    print "is running"
    meeting = Meeting(bbb_url, bbb_salt)
    return meeting.is_running(meeting_id)

def end_meeting_url(result, pwd):
    print "end meeting url"
    meeting = Meeting(bbb_url, bbb_salt)
    return meeting.end_meeting_url(meeting_id, pwd)


if __name__ == '__main__':

    session = MeetingSetup(bbb_url, bbb_salt,
                           meeting_name, meeting_id,
                           pwd_att, pwd_mod,
                           bbb_url)

    d = session.create_meeting()
    d.addCallback(display)
    d.addCallback(join, "Attendee", pwd_mod)
    d.addCallback(display)
    d.addCallback(join, "Moderator", pwd_att)
    d.addCallback(display)
    d.addCallback(get_meetings)
    d.addCallback(display)
    d.addCallback(is_running)
    d.addCallback(display)
    d.addCallback(end_meeting_url, pwd_mod)
    d.addCallback(display)
    d.addBoth(lambda _: reactor.stop())
    reactor.run()
```
