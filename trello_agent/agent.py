import os
import time
from typing import List, Dict, Optional
from dotenv import load_dotenv
from trello import TrelloClient
from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from pydantic import BaseModel, Field
from openai import RateLimitError

load_dotenv()

class TrelloCard(BaseModel):
    title: str = Field(description="Title of the card")
    description: str = Field(description="Detailed description of the card")
    members: Optional[List[str]] = Field(default=None, description="List of member IDs to assign to the card")
    labels: Optional[List[str]] = Field(default=None, description="List of label colors or names")

class TrelloList(BaseModel):
    name: str = Field(description="Name of the list")
    cards: List[TrelloCard] = Field(description="List of cards in this list")

class TrelloBoard(BaseModel):
    name: str = Field(description="Name of the board")
    description: str = Field(description="Description of the board")
    lists: List[TrelloList] = Field(description="Lists to create in the board")

class TrelloAgent:
    def __init__(self):
        self.api_key = os.getenv('TRELLO_API_KEY')
        self.token = os.getenv('TRELLO_TOKEN')
        
        if not self.api_key or not self.token:
            raise ValueError("Missing Trello API credentials. Please set TRELLO_API_KEY and TRELLO_TOKEN in .env file")
        
        self.client = TrelloClient(
            api_key=self.api_key,
            api_secret=None,  
            token=self.token,
            token_secret=None  
        )
        
        self.llm = ChatOpenAI(temperature=0)
        self.parser = PydanticOutputParser(pydantic_object=TrelloBoard)
        
        template = """Create a Trello board structure for this project description:
{project_description}

Create a board with these lists: Backlog, To Do, In Progress, Review, Done.
Break down the project into specific, actionable tasks.
Add relevant labels to categorize tasks (e.g., feature, bug, docs).

{format_instructions}"""

        self.prompt = PromptTemplate(
            template=template,
            input_variables=["project_description"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )

    def create_board(self, project_description: str) -> str:
        max_retries = 3
        retry_delay = 5  
        
        for attempt in range(max_retries):
            try:
                prompt_value = self.prompt.format(project_description=project_description)
                board_structure = self.parser.parse(self.llm.invoke(prompt_value).content)
                
                board = self.client.add_board(
                    board_name=board_structure.name,
                    permission_level='private' 
                )
                
                board.set_description(board_structure.description)

                label_colors = ['green', 'yellow', 'orange', 'red', 'purple', 'blue']
                labels = {}
                
                for list_info in board_structure.lists:
                    trello_list = board.add_list(list_info.name)
                    
                    for card_info in list_info.cards:
                        card = trello_list.add_card(
                            name=card_info.title,
                            desc=card_info.description
                        )
                        
                        if card_info.labels:
                            for label_name in card_info.labels:
                                label_color = label_name if label_name in label_colors else 'blue'
                                if label_color not in labels:
                                    labels[label_color] = board.add_label(label_name, label_color)
                                card.add_label(labels[label_color])
                        
                        if card_info.members:
                            for member_id in card_info.members:
                                card.add_member(member_id)
                
                return board.url
                
            except RateLimitError:
                if attempt < max_retries - 1:
                    print(f"Rate limit hit, retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  
                else:
                    raise
            except Exception as e:
                raise Exception(f"Failed to create board: {str(e)}")

    def add_list(self, board_id: str, name: str) -> str:
        board = self.client.get_board(board_id)
        trello_list = board.add_list(name)
        return trello_list.id

    def add_card(self, list_id: str, title: str, description: str) -> str:
        trello_list = self.client.get_list(list_id)
        card = trello_list.add_card(name=title, desc=description)
        return card.id

    def get_boards(self) -> List[Dict]:
        try:
            boards = self.client.list_boards()
            return [{'id': board.id, 'name': board.name, 'url': board.url} for board in boards]
        except Exception as e:
            print("Note: Unable to list boards. This doesn't affect board creation.")
            return []
