from openai import OpenAI
from utils import contains_image_url, strip_urls
import logging

class OpenAIModel(OpenAI):
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    def text(self, conversation) -> str:
        completion = super().chat.completions.create(
            model=self.model,
            messages=conversation,
        )
        return completion.choices[0].message.content
    
    def image(self, prompt: str, image_size: str) -> str:
        response = super().image.create(
            prompt=prompt,
            n=1,
            size=image_size
        )
        image_url = response.data[0].url
        return image_url


class Conversation:
    user_id: str
    messages: list
    app: str

class OpenAIParser():
    def parse_message_body(self, text: str) -> list:
        messages = []
        image_urls = contains_image_url(text)
        if(image_urls.length > 0):
            for image_url in image_urls:
                messages.append(f'{"type":"image_url","image_url":{"url":{image_url}}}')
        
        text = strip_urls(text)
        messages.append(f'{"type":"text","text":{text}}')
        return messages


    def parse_messages(self, author: str, messages: list) -> str:
        if(len(messages) == 0):
            raise Exception('Empty messages')
        if author != 'user' and author != 'assistant' and author != 'system':
            raise Exception('Invalid author')
        messages = [self.parse_message_body(message) for message in messages]
        
        return f'{"role":{author},"content": {messages}}'
    

    def load_conversation(self, user_id: str, app: str) -> list:
        conversation: Conversation = {}
        try:
                with open(f"chats/{app}/{user_id}.txt", "r", encoding='utf-8') as file:
                    lines = file.readlines()
                    message_content = []

                    for line in lines:
                        line = line.strip()
                        if line.startswith("USER: "):
                            message_content = line[len("USER: "):]
                            conversation.messages.append({"role": "user", "content": message_content})
                        elif line.startswith("ASSISTANT: "):
                            message_content = line[len("ASSISTANT: "):]
                            conversation.messages.append({"role": "assistant", "content": message_content})
                        else:
                            continue
                conversation.user_id = user_id
                conversation.app = app
                return conversation
        except Exception as e:
            logging.debug(f"No previous conversation with userId {user_id}: error {e}")
            return None


    def save_conversation(self, profile: str, user_id: str, app: str, conversation: Conversation):
        try:
            with open(f"chats/{app}/{user_id}.txt", "w", encoding='utf-8') as file:
                file.write(f"SPEAKING TO: {profile}\n\n")
                for message in conversation.messages:
                    if message['role'] == 'user':
                        file.write(f"USER: {message['content']}\n")
                    elif message['role'] == 'assistant':
                        file.write(f"ASSISTANT: {message['content']}\n")
        except Exception as e:
            logging.error(f"Error saving conversation with userId {user_id}: error {e}")

class Chatter():
    def __init__(self, ai, parser, initial_description: str):
        self.ai = ai
        self.parser = parser
        self.initial_description = initial_description
        self.conversations =  []

    def load_conversation(self, app, user_id) -> Conversation:
        conversation = next((conversation for conversation in self.conversations if conversation.user_id == user_id and conversation.app == app), None)
        if conversation.messages.length == 0:
            # create new
            conversation = Conversation()
            conversation.user_id = user_id
            conversation.app = app
            conversation.messages = [
                self.parser.parse_messages('system', [self.initial_description])
            ]
            self.conversations.append(conversation)
        return conversation

    def read(self, app, user_id, msg):
        conversation: Conversation = self.load_conversation(app, user_id)

        # read msg
        conversation.messages.append(self.parser.parse_messages('user', [msg]))

        # save
        self.parser.save_conversation(app, user_id, conversation)

    def reply(self, app, user_id):
        conversation: Conversation = self.load_conversation(app, user_id)
        
        # reply to msg
        response = self.ai.text(conversation.messages)
        conversation.messages.append(self.parser.parse_messages('assistant', [response]))

        # save
        self.parser.save_conversation(app, user_id, conversation)
