
from __future__ import annotations
import pytest
from typing import Dict, Generator, Optional
from config.loader import load_settings
from utils.browser_manager import BrowserManager
from typing import Literal

BrowserName = Literal["chrome", "firefox", "edge"]

@pytest.fixture(scope="session")
def settings() -> Dict:
	return load_settings()


def _is_placeholder(url: str) -> bool:
	return not url or "example.com" in url


# Global browser manager instance
_browser_manager: Optional[BrowserManager] = None

@pytest.fixture(scope="session")
def browser_manager(settings: Dict) -> Generator[BrowserManager, None, None]:
	"""Create a single browser manager instance for the entire test session."""
	global _browser_manager
	
	if _browser_manager is None:
		_browser_manager = BrowserManager(settings)
		legacy_driver, modern_driver = _browser_manager.setup_browsers()
		
		# Navigate to initial URLs
		legacy_url = settings["envs"]["legacy"]["base_url"]
		modern_url = settings["envs"]["modern"]["base_url"]
		
		if _is_placeholder(legacy_url) or _is_placeholder(modern_url):
			pytest.skip("Configure framework/config/settings.yaml with real base_urls before running")
		
		legacy_driver.get(legacy_url)
		modern_driver.get(modern_url)
	
	yield _browser_manager
	
	# Cleanup
	if _browser_manager:
		try:
			_browser_manager.close_browsers()
		except Exception as e:
			print(f"Error closing browsers: {e}")
		finally:
			_browser_manager = None


@pytest.fixture(scope="session")
def legacy_driver(browser_manager: BrowserManager) -> Generator:
	"""Get legacy WebDriver from the shared browser manager."""
	legacy_driver, _ = browser_manager.setup_browsers()
	yield legacy_driver


@pytest.fixture(scope="session")
def modern_driver(browser_manager: BrowserManager) -> Generator:
	"""Get modern WebDriver from the shared browser manager."""
	_, modern_driver = browser_manager.setup_browsers()
	yield modern_driver