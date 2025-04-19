from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
import os

load_dotenv()
# set up apis
groq_api_key = os.getenv("GROQ_API_KEY")
groq_model = os.getenv("MODEL_Z")

# set up llm
groq = ChatGroq(model=groq_model,
                api_key=groq_api_key,
                temperature=0)

def planning_agent(state):
    """
    This function takes the user prompt and converts it into a list of steps
    that will be used to navigate the browser.

    Args: 
        state (dict): The current state containing messages and steps

    Returns:
        dict: Updated state with new messages and steps
    """
    messages = state["messages"]

    # set up system prompt
    system_prompt = """
    You are a helpful assistant that converts a user prompt into a list of steps that will be used to navigate the browser.
    The steps should be in numbered order and each step should be a single action.
    Your output will be going to another agent that controls the browser. 
    A step should be detailed without being super complex.
    Only output the steps, no other text.
    """

    # invoke groq with full message history
    response = groq.invoke([SystemMessage(content=system_prompt)] + [*messages])

    return {
        "messages": [AIMessage(content=response.content)],
        "steps": response.content
    }   