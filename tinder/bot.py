import asyncio
import tinder
import os

class Client(tinder.Client):
    teaser_ids = set()

    async def get_teasers(self):
        while True:
            teasers = await self.fetch_teasers()
            self.teaser_ids |= {teaser.id for teaser in teasers}
            await asyncio.sleep(60)

    async def get_recs(self):
        while True:
            users = await self.fetch_recs()
            print(f"fetched {len(users)} users")
            for user in users:
                profile = await self.fetch_user_profile(user.id)
                print(profile.birth_date)
            await asyncio.sleep(60)

    async def main(self):
        profile = await self.fetch_profile()
        print(profile.birth_date)
        #await asyncio.gather(self.get_teasers(), self.get_recs())


if __name__ == "__main__":
    client = Client()
    tinder_token = os.environ.get('TINDER_TOKEN')
    client.run(tinder_token)
    client.close()
