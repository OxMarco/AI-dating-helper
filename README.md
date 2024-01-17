![header](header.png)

<h1 align="center">Dating helper</h1>

<div align="center">
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![ChatGPT](https://img.shields.io/badge/chatGPT-74aa9c?style=for-the-badge&logo=openai&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-%234ea94b.svg?style=for-the-badge&logo=mongodb&logoColor=white)
</div>

> Step up your dating game with a sprinkle of AI. Supports both Tinder and Grindr.

This AI-driven wingman is your secret weapon in the tumultuous world of online dating; whether you're juggling multiple conversations or just struggling to come up with that perfect icebreaker, this AI helper has got your back! It's like having a Cyrano de Bergerac in your pocket, but instead of a poetic Frenchman, it's a super-smart algorithm that knows just what to say to keep the conversation going.

## Key features
* [x] AI-driven response generation
* [x] Seamless integration with Tinder and Grindr
* [x] Real-time messaging
* [x] Multi-threaded architecture to handle parallel conversations
* [ ] Adaptive ai

## Technical Overview

### Tinder Module
The Tinder module of this application simplifies the process of interacting with potential matches on Tinder. Here's a breakdown of its technical components:

- **Message Processing Loop**: The core of the Tinder module is a loop that continuously checks for new messages from matches where no reply has been sent yet. This loop ensures timely responses and helps maintain the flow of conversations.

- **AI-Driven Response Generation**: Upon receiving a new message, the content is fed into an AI model designed to understand context and generate human-like responses. This AI uses advanced natural language processing techniques to ensure that each message is contextually relevant and personalised.

- **Response Delivery**: Once the AI crafts a response, it is automatically sent back through Tinder's messaging system. This seamless integration maintains the continuity of the conversation.

### Grindr Module
Grindr's real-time chatting system presents unique challenges, addressed as follows:

- **Main Listening Thread**: The application starts a main thread that listens for incoming messages on Grindr. This thread is responsible for identifying new conversations and messages.

- **Daemon Threads for Conversations**: For each active conversation, a daemon thread is spawned. These threads handle messages in parallel, ensuring real-time responses across multiple chats.

- **Human-like Interaction**: To mimic human behavior, the application includes waiting times before sending responses. These delays are proportional to the length of the generated message, adding to the authenticity of the interaction.

- **Acknowledgments (ACKs)**: The system sends read receipts (ACKs) to Grindr's server, indicating that the messages have been read, further mimicking human behavior.

### Notes on AI Integration
The AI component in both modules is the heart of the application. It utilises a blend of machine learning algorithms and natural language processing techniques to understand and respond to messages. The AI is trained on a diverse dataset, allowing it to handle a wide range of conversation topics and styles. 

### Example of AI Response Generation
Here's a simple example to illustrate how AI generates a response:

1. **Input Message**: "Hey, I noticed you like hiking. Have you visited any cool trails lately?"
2. **AI Processing**: The AI analyses key terms ("hiking", "visited", "trails") and the friendly tone.
3. **Generated Response**: "Hi! Yes, I recently explored the Blue Ridge Mountains. The trails there are breathtaking. How about you? Any favorite hiking spots?"

### macOS Users - Installation Note
For macOS users, specific steps are required to ensure compatibility when installing the SSL library for `pycurl`. This command can help install the correct backend for pycurl

> Notice: users should adjust the openssl library version and path to match their local setup.

```bash
env PYCURL_SSL_LIBRARY=openssl 
LDFLAGS="-L/opt/homebrew/Cellar/openssl@3/3.2.0_1/lib" 
CPPFLAGS="-I/opt/homebrew/Cellar/openssl@3/3.2.0_1/include" pip install 
--no-cache-dir --compile --ignore-installed pycurl
```

## Disclamer
This project, including its code and concepts, is presented as a funny PoC and is intended for educational and demonstrative purposes only. Users of this software are strongly advised against employing it in a manner that deceives or misleads other individuals on any dating platforms, including Tinder and Grindr users.


