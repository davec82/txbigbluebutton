# Copyright: 2011 Steve Challis (http://schallis.com)
# Copyright: 2012-2016 MoinMoin:ReimarBauer
# Copyright: 2016 Davide Colombo
# License: MIT

"""
    txbigbluebutton



    This module contains functions to access bigbluebutton servers
    Meeting_Setup: for initializing a meeting.
    Meeting: for operations on the meeting after initializing.

"""
import random
try:
    import ujson as json
except ImportError:
    import json

from urllib import urlencode
from txbigbluebutton.utils import api_call, get_xml, xml_match
from twisted.internet import defer


class MeetingSetup(object):
    """
    Initializes meetings
    """

    def __init__(self, bbb_api_url=None, salt=None, meeting_name='',
                 meeting_id='', attendee_password=None,
                 moderator_password=None,
                 logout_url='', max_participants=-1, duration=0,
                 dial_number='', welcome=u'Welcome!',
                 moderator_only_message=u'', meta=None,
                 record=False, auto_start_recording=False,
                 allow_start_stop_recording=True,
                 pre_upload_slide=None
                 ):
        """
        :param bbb_api_url: The url to your bigbluebutton instance (including the api/)
        :param salt: The security salt defined for your bigbluebutton instance
        :param meeting_name: A name for the meeting.
        :param meeting_id: A meeting ID that can be used to identify this meeting by the third party application.
                           This must be unique to the server that you are calling. If you supply a non-unique
                           meeting ID, you will still have a successful call, but will receive a warning message
                           in the response.
                           If you intend to use the recording feature, the meetingID shouldn't contain commas.
        :param attendee_password: The password that will be required for attendees to join the meeting.
                                  This is optional, and if not supplied, BBB will assign a random password.
        :param moderator_password:  The password that will be required for moderators to join the meeting or
                                    for certain administrative actions (i.e. ending a meeting). This is optional,
                                    and if not supplied, BBB will assign a random password.
        :param logout_url: The URL that the BigBlueButton client will go to after users click the OK button on
                           the 'You have been logged out message'. This overrides, the value for
                           bigbluebutton.web.loggedOutURLif defined in bigbluebutton.properties
        :param max_participants: The maximum number of participants to allow into the meeting (including moderators).
                                 After this number of participants have joined, BBB will return an appropriate error
                                 for other users trying to join the meeting. A negative number indicates that
                                 an unlimited number of participants should be allowed (this is the default setting).
        :param duration: The duration parameter allows to specify the number of minutes for the meeting's length.
                         When the length of the meeting reaches the duration, BigBlueButton automatically
                         ends the meeting. The default is 0, which means the meeting continues until the last person
                         leaves or an end API calls is made with the associated meetingID.
        :param dial_number: The dial access number that participants can call in using regular phone.
        :param welcome: A welcome message that gets displayed on the chat window when the participant joins.
                        You can include keywords (%%CONFNAME%%, %%DIALNUM%%, %%CONFNUM%%) which will be
                        substituted automatically. You can set a default welcome message on bigbluebutton.properties
        :param moderator_only_message: Display a message to all moderators in the public chat.
        :param meta: You can pass one or more metadata values for create a meeting.
                    These will be stored by BigBlueButton and later retrievable via the getMeetingInfo call
                    and getRecordings. Examples of meta parameters are meta_Presenter, meta_category, meta_LABEL, etc.
                    All parameters are converted to lower case, so meta_Presenter would be the same as meta_PRESENTER.
        :param record: Setting record=True instructs the BigBlueButton server to record the media and events in
                       the session for later playback. Available values are true or false. Default value is false.
        :param auto_start_recording: Default=False, Setting start_recording=True will automatically
                                     starts recording when first user joins.
                                     NOTE: Don't set to autoStartRecording =false and allowStartStopRecording=false
                                     as the user won't be able to record.
        :param allow_start_stop_recording: Default=True, Allow the user to start/stop recording.
                                           This means the meeting can start recording automatically
                                           (autoStartRecording=true) with the user able to stop/start
                                           recording from the client.
        :param pre_upload_slide: You can preupload slides within the create call by providing an URL to the slides.
        """
        self.bbb_api_url = bbb_api_url
        self.salt = salt
        self.meeting_name = meeting_name
        self.meeting_id = meeting_id
        self.attendee_password = attendee_password
        self.moderator_password = moderator_password
        self.logout_url = logout_url
        self.max_participants = max_participants
        self.duration = duration
        self.dial_number = dial_number
        self.welcome = welcome
        self.record = str(record).lower()
        self.moderator_only_message = moderator_only_message
        self.meta = meta
        self.allow_start_stop_recording = allow_start_stop_recording
        self.auto_start_recording = auto_start_recording
        self.pre_upload_slide = pre_upload_slide

    @defer.inlineCallbacks
    def create_meeting(self):
        """
        creates the meeting
        """
        meeting = Meeting(self.bbb_api_url, self.salt)
        is_running = yield meeting.is_running(self.meeting_id)
        if not is_running:
            call = 'create'
            if self.pre_upload_slide is not None:
                self.welcome = ('The presentation will appear in moment.  To download click <a href="%(url)s"></a>.'
                            '<br> %(welcome)s' % {"url": self.pre_upload_slide,
                                                  "welcome": self.welcome})

            voicebridge = 70000 + random.randint(0, 9999)
            params = dict(name=self.meeting_name, meetingID=self.meeting_id,
                      attendeePW=self.attendee_password, moderatorPW=self.moderator_password,
                      voiceBridge=voicebridge, dialNumber=self.dial_number,
                      welcome=self.welcome, logoutURL=self.logout_url,
                      maxParticipants=self.max_participants, duration=self.duration,
                      record=self.record, moderatorOnlyMessage=self.moderator_only_message,
                      autoStartRecording=self.auto_start_recording,
                      allowStartStopRecording=self.allow_start_stop_recording)
      
            if self.meta:
                for k, v in self.meta.iteritems():
                    meta_key = "meta_%s" % k
                    params.update({meta_key: json.dumps(v)})
            query = urlencode((params))
            xml = yield get_xml(self.bbb_api_url, self.salt, call, query,
                                self.pre_upload_slide)
            if xml is not None:
                defer.returnValue(xml)
            else:
                defer.returnValue(None)
            #return xml is not None


class Meeting(object):
    """
    gives access to meetings
    """

    def __init__(self, bbb_api_url=None, salt=None):
        """
        :param bbb_api_url: The url to your bigbluebutton instance (including the api/)
        :param salt: The security salt defined for your bigbluebutton instance
        """
        self.bbb_api_url = bbb_api_url
        self.salt = salt

    @defer.inlineCallbacks
    def check_api(self):
        """
        This call  simply checks whether a bigbluebutton instane is reachable.

        """
        xml = yield get_xml(self.bbb_api_url, self.salt, None, None)
        defer.returnValue(xml)

    @defer.inlineCallbacks
    def is_running(self, meeting_id):
        """
        This call enables you to simply check on whether or not a meeting is
        running by looking it up with your meeting ID.

        :param meeting_id: ID that can be used to identify the meeting
        """
        call = 'isMeetingRunning'
        match = 'running'
        query = urlencode((
            ('meetingID', meeting_id),
        ))
        xml = yield get_xml(self.bbb_api_url, self.salt, call, query)
        defer.returnValue(xml_match(xml, match))

    def join_url(self, meeting_id, name, password, optional_params=None):
        """
        generates the url for accessing a meeting

        :param meeting_id: ID that can be used to identify the meeting
        :param name: The name that is to be used to identify this user to
                     other conference attendees.
        :param password: The password that this attendee is using.
                         If the moderator password is supplied, he will be
                         given moderator status
                         (and the same for attendee password, etc)
        :param optional_params: optional params used by MConf for example
        """
        call = 'join'
        params = dict(fullName=name, meetingID=meeting_id,
                      password=password)

        if optional_params:
            params.update(optional_params) 
        query = urlencode((params))
        hashed = api_call(self.salt, query, call)
        return self.bbb_api_url + call + '?' + hashed

    def end_meeting_url(self, meeting_id, password):
        """
        Use this to generate the url to end a meeting

        :param meetingID: The meeting ID that identifies the meeting you are attempting to end.
        :param password: The moderator password for this meeting.
                         You can not end a meeting using the attendee password.
        """
        call = 'end'
        query = urlencode((
            ('meetingID', meeting_id),
            ('password', password),
        ))

        hashed = api_call(self.salt, query, call)
        return self.bbb_api_url + call + '?' + hashed

    @defer.inlineCallbacks
    def end_meeting(self, meeting_id, password):
        """
        Use this to forcibly end a meeting and kick all participants out of the meeting.

        :param meetingID: The meeting ID that identifies the meeting you are attempting to end.
        :param password: The moderator password for this meeting.
                         You can not end a meeting using the attendee password.
        """
        call = 'end'
        query = urlencode((
            ('meetingID', meeting_id),
            ('password', password),
        ))
        xml = yield get_xml(self.bbb_api_url, self.salt, call, query)
        if xml is not None:
            defer.returnValue(xml)
        else:
            defer.returnValue(None)

    @defer.inlineCallbacks
    def meeting_info(self, meeting_id, password, meta=False):
        """
        This call will return all of a meeting's information,
        including the list of attendees as well as start and end times.

        :param meetingID: The meeting ID that identifies the meeting
        :param password: The moderator password for this meeting.
        """
        call = 'getMeetingInfo'
        query = urlencode((
            ('meetingID', meeting_id),
            ('password', password),
        ))
        xml = yield get_xml(self.bbb_api_url, self.salt, call, query)
        if xml is not None:
            # Create dict of values for easy use in template
            users = []
            attendees = xml.find('attendees')
            if attendees is not None:
                for attendee in attendees.getchildren():
                    user = {}
                    user['user_id'] = attendee.find('userID').text
                    user['name'] = attendee.find('fullName').text
                    user['role'] = attendee.find('role').text
                    users.append(user)
            metadata_dict = {}
            if meta:
                metadata = xml.find('metadata')
                for data in list(metadata):
                    metadata_dict[data.tag] = json.loads(data.text)

            meeting_info = {
                'meeting_name': xml.find('meetingName').text,
                'meeting_id': xml.find('meetingID').text,
                'create_time': int(xml.find('createTime').text),
                'voice_bridge': int(xml.find('voiceBridge').text),
                'attendee_pw': xml.find('attendeePW').text,
                'moderator_pw': xml.find('moderatorPW').text,
                'running': xml.find('running').text == "true",
                'recording': xml.find('recording').text == "true",
                'has_been_forcibly_ended': xml.\
                                find('hasBeenForciblyEnded').text == "true",
                'start_time': int(xml.find('startTime').text),
                'end_time': int(xml.find('endTime').text),
                'participant_count': int(xml.find('participantCount').text),
                'max_users': int(xml.find('maxUsers').text),
                'moderator_count': int(xml.find('moderatorCount').text),
                'users': users
            }
            if meta and metadata_dict:
                meeting_info.update(metadata_dict)
            defer.returnValue(meeting_info)
        else:
            defer.returnValue(None)

    @defer.inlineCallbacks
    def get_meetings(self, meta=False):
        """
        This call will return a list of all the meetings found on this server.
        """
        call = 'getMeetings'
        query = urlencode((
            ('random', 'random'),
        ))

        xml = yield get_xml(self.bbb_api_url, self.salt, call, query)
        if xml is not None:
            # Create dict of values for easy use in template
            all_meetings = []
            meetings = xml[1].findall('meeting')
            for meeting in meetings:
                meeting_id = meeting.find('meetingID').text
                password = meeting.find('moderatorPW').text
                info = yield self.meeting_info(meeting_id, password, meta=meta)
                all_meetings.append({
                    'name': meeting_id,
                    'moderator_pw': password,
                    'attendee_pw': meeting.find('attendeePW').text,
                    'has_been_forcibly_ended': meeting.\
                                find('hasBeenForciblyEnded').text == "true",
                    'running': meeting.find('running').text == "true",
                    'create_time': int(meeting.find('createTime').text),
                    'info': info
                })
            defer.returnValue(all_meetings)
        else:
            defer.returnValue(None)

    @defer.inlineCallbacks
    def get_recordings(self, meeting_id=u'', meta=None):
        """
        Retrieves the recordings that are available for playback for a given meetingID (or set of meeting IDs).

        :param meetingID: The meeting ID that identifies the meeting
        :param meta: You can pass one or more metadata values to filter the recordings returned
        """
        call = 'getRecordings'
        params = {}
        if meeting_id:
            params.update(dict(meetingID=meeting_id))
        if meta:
            for k, v in meta.iteritems():
                meta_key = "meta_%s" % k
                params.update({meta_key: json.dumps(v)})
        if params:
            query = urlencode((params))
        else:
            query = ''
        xml = yield get_xml(self.bbb_api_url, self.salt, call, query)
        # ToDO implement more keys
        if xml is not None:
            recordings = xml.find('recordings')
            records = []
            for meeting in list(recordings):
                record = {}
                record['record_id'] = meeting.find('recordID').text
                record['meeting_id'] = meeting.find('meetingID').text
                record['meeting_name'] = meeting.find('name').text
                record['published'] = meeting.find('published').text == "true"
                record['start_time'] = meeting.find('startTime').text
                record['name'] = meeting.find('name').text
                record['end_time'] = meeting.find('endTime').text
                metadata = meeting.find('metadata')
                for data in list(metadata):
                    record[data.tag] = json.loads(data.text)
                record['size'] = meeting.find('size').text
                playback = meeting.find('playback')
                play_format = playback.find('format')
                record['length'] = play_format.find('length').text
                record['url'] = play_format.find('url').text
                records.append(record)
            defer.returnValue(records)
        else:
            defer.returnValue(None)

    @defer.inlineCallbacks
    def publish_recordings(self, record_id, publish=False):
        """
        Publish and unpublish recordings for a given recordID (or set of record IDs).

        :param record_id: A record ID for specify the recordings to apply the publish action.
                         It can be a set of meetingIDs separate by commas.
        :param publish: The value for publish or unpublish the recording(s). Available values: True or False.
        """
        call = 'publishRecordings'
        match = 'published'
        query = urlencode((
            ('recordID', record_id),
            'publish', str(publish).lower()
        ))
        xml = yield get_xml(self.bbb_api_url, self.salt, call, query)
        defer.returnValue(xml_match(xml, match))

    @defer.inlineCallbacks
    def delete_recordings(self, record_id, publish=False):
        """
        Delete one or more recordings for a given recordID (or set of record IDs).

        :param record_id: A record ID for specify the recordings to delete. It can be a set of
                         meetingIDs separate by commas.
        :param publish: The value for publish or unpublish the recording(s). Available values: True or False.
        """
        call = 'deleteRecordings'
        match = "deleted"
        query = urlencode((
            ('recordID', record_id),
            'publish', str(publish).lower()
        ))
        xml = yield get_xml(self.bbb_api_url, self.salt, call, query)
        defer.returnValue(xml_match(xml, match))
