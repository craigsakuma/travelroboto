#!/usr/bin/env python3
"""
Main entry point for the Travel Itinerary SMS Chatbot API.

This app:
- Launches the Gradio UI
- Connects to LLM chains
"""

# Standard library
import base64
import json
import os
from pathlib import Path
from typing import Any, Dict, Literal, Optional

# Third-party
import gradio as gr
from dotenv import load_dotenv

# Local application
import app.config as config
import app.models as models
from app.services.llm_chains import (
    question_chain,
    ask_question,
    clear_memory
)

TEST_DATA_DIR = config.TEST_DATA_DIR

load_dotenv(dotenv_path=Path.home() / ".env")

# --- Gradio Interface ---
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
        outputs=[chat_display,user_input]
    )
    clear_btn.click(
        clear_memory, 
        outputs=[chat_display,user_input]        
    )


if __name__ == "__main__":
    demo.launch(share=True)
