from tinder.tinder import TinderAPI
import os

class Tinder():
    def __init__(self):
        tinder_token = os.environ.get('TINDER_TOKEN')
        if tinder_token is None:
            print("Invalid token")
            exit(-1)
        self.tinder_api = TinderAPI(tinder_token)
        self.profile = self.tinder_api.profile()

    def get_profile_intro(self, match) -> str:
        profile = match.person.infos()
        intro = f"You are talking to {profile['name']}, a {profile['age']} years old {profile['gender']}."
            
        if(profile['gender'] == 'Male'):
            pronoum = "He "
        elif(profile['gender'] == 'Female'):
            pronoum = "She"
        else:
            pronoum = "They (ungendered)"

        if(profile['bio']):
            intro += f"{pronoum} describes themselves as: {profile['bio']}."

        if(profile['city']):
            intro += f"{pronoum} is from {profile['city']}."

        if profile['distance'] > 0:
            intro += f"{pronoum} is {profile['distance']} kilometers away from you."

        if profile['jobs']:
            intro += f"{pronoum} works as: {profile['jobs']}."

        if profile['schools']:
            intro += f"{pronoum} studied at: {profile['schools']}."

        return intro

    def run(self):
        for match in self.tinder_api.matches(limit=50):
            #for image in match.person.images:
            #    print(image)
            chatroom = self.tinder_api.get_messages(match.match_id)
            latest_message = chatroom.get_lastest_message()
            if latest_message:
                if latest_message.from_id != self.profile.id:
                    # they sent the last message
                    print("They said:")
                    print(latest_message.message)
            else:
                # no messages sent yet
                intro = self.get_profile_intro(match)
                # give AI context on the person
                # intro
                

            #chatroom.send("Hey", user_id, match.person.id)

if __name__ == "__main__":
    tinder = Tinder()
    tinder.run()
