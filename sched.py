import meetup.api
import logging
from twilio.rest import Client


logging.basicConfig(filename='/tmp/sched.log', level=logging.INFO, format='%(asctime)s %(levelname)-8s %(filename)s, line [%(lineno)- 3d] ::: %(message)s')

def notify(msg):
    tw_send_sms(msg)
    logging.info("Notification sent: %s" % msg)

def tw_send_sms(msg):
    tw_ac_sid = ''
    tw_ac_token = ''

    client = Client(tw_ac_sid, tw_ac_token)
    client.messages.create(to='+19144337683',
                           from_='+16468460971',
                           body=msg)


def findMeetupByName(meetup_list, name):
    """

    :param meetup_list: result of GetEvents search
    :param name: substring to look for
    :return: event id
    """
    events_list = []
    for x in meetup_list.results:
        if name in x['name']:
            events_list.append(x['id'])
    return events_list

def checkExistingRSVP(event_data, member_id):
    """
    Check if member RSVPd yet
    :param event_data:
    :param member_id:
    :return: False if no RSVP found, or RSVP response from api.
    """
    for x in event_data:
        if x['member']['member_id'] == member_id:
            return x['response']
    return False

def registerForMeetup(meetup_api_key, group_id, member_id, event_search_pattern):
    client = meetup.api.Client(meetup_api_key)

    event = client.GetEvents(group_id=group_id, status="upcoming")
    event_ids = findMeetupByName(event, event_search_pattern)
    logging.info('Upcoming meetups found: %s' % str(event_ids))
    for event_id in event_ids:
        currentRsvps = client.GetRsvps(event_id=event_id)
        myCurrentRsvp = checkExistingRSVP(currentRsvps.results, member_id)

        if myCurrentRsvp == False:
            logging.info('RSVP not found, attempting to RSVP')
            myRsvp_id = client.CreateRsvp(event_id=event_id, guests=0, rsvp='yes')
            if hasattr(myRsvp_id, 'problem'):
                msg = "RSVP attempt failed with %s, %s" % (myRsvp_id.problem, myRsvp_id.details)
                logging.error(msg)
                notify(msg)
                return False
            else:
                currentRsvps = client.GetRsvps(event_id=event_id)
                myCurrentRsvp = checkExistingRSVP(currentRsvps.results, member_id)
                msg = "RSVP attempt successful, current status: %s" % myCurrentRsvp
                logging.info(msg)
                notify(msg)
                # email / push notify
                return myCurrentRsvp
        else:
            logging.info("group: %s, event: %s, rsvp: %s" % (group_id, event_id, myCurrentRsvp))
            return myCurrentRsvp

def main():

    meetup_api_key = ''

    group_id = 4504982      # gmavb
    member_id = 45248032    # vitaly
    event_search_pattern = 'Friday'

    print registerForMeetup(meetup_api_key, group_id, member_id, event_search_pattern)

def _test():
    meetup_api_key = ''

    group_id = 18509029
    member_id = 45248032
    event_search_pattern = 'Monday'

    print registerForMeetup(meetup_api_key, group_id, member_id, event_search_pattern)


if __name__ == '__main__':
    main()
