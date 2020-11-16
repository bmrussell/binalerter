import http.client, urllib
import logging

class Pushover(object):
    """Pushover: Wrapper for PushOver API (https://pushover.net/)

    Note: implements singleton object.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:            
            cls._instance = super(Pushover, cls).__new__(cls)
            # Put any initialization here.
            ApiUser = None
            ApiToken = None
        return cls._instance

    @classmethod
    def Initialise(self, user=None, token=None):
        """Initialise: Set up the Pushover interface

        Note:
            When user and token supplied, these are persisted in an ecrypted file using CredentialStore
            When user and token are omitted they are loaded from file
        Args:
            user (str) : Pushover API user token
            token (str): Pushover API app token
        """
        self.ApiUser = user
        self.ApiToken = token
    
    @classmethod
    def Notify(self, message, sound):
        """Notify: Send a push notification

        Note:
            sound used is cashregister

        Args:
            message (str) : The message to send
        """
        conn = http.client.HTTPSConnection("api.pushover.net:443")
        conn.request("POST", "/1/messages.json",
        urllib.parse.urlencode({
            "token": self.ApiToken,
            "user": self.ApiUser,
            "message": message,
            "sound" : sound
        }), { "Content-type": "application/x-www-form-urlencoded" })
        response = conn.getresponse()
        if response.status == 200:
            logging.info("Push notification sent (" + str(response.status) + ":" + response.reason + ")")            
        else:
            logging.error("Push notification failed (" + str(response.status) + ":" + response.reason + ")")