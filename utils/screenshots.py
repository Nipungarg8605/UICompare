from __future__ import annotations

import os
import time
from typing import Optional

from selenium.webdriver.remote.webdriver import WebDriver


def save_screenshot(driver: WebDriver, path: str) -> str:
	os.makedirs(os.path.dirname(path), exist_ok=True)
	driver.save_screenshot(path)
	return path


def save_named_screenshot(driver: WebDriver, directory: str, name_prefix: str) -> str:
	timestamp = time.strftime("%Y%m%d-%H%M%S")
	filename = f"{name_prefix}-{timestamp}.png"
	path = os.path.join(directory, filename)
	return save_screenshot(driver, path)
