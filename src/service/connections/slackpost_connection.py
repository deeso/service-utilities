

class SlackMessagePostConnection():
    URL = 'https://slack.com/api/chat.postMessage'
    CONTENT_TYPE = 'application/json'

    BASE_MSG = {
                'link_names': True,
                'token': None,
                'channel': None,
                'text': None,
               }

    def __init__(self, token=None, workspace=None, user=None):
        pass

    def post_message(self, json_msg):
        out_going_msg = {}
        out_going_msg.update(json_msg)
        out_going_msg['channel'] = self.channel
        out_going_msg['token'] = token