import gradio as gr
from agents.planning_agent import planning_agent
from agents.browser_agent import browser_agent
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from typing import Annotated, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get available models from .env
def get_available_models():
    models = []
    for key in os.environ:
        if key.startswith("MODEL_"):
            model_name = key[6:]  # Remove "MODEL_" prefix
            model_value = os.environ[key]
            models.append((model_name, key))
    return models

class State(TypedDict):
    messages: Annotated[list, add_messages]
    steps: str
    credentials: Optional[dict]
    model: Optional[str]


def initialize_graph():
    # initialize graph
    graph_builder = StateGraph(State)

    # add nodes
    graph_builder.add_node("planning_agent", planning_agent)
    graph_builder.add_node("browser_agent", browser_agent)

    # add edges
    graph_builder.add_edge(START, "planning_agent")
    graph_builder.add_edge("planning_agent", "browser_agent")
    graph_builder.add_edge("browser_agent", END)

    # compile graph
    memory = MemorySaver()
    graph = graph_builder.compile(checkpointer=memory)

    return graph


def invoke_prompt(prompt, username=None, password=None, credentials_enabled=False, model_key=None):
    # initialize the state with the prompt
    initial_state = {
        "messages": [HumanMessage(content=prompt)],
        "steps": "",
        "credentials": None,
        "model": model_key
    }
    
    # Add credentials only if enabled and provided
    if credentials_enabled and username and password:
        initial_state["credentials"] = {
            "username": username,
            "password": password
        }
    
    # Get available models
    if model_key:
        # Update environment variable to the selected model
        os.environ["MODEL_SELECTED"] = os.environ.get(model_key, "")
    
    # invoke the graph with the initial state
    output = graph.invoke(initial_state, config)
    # print(output["steps"])
    # return the steps from the output
    return output["steps"]


def gradio_setup():
    # Get available models
    available_models = get_available_models()
    
    with gr.Blocks() as interface:
        with gr.Row():
            # left col
            with gr.Column(scale=1):
                gr.Markdown("### Enter Prompt")
                prompt_input = gr.Textbox(lines=2, placeholder="e.g., Login to Canvas...", label="Prompt")
                
                with gr.Accordion("Model & Credentials Settings", open=True):
                    # Model selection
                    model_choices = [(name.replace("_", " "), key) for name, key in available_models]
                    model_dropdown = gr.Dropdown(
                        choices=model_choices,
                        label="Select LLM Model",
                        value=model_choices[0][1] if model_choices else None
                    )
                    
                    # Credentials section
                    credentials_enabled = gr.Checkbox(label="Use secure credentials", value=False)
                    username_input = gr.Textbox(label="Username", placeholder="Your username", visible=True)
                    password_input = gr.Textbox(label="Password", placeholder="Your password", type="password", visible=True)
                    gr.Markdown("""
                    **Security Note:** 
                    - Credentials are only used for the current session and are not stored
                    - They are passed securely to the browser agent
                    - For maximum security, avoid using your real credentials
                    """)

                submit_btn = gr.Button("Run Agent")

                gr.Markdown("### Agent Steps")
                agent_logs = gr.Textbox(label="Browser Agent Output", lines=16, interactive=False)

            # right col
            with gr.Column(scale=3):
                gr.Markdown("### Browser Information")
                gr.Markdown("""
                **Note:** Since you're running this locally (not in Docker):
                
                1. A Chrome browser window will open automatically when you run an agent task
                2. You'll see the automation happen in that separate window 
                3. The window will close when the task is complete
                4. Detailed logs will appear in the left panel
                
                To see the browser in this iframe instead, use the Docker setup.
                """)
                
                # Keep iframe for future Docker usage
                gr.HTML("<iframe src='http://localhost:6080/vnc_auto.html' width='1056px' height='600px' style='opacity:0.5'></iframe>")

        # Connect the credentials checkbox to show/hide the credential inputs
        credentials_enabled.change(
            fn=lambda x: [gr.update(visible=x), gr.update(visible=x)],
            inputs=[credentials_enabled],
            outputs=[username_input, password_input]
        )

        submit_btn.click(
            fn=invoke_prompt, 
            inputs=[prompt_input, username_input, password_input, credentials_enabled, model_dropdown],
            outputs=agent_logs
        )
    interface.launch()


# main
if __name__ == "__main__":
    graph = initialize_graph() #initialize graph
    config = {"configurable": {"thread_id": "browser_use"}} # define config
    gradio_setup() # set up gradio interface


