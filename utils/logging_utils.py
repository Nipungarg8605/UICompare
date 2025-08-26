import logging
from typing import Iterable


def get_logger(name: str = "ui_compare") -> logging.Logger:
	logger = logging.getLogger(name)
	if not logger.handlers:
		# Handler will be managed by pytest's log_cli; avoid duplicate handlers
		logger.propagate = True
	logger.setLevel(logging.INFO)
	return logger
