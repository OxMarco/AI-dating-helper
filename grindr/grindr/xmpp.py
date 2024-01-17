import socket
import ssl
import xml.etree.ElementTree as ET
import json
import uuid
import time
import random
import logging
import threading
import queue
import os
from openai import OpenAI
from grindr.user import User
from grindr.utils import calculate_sleep_time

class Chatter(User):
    def __init__(self):
        User.__init__(self)
        random.seed()
        self.plainAuth = None
        self.h_value = 0
        self.hostname = 'chat.grindr.com'
        self.secure_sock = None
        self.stop_event = threading.Event()
        self.socket_lock = threading.Lock()
        self.send_lock = threading.Lock()
        self.conversations_lock = threading.Lock()
        api_key = os.environ.get('API_KEY')
        if api_key is None:
            print("Invalid OpenAI api key")
            exit(-1)
        self.openai = OpenAI(
            api_key=api_key,
        )
        self.conversations = {}
        self.conversation_queues = {}
        self.reader_thread = None
        self.message_threads = []


    def getProfileInfo(self, profile):
        intro = "You are talking to a guy"
        if profile:
            if profile['displayName']:
                intro += f" called {profile['displayName']}"

            if profile['age']:
                intro += f" who is {str(profile['age'])} years old"
            
            if profile['aboutMe']:
                intro += f" and who describes himself as: {profile['aboutMe']}"

        logging.debug(intro)
        return intro


    def send_chat_location_message(self, to_id: str, lat: float, lon: float):
        self.send_chat_message(to_id, f'{{"lat":{lat},"lon":{lon}}}', 'map')


    def send_chat_image_message(self, to_id: str, height: int, width: int, image_hash: str):
        self.send_chat_message(to_id, f'{{"height":{height},"imageHash":"{image_hash}","width":{width},"imageType":0}}', 'image')


    def send_chat_message(self, to_id, msg, type='text'):
        with self.send_lock:
            message_id = str(uuid.uuid4()).upper()
            timestamp = int(time.time() * 1000)
            body_content = {
                "sourceProfileId": self.profileId,
                "messageContext": "chat,inbox,false",
                "targetProfileId": to_id,
                "messageId": message_id,
                "countryCode": ["GB"],
                "body": msg,
                "timestamp": timestamp,
                "type": type
            }
            body = json.dumps(body_content)

            message = f"""
            <message to='{to_id}@chat.grindr.com' from='{self.profileId}@chat.grindr.com' type='chat' id='{message_id}'>
                <body>{body}</body>
            </message><r xmlns='urn:xmpp:sm:3'/>
            """

            # Send the message
            try:
                with self.socket_lock:
                    self.secure_sock.send(message.encode())
                    logging.debug("Message sent successfully")
            except Exception as e:
                logging.error(f"Error sending message: {e}")
                self.stop_event.set()


    def send_ack(self):
        with self.send_lock:
            ack_message = f"<a xmlns='urn:xmpp:sm:3' h='{self.h_value}'/>"
            try:
                with self.socket_lock:
                    self.secure_sock.send(ack_message.encode())
                    self.h_value += 1
            except Exception as e:
                logging.error(f"Error sending ACK: {e}")
                self.stop_event.set()


    def send_displayed(self, original_msg_id, to_id):
        with self.send_lock:
            message_id = str(uuid.uuid4()).upper()
            response_message_received = f"""
            <message from='{self.profileId}@chat.grindr.com' to='{to_id}@chat.grindr.com' xml:lang='en' type='chat' id='{message_id}'>
                <received xmlns='urn:xmpp:chat-markers:0' id='{original_msg_id}'/>
            </message>
            """

            time.sleep(0.2)

            message_id = str(uuid.uuid4()).upper()
            response_message_displayed = f"""
            <message from='{self.profileId}@chat.grindr.com' to='{to_id}@chat.grindr.com' xml:lang='en' type='chat' id='{message_id}'>
                <displayed xmlns='urn:xmpp:chat-markers:0' id='{original_msg_id}'/>
            </message>
            """

            try:
                with self.socket_lock:
                    self.secure_sock.send(response_message_received.encode())
            except Exception as e:
                logging.error(f"Error sending message received response: {e}")
                self.stop_event.set()

            time.sleep(0.3)

            try:
                with self.socket_lock:
                    self.secure_sock.send(response_message_displayed.encode())
            except Exception as e:
                logging.error(f"Error sending message displayed response: {e}")
                self.stop_event.set()


    def parse_chat_message(self, xml_message):
        try:            
            # Parse only the <message> element
            root = ET.fromstring(xml_message)
            body_content = root.find('body')
            if body_content is not None:
                body_content = body_content.text
                decoded_json = json.loads(body_content.replace('&quot;', '"'))
                return decoded_json
            
            if xml_message.count("<active") == 0:
                logging.info("Someone viewed your profile")
                return None
            
            if xml_message.count("<composing") == 0:
                logging.info("Someone is typing you a message")
                return None
            
            if xml_message.count("<paused") == 0:
                logging.info("Someone stopped typing you a message")
                return None

        except ET.ParseError as e:
            logging.error(f"XML Parsing Error: {e}")
            return None
        except json.JSONDecodeError as e:
            logging.error(f"JSON Decoding Error: {e}")
            return None
        

    def message_reader(self):
        logging.debug("Starting message reader thread")
        while not self.stop_event.is_set():
            try:
                    msgReceived = self.secure_sock.recv(2048)
                    if msgReceived:
                        msgReceived = msgReceived.decode()

                        if msgReceived.count("<error reason='not-authorized'/>") == 1:
                            logging.error("Need to login first")
                            self.stop_event.set()
                            break

                        # needs ack
                        if msgReceived.count("<r xmlns='urn:xmpp:sm:3'/>") == 1:
                            msgReceived = msgReceived.replace("<r xmlns='urn:xmpp:sm:3'/>", "")
                            self.send_ack()

                        # parse incoming msg, if not a chat msg, skip
                        if msgReceived.count("<message") == 0:
                            continue

                        messages = msgReceived.split('</message>')
                        full_message = messages[0] + '</message>'

                        received = self.parse_chat_message(full_message)
                        if received != None:
                            logging.info("--- Message Received ---")
                            logging.info(received)
                            logging.info("--- --- --- --- ---")
                            
                            self.send_displayed(received.get("messageId"), received.get("sourceProfileId"))               

                            sender_id = received.get('sourceProfileId')
                            profile = None

                            # Initialize queue if not exists
                            if sender_id not in self.conversation_queues:
                                logging.debug(f"Initializing queue and thread for {sender_id}")
                                self.conversation_queues[sender_id] = queue.Queue()
                                thread = threading.Thread(
                                    target=self.message_responder, args=(sender_id,)
                                )
                                thread.start()
                                self.message_threads.append(thread)

                                try:
                                    data = self.getProfile(sender_id)
                                    if data:
                                        profiles = data.get('profiles', [])
                                        if profiles:
                                            profile = profiles[0]
                                except Exception as e:
                                    logging.debug(f"Error getting profile for {sender_id}: {e}")

                            self.conversation_queues[sender_id].put(received)
                                
                            # Initialize conversation state if not exists
                            if sender_id not in self.conversations:
                                logging.debug(f"Initializing conversation state for {sender_id}")
                                self.conversations[sender_id] = [
                                        {"role": "system", "content": 
                                        "You are a human being"},
                                        {"role": "system", "content": self.getProfileInfo(profile)},
                                    ]
                                convo = self.load_chat(sender_id)
                                if convo:
                                    for message in convo:
                                        self.conversations[sender_id].append(message)
            except socket.timeout:
                # Timeout occurred, loop will recheck the stop event
                continue
            except socket.error as e:
                logging.error(f"Socket error in message reader: {e}")
                self.stop_event.set()
                break
            except Exception as e:
                logging.error(f"Error in message reader: {e}")
                self.stop_event.set()
                break
        logging.debug("Stopping message reader thread")


    def message_responder(self, sender_id):
        logging.debug(f"Starting message responder thread for {sender_id}")
        while not self.stop_event.is_set():
            messages = []
            response_msg = None
            while not self.conversation_queues[sender_id].empty():
                try:
                    msgReceived = self.conversation_queues[sender_id].get(timeout=1.0)
                    if msgReceived is None or msgReceived.get('type') != 'text':
                        logging.debug("Not a text message, skipping")
                        continue
                    messages.append(msgReceived.get('body'))
                    sleep_time = random.randrange(1, 3) # random sleep time to simulate a human
                    time.sleep(sleep_time)
                except queue.Empty:
                    break

            if messages:
                with self.conversations_lock:
                    for msg in messages:
                        self.conversations[sender_id].append({"role": "user", "content": msg})

                try:
                    completion = self.openai.chat.completions.create(
                        model="gpt-4",
                        messages=self.conversations[sender_id],
                    )
                    response_msg = completion.choices[0].message.content                        
                    if response_msg.count("SEND PHOTO") > 0:
                        self.send_chat_message(sender_id, "Better on insta")
                    else:
                        with self.conversations_lock:
                            # Add the model's response to the conversation state
                            self.conversations[sender_id].append({"role": "assistant", "content": response_msg})

                        logging.info(f"Scheduled response to \"{msg}\" with \"{response_msg}\"")
                        self.send_chat_message(sender_id, response_msg)
                except Exception as e:
                    logging.error(f"Error in handle_response for {sender_id}: {e}")


            self.save_chat(sender_id)
            if response_msg:
                sleep_time = calculate_sleep_time(response_msg)
            else:
                sleep_time = random.randrange(5, 60) # random sleep time to simulate a human
            time.sleep(sleep_time)
        logging.debug(f"Stopping message responder thread for {sender_id}")


    def load_chat(self, sender_id):
        chat = []
        try:
            with self.conversations_lock:
                with open(f"chats/{sender_id}.txt", "r", encoding='utf-8') as file:
                    lines = file.readlines()
                    message_content = []

                    for line in lines:
                        line = line.strip()
                        if line.startswith("USER: "):
                            message_content = line[len("USER: "):]
                            chat.append({"role": "user", "content": message_content})
                        elif line.startswith("ASSISTANT: "):
                            message_content = line[len("ASSISTANT: "):]
                            chat.append({"role": "assistant", "content": message_content})
                        else:
                            continue
                return chat
        except Exception as e:
            logging.debug(f"No previous conversation with sender_id {sender_id}")
            return None


    def save_chat(self, sender_id):
        try:
            if sender_id in self.conversations:
                with self.conversations_lock:
                    with open(f"chats/{sender_id}.txt", "w", encoding='utf-8') as file:
                        file.write(f"SPEAKING TO: {sender_id}\n\n")
                        for message in self.conversations[sender_id]:
                            if message['role'] == 'user':
                                file.write(f"USER: {message['content']}\n")
                            elif message['role'] == 'assistant':
                                file.write(f"ASSISTANT: {message['content']}\n")
            else:
                logging.debug(f"No previous conversation with sender_id {sender_id}")
        except Exception as e:
            logging.error(f"Error saving chat for {sender_id}: {e}")


    def connect(self):
        resource_id = os.environ.get('RESOURCE_ID')
        if resource_id is None:
            logging.error("Invalid resource_id value")
            exit(-1)

        self.plainAuth = self.generatePlainAuth()
        logging.debug("Connecting to XMPP server...")

        try:
            context = ssl.create_default_context()
            with socket.create_connection((self.hostname, 453)) as sock:
                with context.wrap_socket(sock, server_hostname=self.hostname) as secure_sock:
                    self.secure_sock = secure_sock  # Keep a reference to the secure socket
                    self.secure_sock.settimeout(1.0)
                    self.secure_sock.send(f"<session to='chat.grindr.com' auth_data='{self.plainAuth}' resource='{resource_id}' stream_management='true' carbons='true' compress='false'>".encode())

                    # Start reader and responder threads
                    self.reader_thread = threading.Thread(target=self.message_reader, daemon=True)
                    self.reader_thread.start()
                    self.reader_thread.join()
        except KeyboardInterrupt:
            logging.debug("Interrupt received, stopping threads")
            self.stop_event.set()
        finally:
            logging.debug("Cleaning up and exiting")
            for thread in self.message_threads:
                if thread.is_alive():
                    thread.join()
            if self.secure_sock:
                self.secure_sock.close()
