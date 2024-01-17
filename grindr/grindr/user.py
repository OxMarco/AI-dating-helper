import json
import binascii
import os
import logging
from grindr.client import Client
from grindr.utils import *
from grindr.paths import *


class User:
    def __init__(self):
        self.sessionId = None
        self.profileId = None
        self.authToken = None
        self.xmppToken = None
        self.logged_in = False
        self.login_file = 'login_data.json'
        self.client = Client()


    def login(self):
        # Check if login data is available in the file
        if os.path.exists(self.login_file):
            with open(self.login_file, 'r') as file:
                data = json.load(file)
                self.sessionId = data.get('sessionId')
                self.profileId = data.get('profileId')
                self.authToken = data.get('authToken')
                self.xmppToken = data.get('xmppToken')
                self.logged_in = True
                logging.info("Session loaded")
                return

        logging.info("No session data found, logging in...")
        email = input("Email: ")
        password = input("Password: ")

        # Proceed with the login process
        response = self.client.post(
            SESSIONS, {"email": email, "password": password, "token": ""}
        )
        if 'code' in response and response['code'] == 30:
            logging.error("You need to verify your account via phone number!")
            exit(-1)

        self.sessionId = response.get("sessionId")
        self.profileId = response.get("profileId")
        self.authToken = response.get("authToken")
        self.xmppToken = response.get("xmppToken")

        # Save the session data
        with open(self.login_file, 'w') as file:
            json.dump({
                'sessionId': self.sessionId,
                'profileId': self.profileId,
                'authToken': self.authToken,
                'xmppToken': self.xmppToken
            }, file)

        self.logged_in = True


    def getProfiles(self, lat, lon):
        assert(self.logged_in)

        params = {
            "nearbyGeoHash": to_geohash(lat, lon),
            "onlineOnly": "false",
            "photoOnly": "false",
            "faceOnly": "false",
            "notRecentlyChatted": "false",
            "fresh": "false",
            "pageNumber": "1",
            "rightNow": "false",
        }

        response = self.client.get(GET_USERS, params, auth_token=self.sessionId)
        return response


    def getTaps(self):
        assert(self.logged_in)

        response = self.client.get(TAPS_RECIEVED, {}, auth_token=self.sessionId)
        return response


    # type is a number from 1 - ?
    def tap(self, profileId, type):
        assert(self.logged_in)

        response = self.client.post(
            TAP, {"recipientId": profileId, "tapType": type}, auth_token=self.sessionId
        )
        return response


    def getProfile(self, profileId):
        assert(self.logged_in)

        response = self.client.get(GET_PROFILE + profileId, {}, auth_token=self.sessionId)
        return response


    def getUserProperty(self, profileId: str, property: str):
        assert(self.logged_in)

        profile = self.getProfile(profileId)
        profiles = profile.get('profiles', [])

        if profiles:
            first_profile = profiles[0]
            val = first_profile.get(property)
            logging.debug(f"{property}: {val}")
            return val
        else:
            logging.error("No profiles found")
            return None


    # profileIdList MUST be an array of profile ids
    def getProfileStatuses(self, profileIdList):
        assert(self.logged_in)

        response = self.client.post(
            STATUS, {"profileIdList": profileIdList}, auth_token=self.sessionId
        )
        return response


    def getAlbum(self, profileId):
        assert(self.logged_in)

        response = self.client.post(
            ALBUM, {"profileId": profileId}, auth_token=self.sessionId
        )
        return response


    #returns session data (might renew it)
    def sessions(self, email):
        assert(self.logged_in)

        response = self.client.post(
            SESSIONS,
            {"email": email, "token": "", "authToken": self.authToken},
            auth_token=self.sessionId,
        )

        self.sessionId = response["sessionId"]
        self.profileId = response["profileId"]
        self.authToken = response["authToken"]
        self.xmppToken = response["xmppToken"]

        return response


    # generating plain auth
    def generatePlainAuth(self):
        assert(self.logged_in)

        auth = self.profileId + "@chat.grindr.com" + "\00" + self.profileId + "\00" + self.xmppToken
        _hex = binascii.b2a_base64(str.encode(auth), newline=False)
        _hex = str(_hex)
        _hex = _hex.replace("b'", "").replace("'", "")
        return _hex
