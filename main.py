import gradio as gr

def run_agent(prompt):
    # temp output
    return f">> Agent received prompt:\n{prompt}\n\n>> Navigating...\n>> Auth complete.\n>> Task finished!"

with gr.Blocks() as interface:
    with gr.Row():
        # left col
        with gr.Column(scale=1):
            gr.Markdown("### Enter Prompt")
            prompt_input = gr.Textbox(lines=2, placeholder="e.g., Login to Canvas...", label="Prompt")

            submit_btn = gr.Button("Run Agent")

            gr.Markdown("### Agent Steps")
            agent_logs = gr.Textbox(label="Browser Agent Output", lines=20, interactive=False)

        # right col
        with gr.Column(scale=2):
            gr.Markdown("### Browser View")
            gr.HTML("<iframe src='http://localhost:6080/vnc_auto.html' width='100%' height='700px'></iframe>")

    submit_btn.click(fn=run_agent, inputs=prompt_input, outputs=agent_logs)

interface.launch()
