from .repositories import AgenticBrainRepository

class AgenticBrainService:
    """
    Handles LangChain/LangGraph automated decision-making workflows.
    Communicates with ML Engine and Products services.
    """
    def __init__(self):
        self.repository = AgenticBrainRepository()
