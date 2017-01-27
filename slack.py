import requests
import json

from slackclient import SlackClient

from kalliope import Utils
from kalliope.core.NeuronModule import NeuronModule, MissingParameterException

Slack_Actions = (
    "POST",
    "READ"
)


class Slack(NeuronModule):
    def __init__(self, **kwargs):

        super(Slack, self).__init__(**kwargs)

        # parameters
        self.action = kwargs.get('action', None)
        self.token = kwargs.get('slack_token', None)
        self.channel = kwargs.get('channel', None)
        self.message = kwargs.get('message', None)
        self.nb_messages = int(kwargs.get('nb_messages', 10))  # Int
        
        # check parameters
        if self._is_parameters_ok():
            sc = SlackClient(self.token)

            if self.action == Slack_Actions[0]:  # POST
                if self._is_post_parameters_ok():

                    sc.api_call(
                        "chat.postMessage",
                        channel=self.channel,
                        text=self.message,
                        as_user=True
                    )

                    message = {
                        "action": self.action,
                        "text": self.message,
                        "channel": self.channel
                    }

            if self.action == Slack_Actions[1]:  # READ
                if self.is_read_parameters_ok():
                    # get the list of channel
                    user_list = sc.api_call("users.list")
                    channel_list = sc.api_call("channels.list")

                    # Find the channel ID of the given channel name
                    channel_id = self._get_channel_id(channel_name=self.channel,
                                                      channel_list=channel_list)

                    # Get all messages of the channel
                    messages_list = self._get_list_messages(token=self.token,
                                                            channel_id=channel_id,
                                                            nb_messages=self.nb_messages)

                    # Associate user ID of messages to the user name
                    user_messages = self._get_user_message_list(user_list=user_list,
                                                                messages=messages_list)

                    message = {
                        "action": self.action,
                        "messages": user_messages,
                        "channel": self.channel
                    }

            self.say(message)

    def _is_parameters_ok(self):
        """
        Check if received parameters are ok to perform operations in the neuron.
        :return: True if parameters are ok, raise an exception otherwise.

        .. raises:: MissingParameterException
        """
        if self.token is None:
            raise MissingParameterException("Slack needs a slack_token")
        if self.action is None:
            raise MissingParameterException("Slack needs an action parameter")
        return True

    def _is_post_parameters_ok(self):
        """
        Check if parameters required to POST a message are present.
        :return: True, if parameters are OK, raise exception otherwise.

        .. raises:: MissingParameterException
        """
        if self.channel is None:
            raise MissingParameterException("Slack needs a channel")
        if self.message is None:
            raise MissingParameterException("Slack needs a message")
        
        return True

    def is_read_parameters_ok(self):
        """
        Check if parameters required to READ a message are present.
        :return: True, if parameters are OK, raise exception otherwise.

        .. raises:: MissingParameterException
        """
        if self.channel is None:
            raise MissingParameterException("Slack needs a channel")

        return True

    @staticmethod
    def _get_list_messages(token=None,
                           channel_id=None,
                           nb_messages=None):
        """
        Using Slack API to access messages from a given channel id.
        :param token: the API token
        :param channel_id: the channel id
        :param nb_messages: the number of messages
        :return: the message list of the last nb_messages
        """
        message_list = list()

        data = {
            "token": token,
            "channel": channel_id
        }

        r = requests.post("https://slack.com/api/channels.history",
                          data=data)

        if r.status_code == 200:
            json_data = json.loads(r.text)
            if "messages" in json_data:
                count = 0
                for message in json_data["messages"]:
                    if count < nb_messages:
                        message_list.append(message)
                        count += 1
                    else: break

        return message_list

    @staticmethod
    def _get_channel_id(channel_name=None,
                        channel_list=None):
        """
        return the id from the channel list corresponding to the channel name.
        :param channel_name: str of the name
        :param channel_list: list of the channel
        :return: the id from the channel list corresponding to the channel name.
        """
        id = None
        if "channels" in channel_list:
            for channel in channel_list["channels"]:
                if "name" in channel:
                    if channel_name == channel["name"]:
                        if "id" in channel:
                            id = channel["id"]
        if id is None:
            Utils.print_warning("The channel name has not been found !")
        return id

    @staticmethod
    def _get_user_message_list(user_list=None,
                               messages=None):
        """
        List of associate message to an user.
        :param user_list: the full list of user
        :param messages: the list of messages
        :return: the list of dicts user:message
        """
        current_user_message_dict = dict()
        user_message_list = list()

        for message in messages:
            if "username" in message:
                current_user_message_dict[message["username"]] = message["text"]
                user_message_list.append(current_user_message_dict)
                current_user_message_dict = dict()
                continue
            elif "user" in message:
                for user in user_list["members"]:
                    if "id" in user:
                        if user["id"] == message["user"]:
                            current_user_message_dict[user["name"]] = message["text"]
                            user_message_list.append(current_user_message_dict)
                            current_user_message_dict = dict()
                            continue

        return user_message_list




