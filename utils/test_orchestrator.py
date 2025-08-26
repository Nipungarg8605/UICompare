
from __future__ import annotations
import time
from typing import Dict, List, Optional
from utils.comparison_engine import ComparisonEngine
from utils.test_utilities import TestUtilities
from utils.logging_utils import get_logger

logger = get_logger("test_orchestrator")


class TestOrchestrator:
    """Clean test orchestration logic separated from implementation details."""
    
    def __init__(self, settings: Dict):
        self.settings = settings
        self.comparison_engine = ComparisonEngine(settings)
        self.test_utilities = TestUtilities(settings)
    
    def run_comparison_test(self, legacy_driver, modern_driver, path: str) -> Dict[str, int]:
       
        test_results = {"passed": 0,"failed": 0,"skipped": 0,"errors": 0}
        
        try:
            # Setup page comparison
            self.test_utilities.setup_page_comparison(legacy_driver, modern_driver, path)
            
            # Run all comparison categories
            logger.info("Starting comprehensive UI comparison test...")
            
            # Basic comparisons
            test_results = self.comparison_engine.run_basic_comparisons(legacy_driver, modern_driver, test_results)
            
            # Extended comparisons
            test_results = self.comparison_engine.run_extended_comparisons(legacy_driver, modern_driver, test_results)
            
            # Modern feature comparisons
            test_results = self.comparison_engine.run_modern_feature_comparisons(legacy_driver, modern_driver, test_results)
            
            # Comprehensive list comparisons
            test_results = self.comparison_engine.run_comprehensive_list_comparisons(legacy_driver, modern_driver, test_results)
            
            # Semantic comparisons
            test_results = self.comparison_engine.run_semantic_comparisons(legacy_driver, modern_driver, test_results)
            
            # Form structure comparisons
            test_results = self.comparison_engine.run_form_structure_comparisons(legacy_driver, modern_driver, test_results)
            
            # Progress and graphics comparisons
            test_results = self.comparison_engine.run_progress_graphics_comparisons(legacy_driver, modern_driver, test_results)
            
            # Advanced web comparisons
            test_results = self.comparison_engine.run_advanced_web_comparisons(legacy_driver, modern_driver, test_results)
            
            # Modern framework comparisons
            test_results = self.comparison_engine.run_modern_framework_comparisons(legacy_driver, modern_driver, test_results)
            
            # Comprehensive page comparisons
            test_results = self.comparison_engine.run_comprehensive_page_comparisons(legacy_driver, modern_driver, test_results)
            
            logger.info("Completed comprehensive UI comparison test!")
            
        except Exception as e:
            logger.error(f"Error during comparison for path {path}: {e}")
            test_results["errors"] += 1
        
        # Log test summary
        self._log_test_summary(test_results)
        
        return test_results
    
    def _log_test_summary(self, test_results: Dict[str, int]) -> None:
        """Log the test results summary."""
        logger.info(
            f"Test Summary - Passed: {test_results['passed']}, "
            f"Failed: {test_results['failed']}, "
            f"Skipped: {test_results['skipped']}, "
            f"Errors: {test_results['errors']}"
        )
    
    def assert_test_success(self, test_results: Dict[str, int]) -> None:
       
        max_failures = self.settings.get("max_test_failures", 5)  # Allow some failures for UI comparison
        if test_results["failed"] > max_failures:
            raise AssertionError(
                f"Too many test failures: {test_results['failed']} "
                f"(max allowed: {max_failures})"
            )
