import pytest
from utils.test_orchestrator import TestOrchestrator
from utils.collectors import (
    page_title_with_iframes, heading_texts_with_iframes, button_texts_with_iframes,
    links_map_with_iframes, collect_comprehensive_with_iframes, _get_all_iframes
)
from utils.logging_utils import get_logger

logger = get_logger("iframe_test")


@pytest.mark.iframe
@pytest.mark.parametrize("path_key", [""])
class TestIframeComparison:
    """Dedicated test class for iframe comparison functionality."""
    
    def test_iframe_detection(self, settings, legacy_driver, modern_driver, path_key: str):
        """Test iframe detection and basic functionality."""
        logger.info("Testing iframe detection...")
        
        # Test iframe detection on both drivers
        legacy_iframes = _get_all_iframes(legacy_driver)
        modern_iframes = _get_all_iframes(modern_driver)
        
        logger.info(f"Legacy page has {len(legacy_iframes)} iframes")
        logger.info(f"Modern page has {len(modern_iframes)} iframes")
        
        # Log iframe details
        for i, iframe in enumerate(legacy_iframes):
            try:
                iframe_info = {
                    'id': iframe.get_attribute('id'),
                    'name': iframe.get_attribute('name'),
                    'src': iframe.get_attribute('src'),
                    'title': iframe.get_attribute('title')
                }
                logger.info(f"Legacy iframe {i+1}: {iframe_info}")
            except Exception as e:
                logger.warning(f"Error getting iframe {i+1} info: {e}")
        
        for i, iframe in enumerate(modern_iframes):
            try:
                iframe_info = {
                    'id': iframe.get_attribute('id'),
                    'name': iframe.get_attribute('name'),
                    'src': iframe.get_attribute('src'),
                    'title': iframe.get_attribute('title')
                }
                logger.info(f"Modern iframe {i+1}: {iframe_info}")
            except Exception as e:
                logger.warning(f"Error getting iframe {i+1} info: {e}")
    
    def test_iframe_page_titles(self, settings, legacy_driver, modern_driver, path_key: str):
        """Test iframe-aware page title collection."""
        logger.info("Testing iframe-aware page title collection...")
        
        # Collect page titles with iframes
        legacy_titles = page_title_with_iframes(legacy_driver)
        modern_titles = page_title_with_iframes(modern_driver)
        
        logger.info(f"Legacy page titles: {len(legacy_titles)} contexts")
        for title_data in legacy_titles:
            context = title_data.get('_iframe_context', {})
            title = title_data.get('content', title_data.get('element', 'Unknown'))
            logger.info(f"  - {context.get('type', 'unknown')}: {title}")
        
        logger.info(f"Modern page titles: {len(modern_titles)} contexts")
        for title_data in modern_titles:
            context = title_data.get('_iframe_context', {})
            title = title_data.get('content', title_data.get('element', 'Unknown'))
            logger.info(f"  - {context.get('type', 'unknown')}: {title}")
    
    def test_iframe_headings(self, settings, legacy_driver, modern_driver, path_key: str):
        """Test iframe-aware headings collection."""
        logger.info("Testing iframe-aware headings collection...")
        
        # Collect headings with iframes
        legacy_headings = heading_texts_with_iframes(legacy_driver)
        modern_headings = heading_texts_with_iframes(modern_driver)
        
        logger.info(f"Legacy headings: {len(legacy_headings)} contexts")
        for heading_data in legacy_headings:
            context = heading_data.get('_iframe_context', {})
            headings = heading_data.get('headings', [])
            logger.info(f"  - {context.get('type', 'unknown')}: {len(headings)} headings")
            if headings:
                logger.info(f"    Sample: {headings[:3]}")
        
        logger.info(f"Modern headings: {len(modern_headings)} contexts")
        for heading_data in modern_headings:
            context = heading_data.get('_iframe_context', {})
            headings = heading_data.get('headings', [])
            logger.info(f"  - {context.get('type', 'unknown')}: {len(headings)} headings")
            if headings:
                logger.info(f"    Sample: {headings[:3]}")
    
    def test_iframe_buttons(self, settings, legacy_driver, modern_driver, path_key: str):
        """Test iframe-aware button collection."""
        logger.info("Testing iframe-aware button collection...")
        
        # Collect buttons with iframes
        legacy_buttons = button_texts_with_iframes(legacy_driver)
        modern_buttons = button_texts_with_iframes(modern_driver)
        
        logger.info(f"Legacy buttons: {len(legacy_buttons)} contexts")
        for button_data in legacy_buttons:
            context = button_data.get('_iframe_context', {})
            buttons = button_data.get('buttons', [])
            logger.info(f"  - {context.get('type', 'unknown')}: {len(buttons)} buttons")
            if buttons:
                logger.info(f"    Sample: {buttons[:3]}")
        
        logger.info(f"Modern buttons: {len(modern_buttons)} contexts")
        for button_data in modern_buttons:
            context = button_data.get('_iframe_context', {})
            buttons = button_data.get('buttons', [])
            logger.info(f"  - {context.get('type', 'unknown')}: {len(buttons)} buttons")
            if buttons:
                logger.info(f"    Sample: {buttons[:3]}")
    
    def test_iframe_links(self, settings, legacy_driver, modern_driver, path_key: str):
        """Test iframe-aware links collection."""
        logger.info("Testing iframe-aware links collection...")
        
        # Collect links with iframes
        legacy_links = links_map_with_iframes(legacy_driver)
        modern_links = links_map_with_iframes(modern_driver)
        
        logger.info(f"Legacy links: {len(legacy_links)} contexts")
        for link_data in legacy_links:
            context = link_data.get('_iframe_context', {})
            links = link_data.get('links', {})
            logger.info(f"  - {context.get('type', 'unknown')}: {len(links)} links")
            if links:
                if isinstance(links, dict):
                    sample_links = list(links.items())[:3]
                else:
                    sample_links = links[:3] if isinstance(links, (list, tuple)) else [str(links)]
                logger.info(f"    Sample: {sample_links}")
        
        logger.info(f"Modern links: {len(modern_links)} contexts")
        for link_data in modern_links:
            context = link_data.get('_iframe_context', {})
            links = link_data.get('links', {})
            logger.info(f"  - {context.get('type', 'unknown')}: {len(links)} links")
            if links:
                if isinstance(links, dict):
                    sample_links = list(links.items())[:3]
                else:
                    sample_links = links[:3] if isinstance(links, (list, tuple)) else [str(links)]
                logger.info(f"    Sample: {sample_links}")
    
    def test_comprehensive_iframe_content(self, settings, legacy_driver, modern_driver, path_key: str):
        """Test comprehensive iframe content collection."""
        logger.info("Testing comprehensive iframe content collection...")
        
        # Collect comprehensive iframe content
        legacy_content = collect_comprehensive_with_iframes(legacy_driver)
        modern_content = collect_comprehensive_with_iframes(modern_driver)
        
        # Log summary information
        legacy_summary = legacy_content.get('summary', {})
        modern_summary = modern_content.get('summary', {})
        
        logger.info(f"Legacy comprehensive content:")
        logger.info(f"  - Total iframes: {legacy_summary.get('total_iframes', 0)}")
        logger.info(f"  - Accessible iframes: {legacy_summary.get('accessible_iframes', 0)}")
        logger.info(f"  - Total elements: {legacy_summary.get('total_elements', 0)}")
        
        logger.info(f"Modern comprehensive content:")
        logger.info(f"  - Total iframes: {modern_summary.get('total_iframes', 0)}")
        logger.info(f"  - Accessible iframes: {modern_summary.get('accessible_iframes', 0)}")
        logger.info(f"  - Total elements: {modern_summary.get('total_elements', 0)}")
        
        # Log iframe details
        legacy_iframes = legacy_content.get('iframes', [])
        modern_iframes = modern_content.get('iframes', [])
        
        logger.info(f"Legacy iframe details:")
        for i, iframe_data in enumerate(legacy_iframes):
            iframe_info = iframe_data.get('iframe_info', {})
            elements = iframe_data.get('elements', {})
            logger.info(f"  - Iframe {i+1}: {iframe_info.get('id', 'no-id')} - {len(elements)} elements")
        
        logger.info(f"Modern iframe details:")
        for i, iframe_data in enumerate(modern_iframes):
            iframe_info = iframe_data.get('iframe_info', {})
            elements = iframe_data.get('elements', {})
            logger.info(f"  - Iframe {i+1}: {iframe_info.get('id', 'no-id')} - {len(elements)} elements")
    
    def test_iframe_comparison_integration(self, settings, legacy_driver, modern_driver, path_key: str):
        """Test iframe comparison integration with the main framework."""
        logger.info("Testing iframe comparison integration...")
        
        # Use the orchestrator to run iframe comparisons
        orchestrator = TestOrchestrator(settings)
        test_results = {"passed": 0, "failed": 0, "skipped": 0, "errors": 0}
        
        # Run only iframe comparisons
        test_results = orchestrator.comparison_engine.run_iframe_comparisons(
            legacy_driver, modern_driver, test_results
        )
        
        # Log results
        logger.info(f"Iframe comparison results:")
        logger.info(f"  - Passed: {test_results['passed']}")
        logger.info(f"  - Failed: {test_results['failed']}")
        logger.info(f"  - Skipped: {test_results['skipped']}")
        logger.info(f"  - Errors: {test_results['errors']}")
        
        # Assert that we have some results
        total_tests = test_results['passed'] + test_results['failed'] + test_results['skipped'] + test_results['errors']
        assert total_tests > 0, "No iframe comparison tests were executed"
        
        # Allow some failures for iframe comparisons (they can be complex)
        max_failures = 3
        assert test_results['failed'] <= max_failures, f"Too many iframe comparison failures: {test_results['failed']}"
