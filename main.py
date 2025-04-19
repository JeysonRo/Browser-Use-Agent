import gradio as gr
from agents.planning_agent import planning_agent
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from typing import Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage


class State(TypedDict):
    messages: Annotated[list, add_messages]
    steps: str


def initialize_graph():
    # initialize graph
    graph_builder = StateGraph(State)

    # add nodes
    graph_builder.add_node("planning_agent", planning_agent)

    # add edges
    graph_builder.add_edge(START, "planning_agent")
    graph_builder.add_edge("planning_agent", END)

    # compile graph
    memory = MemorySaver()
    graph = graph_builder.compile(checkpointer=memory)

    return graph


def invoke_prompt(prompt):
    # initialize the state with the prompt
    initial_state = {
        "messages": [HumanMessage(content=prompt)],
        "steps": ""
    }
    
    # invoke the graph with the initial state
    output = graph.invoke(initial_state, config)
    # print(output["steps"])
    # return the steps from the output
    return output["steps"]


def gradio_setup():
    with gr.Blocks() as interface:
        with gr.Row():
            # left col
            with gr.Column(scale=1):
                gr.Markdown("### Enter Prompt")
                prompt_input = gr.Textbox(lines=2, placeholder="e.g., Login to Canvas...", label="Prompt")

                submit_btn = gr.Button("Run Agent")

                gr.Markdown("### Agent Steps")
                agent_logs = gr.Textbox(label="Browser Agent Output", lines=16, interactive=False)

            # right col
            with gr.Column(scale=3):
                gr.Markdown("### Browser View")
                gr.HTML("<iframe src='http://localhost:6080/vnc_auto.html' width='1056px' height='600px'></iframe>")

        submit_btn.click(fn=invoke_prompt, inputs=prompt_input, outputs=agent_logs)
    interface.launch()


# main
if __name__ == "__main__":
    graph = initialize_graph() #initialize graph
    config = {"configurable": {"thread_id": "browser_use"}} # define config
    gradio_setup() # set up gradio interface


