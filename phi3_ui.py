"""Entry point for the phi3 UI application."""

from src.app import build_app


if __name__ == "__main__":
    app = build_app()
    app.launch(server_name="0.0.0.0", server_port=7860, inbrowser=False)
