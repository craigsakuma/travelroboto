"""
Gradio Web UI for TravelBot
"""
import gradio as gr
from app.services.llm_chains import clear_memory
from app.utils.chat_helpers import ask_question

def launch_web_ui(share: bool = True):
    """Launch the Gradio web interface for TravelBot."""
    with gr.Blocks() as demo:
        gr.Markdown("## 📱 TravelBot (Prototype)")

        with gr.Row():
            chat_display = gr.Textbox(
                label="Conversation",
                interactive=False,
                value="",
                lines=15,
                elem_id="chat-history-box"
            )

        with gr.Row():
            user_input = gr.Textbox(label="Type your message")

        with gr.Row():
            send_btn = gr.Button("Send")
            clear_btn = gr.Button("Clear Memory")

        send_btn.click(
            ask_question,
            inputs=user_input,
            outputs=chat_display
        )
        user_input.submit(
            ask_question,
            inputs=user_input,
            outputs=[chat_display, user_input]
        )
        clear_btn.click(
            clear_memory,
            outputs=[chat_display, user_input]
        )

    demo.launch(share=share)
