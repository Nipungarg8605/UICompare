#!/usr/bin/env python3
"""
FundCenter Legacy vs Modern Application Comparison Test

This script uses the semantic field comparison framework to validate
the FundCenter migration from legacy to modern architecture.
"""

import sys
import os
import json
import time
from typing import Dict, Any

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.test_orchestrator import TestOrchestrator
from utils.browser_manager import BrowserManager
from config.loader import load_settings
from utils.logging_utils import get_logger

logger = get_logger("fundcenter_test")

class FundCenterComparisonTest:
    """Test class for FundCenter legacy vs modern comparison."""
    
    def __init__(self):
        """Initialize the test with FundCenter configuration."""
        self.settings = load_settings()
        self.fundcenter_config = self._load_fundcenter_config()
        self.orchestrator = TestOrchestrator(self.settings)
        self.browser_manager = BrowserManager(self.settings)
        
    def _load_fundcenter_config(self) -> Dict[str, Any]:
        """Load FundCenter specific configuration."""
        config_path = "config/fundcenter_config.json"
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"FundCenter config not found: {config_path}")
            return {}
    
    def run_comparison(self) -> Dict[str, Any]:
        """Run the complete FundCenter comparison test."""
        print("=" * 80)
        print("FUNDCENTER LEGACY VS MODERN COMPARISON TEST")
        print("=" * 80)
        print()
        
        results = {
            "test_name": "FundCenter Comparison",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "results": {},
            "summary": {}
        }
        
        try:
            # Setup browsers
            print("🔧 Setting up browser instances...")
            legacy_driver, modern_driver = self.browser_manager.setup_browsers()
            print("✅ Browsers setup complete")
            
            # Navigate to applications
            legacy_url = self.fundcenter_config["urls"]["legacy"]
            modern_url = self.fundcenter_config["urls"]["modern"]
            
            print(f"🌐 Navigating to applications...")
            print(f"   Legacy: {legacy_url}")
            print(f"   Modern: {modern_url}")
            
            self.browser_manager.navigate_to_page(legacy_url, modern_url)
            
            # Wait for pages to load
            time.sleep(5)
            print("✅ Navigation complete")
            
            # Run semantic field comparisons
            results["results"] = self._run_semantic_comparisons(legacy_driver, modern_driver)
            
            # Generate summary
            results["summary"] = self._generate_summary(results["results"])
            
            print("\n" + "=" * 80)
            print("TEST RESULTS SUMMARY")
            print("=" * 80)
            self._print_summary(results["summary"])
            
        except Exception as e:
            logger.error(f"Test failed: {e}")
            results["error"] = str(e)
        finally:
            # Cleanup
            print("\n🧹 Cleaning up browser instances...")
            self.browser_manager.cleanup()
            print("✅ Cleanup complete")
        
        return results
    
    def _run_semantic_comparisons(self, legacy_driver, modern_driver) -> Dict[str, Any]:
        """Run semantic field comparisons."""
        results = {}
        
        # Test navigation structure
        print("\n🧭 Testing navigation structure...")
        results["navigation"] = self._test_navigation(legacy_driver, modern_driver)
        
        # Test header/branding
        print("\n🏷️  Testing header and branding...")
        results["header"] = self._test_header(legacy_driver, modern_driver)
        
        # Test dashboard content
        print("\n📊 Testing dashboard content...")
        results["dashboard"] = self._test_dashboard(legacy_driver, modern_driver)
        
        # Test search criteria
        print("\n🔍 Testing search criteria...")
        results["search_criteria"] = self._test_search_criteria(legacy_driver, modern_driver)
        
        # Test rates summary
        print("\n📈 Testing rates summary...")
        results["rates_summary"] = self._test_rates_summary(legacy_driver, modern_driver)
        
        # Test baskets summary (legacy only)
        print("\n📦 Testing baskets summary (legacy only)...")
        results["baskets_summary"] = self._test_baskets_summary(legacy_driver, modern_driver)
        
        # Test valuations summary (legacy only)
        print("\n💰 Testing valuations summary (legacy only)...")
        results["valuations_summary"] = self._test_valuations_summary(legacy_driver, modern_driver)
        
        # Test footer
        print("\n📄 Testing footer...")
        results["footer"] = self._test_footer(legacy_driver, modern_driver)
        
        return results
    
    def _test_navigation(self, legacy_driver, modern_driver) -> Dict[str, Any]:
        """Test navigation structure."""
        nav_fields = self.fundcenter_config["semantic_fields"]["navigation"]
        results = {}
        
        for field_name, field_config in nav_fields.items():
            legacy_selector = field_config["selectors"]["legacy"]
            modern_selector = field_config["selectors"]["modern"]
            
            # Check if element exists in legacy
            legacy_exists = self._element_exists(legacy_driver, legacy_selector)
            
            # Check if element exists in modern
            modern_exists = self._element_exists(modern_driver, modern_selector) if modern_selector else False
            
            results[field_name] = {
                "legacy_exists": legacy_exists,
                "modern_exists": modern_exists,
                "match": legacy_exists == modern_exists,
                "priority": field_config["priority"]
            }
        
        return results
    
    def _test_header(self, legacy_driver, modern_driver) -> Dict[str, Any]:
        """Test header and branding elements."""
        header_fields = self.fundcenter_config["semantic_fields"]["header"]
        results = {}
        
        for field_name, field_config in header_fields.items():
            legacy_selector = field_config["selectors"]["legacy"]
            modern_selector = field_config["selectors"]["modern"]
            
            legacy_exists = self._element_exists(legacy_driver, legacy_selector)
            modern_exists = self._element_exists(modern_driver, modern_selector)
            
            results[field_name] = {
                "legacy_exists": legacy_exists,
                "modern_exists": modern_exists,
                "match": legacy_exists == modern_exists,
                "priority": field_config["priority"]
            }
        
        return results
    
    def _test_dashboard(self, legacy_driver, modern_driver) -> Dict[str, Any]:
        """Test dashboard content."""
        dashboard_fields = self.fundcenter_config["semantic_fields"]["dashboard"]
        results = {}
        
        for field_name, field_config in dashboard_fields.items():
            legacy_selector = field_config["selectors"]["legacy"]
            modern_selector = field_config["selectors"]["modern"]
            
            legacy_exists = self._element_exists(legacy_driver, legacy_selector)
            modern_exists = self._element_exists(modern_driver, modern_selector)
            
            results[field_name] = {
                "legacy_exists": legacy_exists,
                "modern_exists": modern_exists,
                "match": legacy_exists == modern_exists,
                "priority": field_config["priority"]
            }
        
        return results
    
    def _test_search_criteria(self, legacy_driver, modern_driver) -> Dict[str, Any]:
        """Test search criteria elements."""
        search_fields = self.fundcenter_config["semantic_fields"]["search_criteria"]
        results = {}
        
        for field_name, field_config in search_fields.items():
            legacy_selector = field_config["selectors"]["legacy"]
            modern_selector = field_config["selectors"]["modern"]
            
            legacy_exists = self._element_exists(legacy_driver, legacy_selector)
            modern_exists = self._element_exists(modern_driver, modern_selector)
            
            results[field_name] = {
                "legacy_exists": legacy_exists,
                "modern_exists": modern_exists,
                "match": legacy_exists == modern_exists,
                "priority": field_config["priority"]
            }
        
        return results
    
    def _test_rates_summary(self, legacy_driver, modern_driver) -> Dict[str, Any]:
        """Test rates summary information."""
        rates_fields = self.fundcenter_config["semantic_fields"]["rates_summary"]
        results = {}
        
        for field_name, field_config in rates_fields.items():
            legacy_selector = field_config["selectors"]["legacy"]
            modern_selector = field_config["selectors"]["modern"]
            
            legacy_exists = self._element_exists(legacy_driver, legacy_selector)
            modern_exists = self._element_exists(modern_driver, modern_selector)
            
            results[field_name] = {
                "legacy_exists": legacy_exists,
                "modern_exists": modern_exists,
                "match": legacy_exists == modern_exists,
                "priority": field_config["priority"]
            }
        
        return results
    
    def _test_baskets_summary(self, legacy_driver, modern_driver) -> Dict[str, Any]:
        """Test baskets summary (legacy only)."""
        baskets_fields = self.fundcenter_config["semantic_fields"]["baskets_summary"]
        results = {}
        
        for field_name, field_config in baskets_fields.items():
            legacy_selector = field_config["selectors"]["legacy"]
            modern_selector = field_config["selectors"]["modern"]
            
            legacy_exists = self._element_exists(legacy_driver, legacy_selector)
            modern_exists = self._element_exists(modern_driver, modern_selector) if modern_selector else False
            
            results[field_name] = {
                "legacy_exists": legacy_exists,
                "modern_exists": modern_exists,
                "expected_missing_in_modern": True,
                "priority": field_config["priority"]
            }
        
        return results
    
    def _test_valuations_summary(self, legacy_driver, modern_driver) -> Dict[str, Any]:
        """Test valuations summary (legacy only)."""
        valuations_fields = self.fundcenter_config["semantic_fields"]["valuations_summary"]
        results = {}
        
        for field_name, field_config in valuations_fields.items():
            legacy_selector = field_config["selectors"]["legacy"]
            modern_selector = field_config["selectors"]["modern"]
            
            legacy_exists = self._element_exists(legacy_driver, legacy_selector)
            modern_exists = self._element_exists(modern_driver, modern_selector) if modern_selector else False
            
            results[field_name] = {
                "legacy_exists": legacy_exists,
                "modern_exists": modern_exists,
                "expected_missing_in_modern": True,
                "priority": field_config["priority"]
            }
        
        return results
    
    def _test_footer(self, legacy_driver, modern_driver) -> Dict[str, Any]:
        """Test footer elements."""
        footer_fields = self.fundcenter_config["semantic_fields"]["footer"]
        results = {}
        
        for field_name, field_config in footer_fields.items():
            legacy_selector = field_config["selectors"]["legacy"]
            modern_selector = field_config["selectors"]["modern"]
            
            legacy_exists = self._element_exists(legacy_driver, legacy_selector)
            modern_exists = self._element_exists(modern_driver, modern_selector)
            
            results[field_name] = {
                "legacy_exists": legacy_exists,
                "modern_exists": modern_exists,
                "match": legacy_exists == modern_exists,
                "priority": field_config["priority"]
            }
        
        return results
    
    def _element_exists(self, driver, selector: str) -> bool:
        """Check if an element exists using the selector."""
        try:
            if selector.startswith("text:"):
                # Text-based selector
                text = selector[5:]
                elements = driver.find_elements("xpath", f"//*[contains(text(), '{text}')]")
                return len(elements) > 0
            elif selector.startswith("img["):
                # Image selector
                elements = driver.find_elements("css", selector)
                return len(elements) > 0
            elif selector.startswith("table:"):
                # Table selector
                text = selector[6:]
                elements = driver.find_elements("xpath", f"//table[contains(., '{text}')]")
                return len(elements) > 0
            elif selector.startswith("button:"):
                # Button selector
                text = selector[7:]
                elements = driver.find_elements("xpath", f"//button[contains(text(), '{text}')]")
                return len(elements) > 0
            elif selector.startswith("input["):
                # Input selector
                elements = driver.find_elements("css", selector)
                return len(elements) > 0
            else:
                # Default CSS selector
                elements = driver.find_elements("css", selector)
                return len(elements) > 0
        except Exception as e:
            logger.warning(f"Error checking element {selector}: {e}")
            return False
    
    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of test results."""
        summary = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "high_priority_passed": 0,
            "high_priority_failed": 0,
            "medium_priority_passed": 0,
            "medium_priority_failed": 0,
            "low_priority_passed": 0,
            "low_priority_failed": 0,
            "missing_features": [],
            "unexpected_differences": []
        }
        
        for category, category_results in results.items():
            for field_name, field_result in category_results.items():
                summary["total_tests"] += 1
                
                if field_result.get("match", False):
                    summary["passed"] += 1
                    
                    if field_result["priority"] == "high":
                        summary["high_priority_passed"] += 1
                    elif field_result["priority"] == "medium":
                        summary["medium_priority_passed"] += 1
                    elif field_result["priority"] == "low":
                        summary["low_priority_passed"] += 1
                else:
                    summary["failed"] += 1
                    
                    if field_result["priority"] == "high":
                        summary["high_priority_failed"] += 1
                    elif field_result["priority"] == "medium":
                        summary["medium_priority_failed"] += 1
                    elif field_result["priority"] == "low":
                        summary["low_priority_failed"] += 1
                    
                    # Check if this is an expected missing feature
                    if field_result.get("expected_missing_in_modern", False):
                        summary["missing_features"].append(f"{category}.{field_name}")
                    else:
                        summary["unexpected_differences"].append(f"{category}.{field_name}")
        
        summary["success_rate"] = (summary["passed"] / summary["total_tests"] * 100) if summary["total_tests"] > 0 else 0
        
        return summary
    
    def _print_summary(self, summary: Dict[str, Any]):
        """Print a formatted summary of results."""
        print(f"📊 Total Tests: {summary['total_tests']}")
        print(f"✅ Passed: {summary['passed']}")
        print(f"❌ Failed: {summary['failed']}")
        print(f"📈 Success Rate: {summary['success_rate']:.1f}%")
        print()
        
        print("🎯 Priority Breakdown:")
        print(f"   High Priority: {summary['high_priority_passed']} passed, {summary['high_priority_failed']} failed")
        print(f"   Medium Priority: {summary['medium_priority_passed']} passed, {summary['medium_priority_failed']} failed")
        print(f"   Low Priority: {summary['low_priority_passed']} passed, {summary['low_priority_failed']} failed")
        print()
        
        if summary["missing_features"]:
            print("📋 Expected Missing Features (Legacy Only):")
            for feature in summary["missing_features"]:
                print(f"   • {feature}")
            print()
        
        if summary["unexpected_differences"]:
            print("⚠️  Unexpected Differences:")
            for diff in summary["unexpected_differences"]:
                print(f"   • {diff}")
            print()
        
        # Overall assessment
        if summary["high_priority_failed"] == 0:
            print("🎉 EXCELLENT: All high-priority features match!")
        elif summary["high_priority_failed"] <= 2:
            print("✅ GOOD: Most high-priority features match with minor issues.")
        else:
            print("⚠️  ATTENTION NEEDED: Multiple high-priority features have differences.")

def main():
    """Main function to run the FundCenter comparison test."""
    test = FundCenterComparisonTest()
    results = test.run_comparison()
    
    # Save results to file
    output_file = f"fundcenter_comparison_results_{int(time.time())}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Results saved to: {output_file}")
    
    return results

if __name__ == "__main__":
    main()
