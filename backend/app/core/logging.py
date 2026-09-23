import logging
import sys


def configure_logging() -> None:
    root = logging.getLogger()
    if root.handlers:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    )
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    # Silencia logs verbosos de bibliotecas de terceiros com dados potencialmente sensíveis.
    logging.getLogger("passlib").setLevel(logging.ERROR)


logger = logging.getLogger("nexfi")
