from grindr.xmpp import Chatter
import logging

if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s %(message)s", datefmt="%m/%d/%Y %I:%M:%S", level=logging.DEBUG
    )

    chatter = Chatter()
    chatter.login()
    chatter.connect()
