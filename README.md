# Trello Board AI Agent

This project implements an AI agent that automatically creates and organizes Trello boards based on natural language prompts. It uses the official Trello API and LangChain for AI capabilities.

## Features

- Creates Trello boards from natural language project descriptions
- Automatically organizes tasks into appropriate lists:
  - Backlog: For larger, future tasks and enhancements
  - To Do: For immediate, ready-to-start tasks
  - In Progress: For active tasks
  - Review: For tasks pending review
  - Done: For completed tasks
- Smart task distribution: Initially places tasks only in Backlog and To Do
- Automatic label creation and assignment
- No default Trello lists - clean board creation
- Error handling for API rate limits and duplicate labels

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

# Initialize the agent
agent = TrelloAgent()

# Example project description
project_description = """
Create a website for a local restaurant with the following features:
- Modern, responsive design
- Online menu with photos
- Table reservation system
- Contact form
- Integration with food delivery platforms
"""

# Create the board
board_url = agent.create_board(project_description)
print(f"Board created: {board_url}")
```

## Board Structure

The agent creates a clean board with five lists:
1. **Backlog**: Contains larger tasks and future enhancements
2. **To Do**: Contains immediate, actionable tasks
3. **In Progress**: Empty by default, for tracking active work
4. **Review**: Empty by default, for tasks needing review
5. **Done**: Empty by default, for completed tasks

Tasks are initially distributed only between Backlog and To Do based on their scope and immediacy.
