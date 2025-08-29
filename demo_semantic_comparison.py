#!/usr/bin/env python3
"""
Semantic Field Comparison Framework Demo

This script demonstrates how to use the field-level logical equivalence
comparison framework to compare legacy and modern applications.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.test_orchestrator import TestOrchestrator
from utils.logging_utils import get_logger
from config.loader import load_settings

logger = get_logger("semantic_demo")

def main():
    """Main demonstration function."""
    print("=" * 80)
    print("SEMANTIC FIELD-LEVEL LOGICAL EQUIVALENCE COMPARISON FRAMEWORK")
    print("=" * 80)
    print()
    
    # Load settings
    settings = load_settings()
    print("✅ Configuration loaded successfully")
    print(f"   - Legacy URL: {settings['envs']['legacy']['base_url']}")
    print(f"   - Modern URL: {settings['envs']['modern']['base_url']}")
    print(f"   - Browser: {settings['browser']}")
    print()
    
    # Initialize orchestrator
    orchestrator = TestOrchestrator(settings)
    print("✅ Test orchestrator initialized")
    print()
    
    # Run comprehensive comparison
    print("🚀 Starting comprehensive UI comparison...")
    print("   This includes:")
    print("   - Traditional element comparisons")
    print("   - Iframe-aware comparisons")
    print("   - Semantic field-level logical equivalence comparisons")
    print()
    
    try:
        # Run the full comparison suite
        test_results = orchestrator.run_comprehensive_comparison()
        
        # Display results
        print("=" * 80)
        print("COMPARISON RESULTS")
        print("=" * 80)
        print(f"✅ Passed: {test_results['passed']}")
        print(f"❌ Failed: {test_results['failed']}")
        print(f"⏭️  Skipped: {test_results['skipped']}")
        print(f"💥 Errors: {test_results['errors']}")
        print()
        
        # Calculate success rate
        total_tests = sum(test_results.values())
        if total_tests > 0:
            success_rate = (test_results['passed'] / total_tests) * 100
            print(f"📊 Success Rate: {success_rate:.1f}%")
            print()
        
        # Provide recommendations
        print("=" * 80)
        print("RECOMMENDATIONS")
        print("=" * 80)
        
        if test_results['failed'] > 0:
            print("⚠️  Some comparisons failed. Consider:")
            print("   - Adjusting field mappings in config/settings.yaml")
            print("   - Refining CSS selectors for better element detection")
            print("   - Adjusting similarity thresholds for text matching")
            print("   - Adding more semantic rules for complex elements")
        else:
            print("🎉 All comparisons passed! Your applications are functionally equivalent.")
        
        if test_results['errors'] > 0:
            print("💥 Some errors occurred. Check:")
            print("   - Browser compatibility")
            print("   - Network connectivity")
            print("   - Application availability")
        
        print()
        print("📝 For detailed analysis, check the logs above.")
        print("🔧 To customize comparisons, edit config/settings.yaml")
        
    except Exception as e:
        print(f"💥 Error during comparison: {e}")
        logger.error(f"Demo failed: {e}")
        return 1
    
    print()
    print("=" * 80)
    print("DEMO COMPLETED SUCCESSFULLY")
    print("=" * 80)
    return 0

def demo_semantic_only():
    """Demonstrate semantic field comparison only."""
    print("=" * 80)
    print("SEMANTIC FIELD COMPARISON DEMO")
    print("=" * 80)
    print()
    
    settings = load_settings()
    orchestrator = TestOrchestrator(settings)
    
    print("🎯 Running semantic field-level comparisons only...")
    print()
    
    try:
        # Create browser manager and get drivers
        from utils.browser_manager import BrowserManager
        browser_manager = BrowserManager(settings)
        legacy_driver, modern_driver = browser_manager.setup_browsers()
        
        # Navigate to test pages
        legacy_url = settings["envs"]["legacy"]["base_url"]
        modern_url = settings["envs"]["modern"]["base_url"]
        
        legacy_driver.get(legacy_url)
        modern_driver.get(modern_url)
        
        # Initialize test results
        test_results = {"passed": 0, "failed": 0, "skipped": 0, "errors": 0}
        
        # Run semantic comparisons
        test_results = orchestrator.comparison_engine.run_semantic_field_comparisons(
            legacy_driver, modern_driver, test_results
        )
        
        # Display results
        print("=" * 80)
        print("SEMANTIC COMPARISON RESULTS")
        print("=" * 80)
        print(f"✅ Passed: {test_results['passed']}")
        print(f"❌ Failed: {test_results['failed']}")
        print(f"⏭️  Skipped: {test_results['skipped']}")
        print(f"💥 Errors: {test_results['errors']}")
        print()
        
        # Clean up
        browser_manager.close_browsers()
        
    except Exception as e:
        print(f"💥 Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Semantic Field Comparison Framework Demo")
    parser.add_argument("--semantic-only", action="store_true", 
                       help="Run only semantic field comparisons")
    
    args = parser.parse_args()
    
    if args.semantic_only:
        exit_code = demo_semantic_only()
    else:
        exit_code = main()
    
    sys.exit(exit_code)
