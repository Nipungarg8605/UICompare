"""
Comparison Engine - Implementation details for running comparisons.

This module contains all the implementation logic for different types of comparisons.
"""

from __future__ import annotations
import time
from typing import Dict, List, Any
from utils.compare import IntegratedComparator, ComparisonType
from utils.collectors import (
    page_title, primary_h1, heading_texts, nav_link_texts, button_texts,
    body_text_snapshot, links_map, collect_form_summary, collect_table_preview,
    collect_meta, collect_accessibility, collect_head_meta_extended,
    collect_breadcrumbs, collect_tabs, collect_accordions, collect_pagination,
    collect_form_details, collect_widgets, collect_images_preview,
    collect_landmarks, collect_interactive_roles, collect_i18n,
    collect_performance, collect_carousel_slides, collect_search_functionality,
    collect_notifications_alerts, collect_loading_states, collect_social_media_links,
    collect_video_audio_elements, collect_data_attributes, collect_custom_elements,
    collect_analytics_tracking, collect_error_states, collect_theme_colors,
    collect_page_structure, collect_list_elements, collect_navigation_lists,
    collect_breadcrumb_lists, collect_feature_lists, collect_all_lists,
    collect_semantic_elements, collect_interactive_elements, collect_form_structure,
    collect_progress_indicators, collect_graphics_elements, collect_all_semantic_content,
    collect_page_elements_ordered, collect_page_structure_ordered,
    # Iframe-aware collectors
    page_title_with_iframes, heading_texts_with_iframes, button_texts_with_iframes,
    links_map_with_iframes, collect_all_iframe_content, collect_comprehensive_with_iframes,
    _collect_from_all_contexts
)
from utils.logging_utils import get_logger
from utils.test_utilities import TestUtilities
from utils.semantic_field_comparator import SemanticFieldComparator

logger = get_logger("comparison_engine")


class ComparisonEngine:
    """Engine for running different types of comparisons."""
    
    def __init__(self, settings: Dict):
        self.settings = settings
        self.test_utilities = TestUtilities(settings)
        self.comparator = self._get_comparator()
        self.checks = settings.get("checks", {})
        self.limits = settings.get("limits", {})
        
        # Initialize semantic field comparator if field mappings are available
        self.semantic_comparator = None
        if 'field_mappings' in settings:
            self.semantic_comparator = SemanticFieldComparator(
                settings.get('field_mappings', {}),
                settings.get('semantic_rules', {}),
                settings.get('comparison_settings', {})
            )
    
    def _get_comparator(self) -> IntegratedComparator:
        """Get configured comparator instance with enhanced options."""
        fuzzy_threshold = self.settings.get("auto_collect_body_similarity", 0.9)
        semantic_threshold = self.settings.get("semantic_threshold", 0.8)
        numeric_tolerance = self.settings.get("numeric_tolerance", 0.1)
        date_tolerance_seconds = self.settings.get("date_tolerance_seconds", 300)
        
        return IntegratedComparator(
            fuzzy_threshold=fuzzy_threshold,
            semantic_threshold=semantic_threshold,
            numeric_tolerance=numeric_tolerance,
            date_tolerance_seconds=date_tolerance_seconds
        )
    
    def run_basic_comparisons(self, legacy_driver, modern_driver, test_results: Dict) -> Dict:
        """Run basic page element comparisons."""
        logger.info("Running basic comparisons...")
        
        # Page title comparison
        self.test_utilities.collect_and_compare(
            legacy_driver, modern_driver,
            page_title, lambda a, b: self.comparator.compare_text(a, b, ComparisonType.EXACT_TEXT),
            "Page Title", test_results
        )
        
        # Primary H1 comparison
        self.test_utilities.collect_and_compare(
            legacy_driver, modern_driver,
            primary_h1, lambda a, b: self.comparator.compare_text(a, b, ComparisonType.EXACT_TEXT),
            "Primary H1", test_results
        )
        
        # Headings comparison
        self.test_utilities.collect_and_compare(
            legacy_driver, modern_driver,
            heading_texts, lambda a, b: self.comparator.compare_lists(a, b, ComparisonType.EXACT_TEXT),
            "Headings", test_results
        )
        
        # Navigation links comparison
        self.test_utilities.collect_and_compare(
            legacy_driver, modern_driver,
            nav_link_texts, lambda a, b: self.comparator.compare_lists(a, b, ComparisonType.EXACT_TEXT),
            "Navigation Links", test_results
        )
        
        # Button texts comparison
        self.test_utilities.collect_and_compare(
            legacy_driver, modern_driver,
            button_texts, lambda a, b: self.comparator.compare_lists(a, b, ComparisonType.EXACT_TEXT),
            "Button Texts", test_results
        )
        
        # Body snapshot fuzzy comparison
        self.test_utilities.collect_and_compare(
            legacy_driver, modern_driver,
            body_text_snapshot, lambda a, b: self.comparator.compare_text(a, b, ComparisonType.FUZZY_TEXT),
            "Body Snapshot", test_results
        )
        
        return test_results
    
    def run_extended_comparisons(self, legacy_driver, modern_driver, test_results: Dict) -> Dict:
        """Run extended comparisons for additional page elements."""
        logger.info("Running extended comparisons...")
        
        # Links map comparison
        self.test_utilities.collect_and_compare(
            legacy_driver, modern_driver,
            links_map, self.comparator.compare_links_map,
            "Links Map", test_results
        )
        
        # Form summary comparison
        if self.checks.get("forms", True):
            self.test_utilities.collect_and_compare(
                legacy_driver, modern_driver,
                collect_form_summary, self.comparator.compare_form_structure,
                "Form Summary", test_results
            )
        
        # Table preview comparison
        if self.checks.get("tables", True):
            self.test_utilities.collect_and_compare(
                legacy_driver, modern_driver,
                collect_table_preview, self.comparator.compare_table_structure,
                "Table Preview", test_results
            )
        
        # Meta tags comparison
        if self.checks.get("meta", True):
            self.test_utilities.collect_and_compare(
                legacy_driver, modern_driver,
                collect_meta, self.comparator.compare_meta_structure,
                "Meta Tags", test_results
            )
        
        return test_results
    
    def run_modern_feature_comparisons(self, legacy_driver, modern_driver, test_results: Dict) -> Dict:
        """Run modern web feature comparisons."""
        logger.info("Running modern feature comparisons...")
        
        # Accessibility comparison
        if self.checks.get("accessibility", True):
            self.test_utilities.collect_and_compare(
                legacy_driver, modern_driver,
                collect_accessibility, self.comparator.compare_accessibility_structure,
                "Accessibility", test_results
            )
        
        # Breadcrumbs comparison
        if self.checks.get("breadcrumbs", True):
            self.test_utilities.collect_and_compare(
                legacy_driver, modern_driver,
                collect_breadcrumbs, lambda a, b: self.comparator.compare_lists(a, b, ComparisonType.EXACT_TEXT),
                "Breadcrumbs", test_results
            )
        
        # Tabs comparison
        if self.checks.get("tabs", True):
            self.test_utilities.collect_and_compare(
                legacy_driver, modern_driver,
                collect_tabs, lambda a, b: self.comparator.compare_interactive_elements(a, b, "tabs"),
                "Tabs", test_results
            )
        
        # Accordions comparison
        if self.checks.get("accordions", True):
            self.test_utilities.collect_and_compare(
                legacy_driver, modern_driver,
                collect_accordions, lambda a, b: self.comparator.compare_interactive_elements(a, b, "accordions"),
                "Accordions", test_results
            )
        
        # Pagination comparison
        if self.checks.get("pagination", True):
            self.test_utilities.collect_and_compare(
                legacy_driver, modern_driver,
                collect_pagination, self.comparator.compare_pagination,
                "Pagination", test_results
            )
        
        return test_results
    
    def run_comprehensive_list_comparisons(self, legacy_driver, modern_driver, test_results: Dict) -> Dict:
        """Run comprehensive list element comparisons."""
        logger.info("Running comprehensive list comparisons...")
        
        # All list elements comparison
        if self.checks.get("lists", True):
            self.test_utilities.collect_and_compare(
                legacy_driver, modern_driver,
                collect_all_lists, self.comparator.compare_list_structure,
                "All Lists", test_results
            )
        
        # Navigation lists comparison
        if self.checks.get("navigation_lists", True):
            self.test_utilities.collect_and_compare(
                legacy_driver, modern_driver,
                collect_navigation_lists, self.comparator.compare_navigation_structure,
                "Navigation Lists", test_results
            )
        
        # Breadcrumb lists comparison
        if self.checks.get("breadcrumb_lists", True):
            self.test_utilities.collect_and_compare(
                legacy_driver, modern_driver,
                collect_breadcrumb_lists, self.comparator.compare_breadcrumb_structure,
                "Breadcrumb Lists", test_results
            )
        
        # Feature lists comparison
        if self.checks.get("feature_lists", True):
            self.test_utilities.collect_and_compare(
                legacy_driver, modern_driver,
                collect_feature_lists, self.comparator.compare_feature_structure,
                "Feature Lists", test_results
            )
        
        return test_results
    
    def run_semantic_comparisons(self, legacy_driver, modern_driver, test_results: Dict) -> Dict:
        """Run semantic HTML element comparisons."""
        logger.info("Running semantic comparisons...")
        
        # All semantic content comparison
        if self.checks.get("semantic", True):
            self.test_utilities.collect_and_compare(
                legacy_driver, modern_driver,
                collect_all_semantic_content, self.comparator.compare_semantic_structure,
                "All Semantic Content", test_results
            )
        
        # Semantic elements comparison
        if self.checks.get("semantic_elements", True):
            self.test_utilities.collect_and_compare(
                legacy_driver, modern_driver,
                collect_semantic_elements, self.comparator.compare_semantic_elements,
                "Semantic Elements", test_results
            )
        
        # Interactive elements comparison
        if self.checks.get("interactive_elements", True):
            self.test_utilities.collect_and_compare(
                legacy_driver, modern_driver,
                collect_interactive_elements, self.comparator.compare_interactive_structure,
                "Interactive Elements", test_results
            )
        
        return test_results
    
    def run_form_structure_comparisons(self, legacy_driver, modern_driver, test_results: Dict) -> Dict:
        """Run form structure comparisons."""
        logger.info("Running form structure comparisons...")
        
        # Form structure comparison
        if self.checks.get("form_structure", True):
            self.test_utilities.collect_and_compare(
                legacy_driver, modern_driver,
                collect_form_structure, self.comparator.compare_form_structure_detailed,
                "Form Structure", test_results
            )
        
        # Form details comparison
        if self.checks.get("form_details", True):
            self.test_utilities.collect_and_compare(
                legacy_driver, modern_driver,
                collect_form_details, self.comparator.compare_form_details,
                "Form Details", test_results
            )
        
        return test_results
    
    def run_progress_graphics_comparisons(self, legacy_driver, modern_driver, test_results: Dict) -> Dict:
        """Run progress indicators and graphics comparisons."""
        logger.info("Running progress and graphics comparisons...")
        
        # Progress indicators comparison
        if self.checks.get("progress_indicators", True):
            self.test_utilities.collect_and_compare(
                legacy_driver, modern_driver,
                collect_progress_indicators, self.comparator.compare_progress_structure,
                "Progress Indicators", test_results
            )
        
        # Graphics elements comparison
        if self.checks.get("graphics_elements", True):
            self.test_utilities.collect_and_compare(
                legacy_driver, modern_driver,
                collect_graphics_elements, self.comparator.compare_graphics_structure,
                "Graphics Elements", test_results
            )
        
        return test_results
    
    def run_advanced_web_comparisons(self, legacy_driver, modern_driver, test_results: Dict) -> Dict:
        """Run advanced web feature comparisons."""
        logger.info("Running advanced web comparisons...")
        
        # Carousel slides comparison
        if self.checks.get("carousels", True):
            self.test_utilities.collect_and_compare(
                legacy_driver, modern_driver,
                collect_carousel_slides, self.comparator.compare_carousel_structure,
                "Carousel Slides", test_results
            )
        
        # Search functionality comparison
        if self.checks.get("search", True):
            self.test_utilities.collect_and_compare(
                legacy_driver, modern_driver,
                collect_search_functionality, self.comparator.compare_search_structure,
                "Search Functionality", test_results
            )
        
        # Notifications and alerts comparison
        if self.checks.get("notifications", True):
            self.test_utilities.collect_and_compare(
                legacy_driver, modern_driver,
                collect_notifications_alerts, self.comparator.compare_notification_structure,
                "Notifications and Alerts", test_results
            )
        
        # Loading states comparison
        if self.checks.get("loading_states", True):
            self.test_utilities.collect_and_compare(
                legacy_driver, modern_driver,
                collect_loading_states, self.comparator.compare_loading_structure,
                "Loading States", test_results
            )
        
        # Social media links comparison
        if self.checks.get("social_media", True):
            self.test_utilities.collect_and_compare(
                legacy_driver, modern_driver,
                collect_social_media_links, self.comparator.compare_social_structure,
                "Social Media Links", test_results
            )
        
        # Video and audio elements comparison
        if self.checks.get("media_elements", True):
            self.test_utilities.collect_and_compare(
                legacy_driver, modern_driver,
                collect_video_audio_elements, self.comparator.compare_media_structure,
                "Video and Audio Elements", test_results
            )
        
        return test_results
    
    def run_modern_framework_comparisons(self, legacy_driver, modern_driver, test_results: Dict) -> Dict:
        """Run modern framework-specific comparisons."""
        logger.info("Running modern framework comparisons...")
        
        # Data attributes comparison
        if self.checks.get("data_attributes", True):
            self.test_utilities.collect_and_compare(
                legacy_driver, modern_driver,
                collect_data_attributes, self.comparator.compare_data_attributes,
                "Data Attributes", test_results
            )
        
        # Custom elements comparison
        if self.checks.get("custom_elements", True):
            self.test_utilities.collect_and_compare(
                legacy_driver, modern_driver,
                collect_custom_elements, self.comparator.compare_custom_elements,
                "Custom Elements", test_results
            )
        
        # Analytics tracking comparison
        if self.checks.get("analytics", True):
            self.test_utilities.collect_and_compare(
                legacy_driver, modern_driver,
                collect_analytics_tracking, self.comparator.compare_analytics_structure,
                "Analytics Tracking", test_results
            )
        
        # Error states comparison
        if self.checks.get("error_states", True):
            self.test_utilities.collect_and_compare(
                legacy_driver, modern_driver,
                collect_error_states, self.comparator.compare_error_structure,
                "Error States", test_results
            )
        
        # Theme colors comparison
        if self.checks.get("theme_colors", True):
            self.test_utilities.collect_and_compare(
                legacy_driver, modern_driver,
                collect_theme_colors, self.comparator.compare_theme_structure,
                "Theme Colors", test_results
            )
        
        return test_results
    
    def run_iframe_comparisons(self, legacy_driver, modern_driver, test_results: Dict) -> Dict:
        """Run comprehensive iframe-aware comparisons."""
        logger.info("Running iframe-aware comparisons...")
        
        # Iframe-aware page title comparison
        self.test_utilities.collect_and_compare(
            legacy_driver, modern_driver,
            page_title_with_iframes, self._compare_iframe_data,
            "Page Titles with Iframes", test_results
        )
        
        # Iframe-aware headings comparison
        self.test_utilities.collect_and_compare(
            legacy_driver, modern_driver,
            heading_texts_with_iframes, self._compare_iframe_data,
            "Headings with Iframes", test_results
        )
        
        # Iframe-aware button texts comparison
        self.test_utilities.collect_and_compare(
            legacy_driver, modern_driver,
            button_texts_with_iframes, self._compare_iframe_data,
            "Button Texts with Iframes", test_results
        )
        
        # Iframe-aware links comparison
        self.test_utilities.collect_and_compare(
            legacy_driver, modern_driver,
            links_map_with_iframes, self._compare_iframe_data,
            "Links with Iframes", test_results
        )
        
        # Comprehensive iframe content comparison
        self.test_utilities.collect_and_compare(
            legacy_driver, modern_driver,
            collect_comprehensive_with_iframes, self._compare_comprehensive_iframe_data,
            "Comprehensive Iframe Content", test_results
        )
        
        return test_results
    
    def _compare_iframe_data(self, legacy_data: List[Dict], modern_data: List[Dict]) -> Any:
        """Compare iframe-aware data structures."""
        try:
            # Extract main document data
            legacy_main = next((item for item in legacy_data if item.get('iframe_context', {}).get('type') == 'main_document'), None)
            modern_main = next((item for item in modern_data if item.get('iframe_context', {}).get('type') == 'main_document'), None)
            
            # Extract iframe data
            legacy_iframes = [item for item in legacy_data if item.get('iframe_context', {}).get('type') != 'main_document']
            modern_iframes = [item for item in modern_data if item.get('iframe_context', {}).get('type') != 'main_document']
            
            # Compare main document
            main_comparison = self.comparator.compare_structure(legacy_main, modern_main) if legacy_main and modern_main else None
            
            # Compare iframe counts
            iframe_count_comparison = self.comparator.compare_numeric(len(legacy_iframes), len(modern_iframes))
            
            # Compare iframe content (simplified - just count elements)
            legacy_total_elements = sum(len(item.get('headings', [])) + len(item.get('buttons', [])) + len(item.get('links', [])) for item in legacy_iframes)
            modern_total_elements = sum(len(item.get('headings', [])) + len(item.get('buttons', [])) + len(item.get('links', [])) for item in modern_iframes)
            iframe_content_comparison = self.comparator.compare_numeric(legacy_total_elements, modern_total_elements)
            
            return {
                'main_document_match': main_comparison.success if main_comparison else False,
                'iframe_count_match': iframe_count_comparison.success,
                'iframe_content_match': iframe_content_comparison.success,
                'legacy_iframes': len(legacy_iframes),
                'modern_iframes': len(modern_iframes),
                'legacy_total_elements': legacy_total_elements,
                'modern_total_elements': modern_total_elements
            }
            
        except Exception as e:
            logger.error(f"Error comparing iframe data: {e}")
            return {'error': str(e)}
    
    def _compare_comprehensive_iframe_data(self, legacy_data: Dict, modern_data: Dict) -> Any:
        """Compare comprehensive iframe data structures."""
        try:
            # Compare main document
            main_doc_comparison = self.comparator.compare_structure(
                legacy_data.get('main_document', {}),
                modern_data.get('main_document', {})
            )
            
            # Compare iframe summaries
            legacy_summary = legacy_data.get('summary', {})
            modern_summary = modern_data.get('summary', {})
            
            iframe_summary_comparison = {
                'total_iframes_match': legacy_summary.get('total_iframes') == modern_summary.get('total_iframes'),
                'accessible_iframes_match': legacy_summary.get('accessible_iframes') == modern_summary.get('accessible_iframes'),
                'total_elements_match': abs(legacy_summary.get('total_elements', 0) - modern_summary.get('total_elements', 0)) <= 5  # Allow small differences
            }
            
            return {
                'main_document_match': main_doc_comparison.success,
                'iframe_summary': iframe_summary_comparison,
                'legacy_summary': legacy_summary,
                'modern_summary': modern_summary
            }
            
        except Exception as e:
            logger.error(f"Error comparing comprehensive iframe data: {e}")
            return {'error': str(e)}
    
    def run_comprehensive_page_comparisons(self, legacy_driver, modern_driver, test_results: Dict) -> Dict:
        """Run comprehensive page structure comparisons."""
        logger.info("Running comprehensive page comparisons...")
        
        # Page structure ordered comparison
        if self.checks.get("page_structure_ordered", True):
            self.test_utilities.collect_and_compare(
                legacy_driver, modern_driver,
                collect_page_structure_ordered, self.comparator.compare_page_structure_ordered,
                "Page Structure Ordered", test_results
            )
        
        # Page elements ordered comparison
        if self.checks.get("page_elements_ordered", True):
            self.test_utilities.collect_and_compare(
                legacy_driver, modern_driver,
                collect_page_elements_ordered, self.comparator.compare_page_elements_ordered,
                "Page Elements Ordered", test_results
            )
        
        # Page structure comparison
        if self.checks.get("page_structure", True):
            self.test_utilities.collect_and_compare(
                legacy_driver, modern_driver,
                collect_page_structure, self.comparator.compare_page_structure,
                "Page Structure", test_results
            )
        
        return test_results
    
    def run_semantic_field_comparisons(self, legacy_driver, modern_driver, test_results: Dict) -> Dict:
        """Run semantic field-level comparisons for logical equivalence."""
        logger.info("Running semantic field-level comparisons...")
        
        if not self.semantic_comparator:
            logger.warning("Semantic field comparator not initialized. Skipping semantic comparisons.")
            return test_results
        
        # Compare form fields semantically
        form_types = ['login', 'registration', 'search', 'contact']
        for form_type in form_types:
            try:
                form_results = self.semantic_comparator.compare_form_fields(
                    legacy_driver, modern_driver, form_type
                )
                
                if form_results.get('overall_match', False):
                    test_results['passed'] += 1
                    logger.info(f"✅ {form_type.title()} form fields match semantically")
                else:
                    test_results['failed'] += 1
                    logger.warning(f"❌ {form_type.title()} form fields don't match semantically")
                    logger.info(f"Missing fields: {form_results.get('missing_fields', [])}")
                    logger.info(f"Extra fields: {form_results.get('extra_fields', [])}")
                
            except Exception as e:
                test_results['errors'] += 1
                logger.error(f"Error comparing {form_type} form fields: {e}")
        
        # Compare navigation elements semantically
        try:
            nav_results = self.semantic_comparator.compare_navigation_elements(
                legacy_driver, modern_driver
            )
            
            if nav_results.get('overall_match', False):
                test_results['passed'] += 1
                logger.info("✅ Navigation elements match semantically")
            else:
                test_results['failed'] += 1
                logger.warning("❌ Navigation elements don't match semantically")
                logger.info(f"Missing nav items: {nav_results.get('missing_nav_items', [])}")
                logger.info(f"Extra nav items: {nav_results.get('extra_nav_items', [])}")
                
        except Exception as e:
            test_results['errors'] += 1
            logger.error(f"Error comparing navigation elements: {e}")
        
        # Compare action buttons semantically
        try:
            action_results = self.semantic_comparator.compare_action_buttons(
                legacy_driver, modern_driver
            )
            
            if action_results.get('overall_match', False):
                test_results['passed'] += 1
                logger.info("✅ Action buttons match semantically")
            else:
                test_results['failed'] += 1
                logger.warning("❌ Action buttons don't match semantically")
                logger.info(f"Missing actions: {action_results.get('missing_actions', [])}")
                logger.info(f"Extra actions: {action_results.get('extra_actions', [])}")
                
        except Exception as e:
            test_results['errors'] += 1
            logger.error(f"Error comparing action buttons: {e}")
        
        # Compare data display elements semantically
        try:
            display_results = self.semantic_comparator.compare_data_display_elements(
                legacy_driver, modern_driver
            )
            
            if display_results.get('overall_match', False):
                test_results['passed'] += 1
                logger.info("✅ Data display elements match semantically")
            else:
                test_results['failed'] += 1
                logger.warning("❌ Data display elements don't match semantically")
                logger.info(f"Missing displays: {display_results.get('missing_displays', [])}")
                logger.info(f"Extra displays: {display_results.get('extra_displays', [])}")
                
        except Exception as e:
            test_results['errors'] += 1
            logger.error(f"Error comparing data display elements: {e}")
        
        return test_results
    
    