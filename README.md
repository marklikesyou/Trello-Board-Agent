# Trello Board AI Agent

This project implements an AI agent that automatically creates and organizes Trello boards based on natural language prompts. It uses the official Trello API and LangChain for AI capabilities.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your credentials:
```
TRELLO_API_KEY=your_api_key
TRELLO_TOKEN=your_token
OPENAI_API_KEY=your_openai_key
```

3. Get your Trello API credentials:
   - Visit https://trello.com/app-key to get your API key
   - Generate a token at https://trello.com/1/authorize?expiration=never&name=MyApp&scope=read,write&response_type=token&key=YOUR_API_KEY

## Usage

```python
from trello_agent import TrelloAgent

agent = TrelloAgent()
agent.create_board("Create a project management board for a website development project")
```
