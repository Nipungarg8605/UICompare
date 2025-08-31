"""
Browser management utilities for handling separate browser instances.
"""

from typing import Dict, Any, Optional, Tuple
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)


class BrowserManager:
    """Manages separate browser instances for legacy vs modern application comparison."""
    
    def __init__(self, settings: Dict[str, Any]):
        self.settings = settings
        self.browser_config = settings.get("browser_management", {})
        
        # Browser configuration
        self.browser_type = settings.get("browser", "chrome")
        self.headless = settings.get("headless", False)
        self.implicit_wait = settings.get("implicit_wait_seconds", 2)
        self.page_load_timeout = settings.get("page_load_timeout_seconds", 30)
        
        # Browser instances
        self.legacy_driver: Optional[WebDriver] = None
        self.modern_driver: Optional[WebDriver] = None
    
    def create_driver(self) -> WebDriver:
        """Create a new WebDriver instance."""
        if self.browser_type.lower() == "chrome":
            options = Options()
            
            if self.headless:
                options.add_argument("--headless")
            
            # Add options for better stability
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            
            # Add unique user data directory to prevent session conflicts
            import tempfile
            import os
            temp_dir = tempfile.mkdtemp(prefix="chrome_user_data_")
            options.add_argument(f"--user-data-dir={temp_dir}")
            options.add_argument("--no-first-run")
            options.add_argument("--no-default-browser-check")
            
            # Add options for better stability
            options.add_argument("--disable-web-security")
            options.add_argument("--allow-running-insecure-content")
            options.add_argument("--disable-features=VizDisplayCompositor")
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            
        else:
            raise ValueError(f"Unsupported browser type: {self.browser_type}")
        
        # Configure driver
        driver.implicitly_wait(self.implicit_wait)
        driver.set_page_load_timeout(self.page_load_timeout)
        
        return driver
    
    def setup_browsers(self) -> Tuple[WebDriver, WebDriver]:
        """Setup separate browser instances."""
        # Only setup browsers if they haven't been created yet
        if self.legacy_driver is None or self.modern_driver is None:
            return self._setup_separate_browsers()
        else:
            return self.legacy_driver, self.modern_driver
    

    
    def _setup_separate_browsers(self) -> Tuple[WebDriver, WebDriver]:
        """Setup separate browser instances."""
        logger.info("Setting up separate browsers for legacy and modern apps")
        
        self.legacy_driver = self.create_driver()
        self.modern_driver = self.create_driver()
        
        return self.legacy_driver, self.modern_driver
    
    def navigate_to_page(self, legacy_url: str, modern_url: str) -> None:
        """Navigate both browsers to their respective URLs."""
        self._navigate_separate_browsers(legacy_url, modern_url)
    

    
    def _navigate_separate_browsers(self, legacy_url: str, modern_url: str) -> None:
        """Navigate separate browsers."""
        self.legacy_driver.get(legacy_url)
        self.modern_driver.get(modern_url)
        
        logger.info(f"Navigated legacy browser to: {legacy_url}")
        logger.info(f"Navigated modern browser to: {modern_url}")
    

    

    
    def get_legacy_driver(self) -> WebDriver:
        """Get the legacy browser driver."""
        return self.legacy_driver
    
    def get_modern_driver(self) -> WebDriver:
        """Get the modern browser driver."""
        return self.modern_driver
    
    def close_browsers(self) -> None:
        """Close all browser instances."""
        try:
            if self.legacy_driver:
                self.legacy_driver.quit()
                logger.info("Closed legacy browser instance")
            if self.modern_driver:
                self.modern_driver.quit()
                logger.info("Closed modern browser instance")
        except Exception as e:
            logger.error(f"Error closing browsers: {e}")
    
    def cleanup(self) -> None:
        """Cleanup method for compatibility with test scripts."""
        self.close_browsers()
        # Reset driver references
        self.legacy_driver = None
        self.modern_driver = None
        logger.info("Browser manager cleanup completed")
    
    def get_browser_info(self) -> Dict[str, Any]:
        """Get information about the current browser setup."""
        info = {
            "mode": "separate_browsers",
            "browser_type": self.browser_type,
            "headless": self.headless
        }
        
        return info

