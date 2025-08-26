"""
Test Utilities - Helper functions for test setup and common operations.

This module contains utility functions for test setup, page navigation, and highlighting.
"""

from __future__ import annotations
import time
from typing import Dict, List, Any
from utils.collectors import wait_for_document_ready, remove_ignored_selectors
from utils.highlight import highlight_selector
from utils.logging_utils import get_logger

logger = get_logger("test_utilities")


class TestUtilities:
    """Utility functions for test setup and common operations."""
    
    def __init__(self, settings: Dict):
        self.settings = settings
    
    def setup_page_comparison(self, legacy_driver, modern_driver, path: str) -> None:
        """
        Setup page comparison with common initialization and error handling.
        
        Args:
            legacy_driver: WebDriver for legacy environment
            modern_driver: WebDriver for modern environment
            path: URL path to compare
        """
        legacy_url = self.settings["envs"]["legacy"]["base_url"].rstrip("/") + path
        modern_url = self.settings["envs"]["modern"]["base_url"].rstrip("/") + path

        logger.info(f"Comparing path: {path}")
        logger.info(f"Legacy URL: {legacy_url}")
        logger.info(f"Modern URL: {modern_url}")
        
        # Navigate to pages with error handling
        try:
            legacy_driver.get(legacy_url)
            modern_driver.get(modern_url)
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            raise
        
        # Wait for pages to load
        wait_for_document_ready(legacy_driver)
        wait_for_document_ready(modern_driver)
        
        # Apply highlighting if enabled
        self._apply_highlighting(legacy_driver, modern_driver, path)
        
        # Remove ignored selectors
        remove_ignored_selectors(legacy_driver, self.settings.get("ignore_selectors", []))
        remove_ignored_selectors(modern_driver, self.settings.get("ignore_selectors", []))
    
    def _apply_highlighting(self, legacy_driver, modern_driver, path: str) -> None:
        """
        Apply highlighting to elements if enabled with error handling.
        
        Args:
            legacy_driver: WebDriver for legacy environment
            modern_driver: WebDriver for modern environment
            path: URL path for route-specific highlighting
        """
        hcfg = self.settings.get("highlight", {})
        h_enabled = hcfg.get("enabled", True)
        
        if not h_enabled:
            return
            
        h_dur = int(hcfg.get("duration_ms", 600))
        global_selectors = hcfg.get("selectors", [])
        route_selectors = (hcfg.get("selectors_by_route", {}) or {}).get(path, [])
        
        for sel in list(global_selectors) + list(route_selectors):
            try:
                highlight_selector(legacy_driver, sel, h_dur)
                highlight_selector(modern_driver, sel, h_dur)
            except Exception as e:
                logger.debug(f"Highlighting failed for selector '{sel}': {e}")
    
    def get_test_configuration(self) -> Dict[str, Any]:
        """
        Get test configuration summary.
        
        Returns:
            Dictionary with test configuration details
        """
        return {
            "checks": self.settings.get("checks", {}),
            "limits": self.settings.get("limits", {}),
            "highlight": self.settings.get("highlight", {}),
            "ignore_selectors": self.settings.get("ignore_selectors", []),
            "max_test_failures": self.settings.get("max_test_failures", 0)
        }
    
    def validate_test_environment(self, legacy_driver, modern_driver) -> bool:
        """
        Validate that the test environment is properly set up.
        
        Args:
            legacy_driver: WebDriver for legacy environment
            modern_driver: WebDriver for modern environment
            
        Returns:
            True if environment is valid, False otherwise
        """
        try:
            # Check if drivers are responsive
            legacy_driver.current_url
            modern_driver.current_url
            return True
        except Exception as e:
            logger.error(f"Test environment validation failed: {e}")
            return False

    def collect_and_compare(self, legacy_driver, modern_driver, collector_func, 
                                 comparator_func, test_name: str, test_results: Dict, 
                                 **collector_kwargs) -> bool:
        """Safely collect data and compare with error handling and timing."""
        try:
            start_time = time.time()
            legacy_data = collector_func(legacy_driver)
            modern_data = collector_func(modern_driver)
            collection_time = time.time() - start_time
            
            logger.info(f"{test_name} collection time: {collection_time:.2f}s")
            
            start_time = time.time()
            result = comparator_func(legacy_data, modern_data)
            comparison_time = time.time() - start_time
            
            logger.info(f"{test_name} comparison time: {comparison_time:.2f}s")
            
            if result.success:
                test_results["passed"] += 1
            else:
                test_results["failed"] += 1
                logger.warning(f"{test_name} failed: {result.message}")
                if result.similarity_score is not None:
                    logger.info(f"{test_name} similarity score: {result.similarity_score:.2%}")
            
            return result.success
        except Exception as e:
            test_results["errors"] += 1
            logger.error(f"{test_name} error: {e}")
            return False
