"""
Browser management utilities for handling single browser with tabs vs separate browsers.
"""

from typing import Dict, Any, Optional, Tuple
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)


class BrowserManager:
    """Manages browser instances for legacy vs modern application comparison."""
    
    def __init__(self, settings: Dict[str, Any]):
        self.settings = settings
        self.browser_config = settings.get("browser_management", {})
        self.use_single_browser = self.browser_config.get("use_single_browser", False)
        self.tab_isolation = self.browser_config.get("tab_isolation", True)
        self.clear_state_between_tabs = self.browser_config.get("clear_state_between_tabs", True)
        self.tab_switch_delay = self.browser_config.get("tab_switch_delay", 0.5)
        
        # Browser configuration
        self.browser_type = settings.get("browser", "chrome")
        self.headless = settings.get("headless", False)
        self.implicit_wait = settings.get("implicit_wait_seconds", 2)
        self.page_load_timeout = settings.get("page_load_timeout_seconds", 30)
        
        # Browser instances
        self.shared_driver: Optional[WebDriver] = None
        self.legacy_driver: Optional[WebDriver] = None
        self.modern_driver: Optional[WebDriver] = None
        self.legacy_tab_handle: Optional[str] = None
        self.modern_tab_handle: Optional[str] = None
    
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
            
            # Add options for tab isolation if needed
            if self.tab_isolation:
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
        """Setup browser instances based on configuration."""
        # Only setup browsers if they haven't been created yet
        if self.use_single_browser:
            if self.shared_driver is None:
                return self._setup_single_browser()
            else:
                return self.shared_driver, self.shared_driver
        else:
            if self.legacy_driver is None or self.modern_driver is None:
                return self._setup_separate_browsers()
            else:
                return self.legacy_driver, self.modern_driver
    
    def _setup_single_browser(self) -> Tuple[WebDriver, WebDriver]:
        """Setup single browser with two tabs."""
        logger.info("Setting up single browser with tabs for legacy and modern apps")
        
        # Create shared driver
        self.shared_driver = self.create_driver()
        
        # Open first tab (legacy)
        self.shared_driver.get("about:blank")
        self.legacy_tab_handle = self.shared_driver.current_window_handle
        
        # Open second tab (modern)
        self.shared_driver.execute_script("window.open('about:blank', '_blank');")
        self.modern_tab_handle = self.shared_driver.window_handles[-1]
        
        logger.info(f"Legacy tab handle: {self.legacy_tab_handle}")
        logger.info(f"Modern tab handle: {self.modern_tab_handle}")
        
        return self.shared_driver, self.shared_driver
    
    def _setup_separate_browsers(self) -> Tuple[WebDriver, WebDriver]:
        """Setup separate browser instances."""
        logger.info("Setting up separate browsers for legacy and modern apps")
        
        self.legacy_driver = self.create_driver()
        self.modern_driver = self.create_driver()
        
        return self.legacy_driver, self.modern_driver
    
    def navigate_to_page(self, legacy_url: str, modern_url: str) -> None:
        """Navigate both browsers/tabs to their respective URLs."""
        if self.use_single_browser:
            self._navigate_single_browser(legacy_url, modern_url)
        else:
            self._navigate_separate_browsers(legacy_url, modern_url)
    
    def _navigate_single_browser(self, legacy_url: str, modern_url: str) -> None:
        """Navigate tabs in single browser."""
        driver = self.shared_driver
        
        # Navigate legacy tab
        driver.switch_to.window(self.legacy_tab_handle)
        if self.clear_state_between_tabs:
            self._clear_browser_state(driver)
        driver.get(legacy_url)
        time.sleep(self.tab_switch_delay)
        
        # Navigate modern tab
        driver.switch_to.window(self.modern_tab_handle)
        if self.clear_state_between_tabs:
            self._clear_browser_state(driver)
        driver.get(modern_url)
        time.sleep(self.tab_switch_delay)
        
        logger.info(f"Navigated legacy tab to: {legacy_url}")
        logger.info(f"Navigated modern tab to: {modern_url}")
    
    def _navigate_separate_browsers(self, legacy_url: str, modern_url: str) -> None:
        """Navigate separate browsers."""
        self.legacy_driver.get(legacy_url)
        self.modern_driver.get(modern_url)
        
        logger.info(f"Navigated legacy browser to: {legacy_url}")
        logger.info(f"Navigated modern browser to: {modern_url}")
    
    def _clear_browser_state(self, driver: WebDriver) -> None:
        """Clear browser state (cookies, localStorage, sessionStorage)."""
        try:
            # Clear cookies
            driver.delete_all_cookies()
            
            # Clear localStorage and sessionStorage
            driver.execute_script("window.localStorage.clear();")
            driver.execute_script("window.sessionStorage.clear();")
            
            logger.debug("Cleared browser state (cookies, localStorage, sessionStorage)")
        except Exception as e:
            logger.warning(f"Failed to clear browser state: {e}")
    
    def switch_to_legacy_tab(self) -> None:
        """Switch to legacy tab (single browser mode only)."""
        if self.use_single_browser and self.shared_driver:
            self.shared_driver.switch_to.window(self.legacy_tab_handle)
            time.sleep(self.tab_switch_delay)
    
    def switch_to_modern_tab(self) -> None:
        """Switch to modern tab (single browser mode only)."""
        if self.use_single_browser and self.shared_driver:
            self.shared_driver.switch_to.window(self.modern_tab_handle)
            time.sleep(self.tab_switch_delay)
    
    def get_legacy_driver(self) -> WebDriver:
        """Get the legacy browser driver."""
        if self.use_single_browser:
            self.switch_to_legacy_tab()
            return self.shared_driver
        else:
            return self.legacy_driver
    
    def get_modern_driver(self) -> WebDriver:
        """Get the modern browser driver."""
        if self.use_single_browser:
            self.switch_to_modern_tab()
            return self.shared_driver
        else:
            return self.modern_driver
    
    def close_browsers(self) -> None:
        """Close all browser instances."""
        try:
            if self.use_single_browser:
                if self.shared_driver:
                    self.shared_driver.quit()
                    logger.info("Closed shared browser instance")
            else:
                if self.legacy_driver:
                    self.legacy_driver.quit()
                    logger.info("Closed legacy browser instance")
                if self.modern_driver:
                    self.modern_driver.quit()
                    logger.info("Closed modern browser instance")
        except Exception as e:
            logger.error(f"Error closing browsers: {e}")
    
    def get_browser_info(self) -> Dict[str, Any]:
        """Get information about the current browser setup."""
        info = {
            "mode": "single_browser_with_tabs" if self.use_single_browser else "separate_browsers",
            "browser_type": self.browser_type,
            "headless": self.headless,
            "tab_isolation": self.tab_isolation if self.use_single_browser else None,
            "clear_state_between_tabs": self.clear_state_between_tabs if self.use_single_browser else None,
            "tab_switch_delay": self.tab_switch_delay if self.use_single_browser else None
        }
        
        if self.use_single_browser and self.shared_driver:
            info["legacy_tab_handle"] = self.legacy_tab_handle
            info["modern_tab_handle"] = self.modern_tab_handle
            info["total_tabs"] = len(self.shared_driver.window_handles)
        
        return info

