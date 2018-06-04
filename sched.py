import meetup.api
import logging
from twilio.rest import Client
import yaml
import sys

logging.basicConfig(filename = '/tmp/sched.log', 
                       level = logging.INFO, 
                      format = '%(asctime)s %(levelname)-8s %(filename)s, line [%(lineno)- 3d] ::: %(message)s')

try:
    parse_config = yaml.safe_load(open('config.yaml'))
except:
    logging.fatal("no configuration file loaded")
    sys.exit(1)

def notify(msg):
    tw_send_sms(msg)
    logging.info("Notification sent: %s" % msg)

def tw_send_sms(msg):
    global parse_config
    tw_ac_sid = parse_config['live']['tw_ac_sid']
    tw_ac_token = parse_config['live']['tw_ac_token']
    tw_sms_from = parse_config['live']['tw_sms_from']
    tw_sms_to = parse_config['live']['tw_sms_to']
 
    client = Client(tw_ac_sid, tw_ac_token)
    client.messages.create(to = tw_sms_to,
                           from_ = tw_sms_from,
                           body = msg)

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

def registerForMeetup(meetup_api_key, group_id, member_id, event_search_pattern, max_events = 12):
    client = meetup.api.Client(meetup_api_key)

    events = client.GetEvents(group_id=group_id, status="upcoming")
    event_ids = findMeetupByName(events, event_search_pattern)
    logging.info('Upcoming events found: %s' % str(event_ids))

    rsvpStatus = {}
    for event_id in event_ids[:max_events]:
        currentRsvps = client.GetRsvps(event_id=event_id)
        logging.debug('event_id: %s, currentRsvps: %s' % (event_id, currentRsvps.results))
        myCurrentRsvp = checkExistingRSVP(currentRsvps.results, member_id)
        logging.info('event_id: %s, myRsvp: %s' % (event_id, myCurrentRsvp))	
        if myCurrentRsvp == False:
            logging.info('event_id: %s, RSVP not found, attempting to RSVP' % event_id)
            myRsvp_id = client.CreateRsvp(event_id=event_id, guests=0, rsvp='yes')
            if hasattr(myRsvp_id, 'problem'):
                msg = "event_id: %s, RSVP attempt failed with %s, %s" % (event_id, myRsvp_id.problem, myRsvp_id.details)
                logging.error(msg)
                notify(msg)
                rsvpStatus[event_id] = False
            else:
                currentRsvps = client.GetRsvps(event_id=event_id)
                myCurrentRsvp = checkExistingRSVP(currentRsvps.results, member_id)
                msg = "event_id: %s, RSVP attempt successful, current status: %s" % (event_id, myCurrentRsvp)
                logging.info(msg)
                notify(msg)
                # email / push notify
                rsvpStatus[event_id] = myCurrentRsvp
        else:
            logging.info("group: %s, event: %s, rsvp: %s" % (group_id, event_id, myCurrentRsvp))
            rsvpStatus[event_id] = myCurrentRsvp
    return rsvpStatus

def main(config):
    meetup_api_key = config['meetup_api_key']

    group_id = config['meetup_group_id']
    member_id = config['meetup_member_id']
    event_search_pattern = config['meetup_event_search_pattern']

    print registerForMeetup(meetup_api_key, group_id, member_id, event_search_pattern)

def _test():
    meetup_api_key = ''

    group_id = 18509029
    member_id = 45248032
    event_search_pattern = 'Monday'

    print registerForMeetup(meetup_api_key, group_id, member_id, event_search_pattern)


if __name__ == '__main__':
    main(config=parse_config['live'])
    #TODO: 'live' must be a command line argument to select profile
    
