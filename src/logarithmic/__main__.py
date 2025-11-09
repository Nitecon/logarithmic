"""Main entry point for the Logarithmic application."""

import logging
import sys

from PySide6.QtWidgets import QApplication

from logarithmic.main_window import MainWindow


def main() -> int:
    """Run the Logarithmic application.
    
    Returns:
        Exit code
    """
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Logarithmic application")
    
    app = QApplication(sys.argv)
    app.setApplicationName("Logarithmic")
    app.setOrganizationName("Logarithmic")
    
    window = MainWindow()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
