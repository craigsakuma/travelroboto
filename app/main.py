"""
Main entrypoint for the Chatbot Application.

This module provides a command-line interface for launching different types of
user interfaces for the chatbot application. It demonstrates a flexible architecture 
that supports multiple front-end interfaces, including:

    - FastAPI-based web interface (default)
    - Legacy Gradio-based web interface (for rapid prototyping)

The application structure is designed for scalability and modularity:
    - Each interface implementation resides in its own module
    - The interface selection is determined at runtime using CLI arguments
    - Additional interfaces (e.g., SMS, mobile, voice) can be easily integrated

Example usage:
    Launch default FastAPI interface:
        $ python -m app.main

    Launch legacy Gradio interface:
        $ python -m app.main --interface gradio
"""

import argparse
import uvicorn
from app.interfaces.fastapi_web_ui import create_app
from app.interfaces.legacy_gradio_web_ui import launch_web_ui


def run_fastapi_web_ui() -> None:
    """
    Launch the FastAPI-based web interface.

    This interface uses FastAPI to provide a scalable, production-ready
    HTTP server with REST endpoints and a Jinja2-powered HTML front-end.
    """
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)


def run_gradio_web_ui() -> None:
    """
    Launch the legacy Gradio-based web interface.

    This interface was originally used for rapid prototyping and provides
    a lightweight way to interact with the chatbot using Gradio's simple
    web UI components.
    """
    launch_web_ui()


def parse_and_run() -> None:
    """
    Parse command-line arguments and launch the selected interface.

    This function supports future expansion of interfaces beyond web,
    such as SMS, mobile, or voice. The selection mechanism keeps the
    main entrypoint clean and readable.
    """
    parser = argparse.ArgumentParser(
        description="Choose which chatbot interface to launch."
    )
    parser.add_argument(
        "--interface",
        choices=["fastapi", "gradio"],
        default="fastapi",
        help="Select which interface to run: fastapi (default) or gradio",
    )
    args = parser.parse_args()

    if args.interface == "fastapi":
        run_fastapi_web_ui()
    elif args.interface == "gradio":
        run_gradio_web_ui()


if __name__ == "__main__":
    # Main execution path:
    # Delegates interface selection and launching to parse_and_run()
    parse_and_run()
