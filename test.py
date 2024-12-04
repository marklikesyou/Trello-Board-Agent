from trello_agent import TrelloAgent

def test_trello_agent():
    agent = TrelloAgent()
    
    #mockup description
    project_description = """
    Create a website for a local restaurant with the following features:
    - Modern, responsive design
    - Online menu with photos
    - Table reservation system
    - Contact form
    - Integration with food delivery platforms
    """
    
    try:
        #board creation begins here
        board_url = agent.create_board(project_description)
        print(f"Successfully created board! You can view it at: {board_url}")
        
        print("\nYour boards:")
        boards = agent.get_boards()
        for board in boards:
            print(f"- {board['name']}: {board['url']}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_trello_agent()
