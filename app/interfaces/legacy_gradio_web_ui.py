"""
Gradio Web UI for TravelBot
"""
import gradio as gr
from app.chatbot.llm_chains import clear_memory
from app.chatbot.conversation import get_chat_response

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
            get_chat_response,
            inputs=user_input,
            outputs=chat_display
        )
        user_input.submit(
            get_chat_response,
            inputs=user_input,
            outputs=[chat_display, user_input]
        )
        clear_btn.click(
            clear_memory,
            outputs=[chat_display, user_input]
        )

    demo.launch(share=share)
