from __future__ import annotations

from typing import Callable, Optional

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def wait_for_visible(driver: WebDriver, locator: tuple[str, str], timeout_seconds: int = 20):
	return WebDriverWait(driver, timeout_seconds).until(EC.visibility_of_element_located(locator))


def wait_for_present(driver: WebDriver, locator: tuple[str, str], timeout_seconds: int = 20):
	return WebDriverWait(driver, timeout_seconds).until(EC.presence_of_element_located(locator))


def wait_until(driver: WebDriver, condition_fn: Callable[[WebDriver], bool], timeout_seconds: int = 20):
	return WebDriverWait(driver, timeout_seconds).until(lambda d: condition_fn(d))
