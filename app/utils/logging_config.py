import logging
import sys

def setup_logging():
    """Configure logging for the application."""
    # Force UTF-8 for stdout on Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('agentic_ai.log', encoding='utf-8')
        ]
    )
    return logging.getLogger(__name__)
