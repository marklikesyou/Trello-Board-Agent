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
            raise ValueError("Missing API credentials. have a look at env file =)")
        
        self.client = TrelloClient(
            api_key=self.api_key,
            api_secret=None,  
            token=self.token,
            token_secret=None  
        )
        
        self.llm = ChatOpenAI(
            temperature=0,
            model="gpt-4o-mini",  # feel free to change
            model_kwargs={"top_p": 0.9}  
        )
        self.parser = PydanticOutputParser(pydantic_object=TrelloBoard)
        
        template = """Create a Trello board structure for this project description:
{project_description}

Create a board with these lists in order:
1. Backlog: Place all initial tasks and future enhancements here
2. To Do: Only include immediate, ready-to-start tasks
3. In Progress: Leave empty (for tasks that are being worked on)
4. Review: Leave empty (for tasks pending review)
5. Done: Leave empty (for completed tasks)

Break down the project into specific, actionable tasks and place them in either Backlog or To Do.
Place larger, future tasks in Backlog.
Place smaller, immediate tasks in To Do.
Leave other lists empty as they will be used during project execution.
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
                
                #board creation
                board = self.client.add_board(
                    board_name=board_structure.name,
                    permission_level='private',
                    default_lists=False  
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
                            added_labels = set()  
                            for label_name in card_info.labels:
                                if label_name not in added_labels:  
                                    label_color = label_name if label_name in label_colors else 'blue'
                                    if label_color not in labels:
                                        labels[label_color] = board.add_label(label_name, label_color)
                                    try:
                                        card.add_label(labels[label_color])
                                        added_labels.add(label_name)
                                    except Exception as e:
                                        if "already on the card" not in str(e):
                                            raise
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
            print("note: no boards listed. this isn't an issue. just a side effect of the trello api")
            return []
