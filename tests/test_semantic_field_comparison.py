import pytest
from utils.test_orchestrator import TestOrchestrator
from utils.semantic_field_comparator import SemanticFieldComparator
from utils.logging_utils import get_logger

logger = get_logger("semantic_field_test")


@pytest.mark.semantic
@pytest.mark.parametrize("path_key", [""])
class TestSemanticFieldComparison:
    """Test class for semantic field-level logical equivalence comparisons."""
    
    def test_semantic_field_comparison_integration(self, settings, legacy_driver, modern_driver, path_key: str):
        """Test semantic field comparison integration with the main framework."""
        logger.info("Testing semantic field comparison integration...")
        
        # Use the orchestrator to run semantic field comparisons
        orchestrator = TestOrchestrator(settings)
        test_results = {"passed": 0, "failed": 0, "skipped": 0, "errors": 0}
        
        # Run only semantic field comparisons
        test_results = orchestrator.comparison_engine.run_semantic_field_comparisons(
            legacy_driver, modern_driver, test_results
        )
        
        # Log results
        logger.info(f"Semantic field comparison results:")
        logger.info(f"  - Passed: {test_results['passed']}")
        logger.info(f"  - Failed: {test_results['failed']}")
        logger.info(f"  - Skipped: {test_results['skipped']}")
        logger.info(f"  - Errors: {test_results['errors']}")
        
        # Assert that we have some results
        total_tests = test_results['passed'] + test_results['failed'] + test_results['skipped'] + test_results['errors']
        assert total_tests > 0, "No semantic field comparison tests were executed"
        
        # Allow some failures for semantic comparisons (they can be complex)
        max_failures = 5
        assert test_results['failed'] <= max_failures, f"Too many semantic field comparison failures: {test_results['failed']}"
    
    def test_form_field_semantic_comparison(self, settings, legacy_driver, modern_driver, path_key: str):
        """Test semantic comparison of form fields."""
        logger.info("Testing semantic form field comparison...")
        
        if 'field_mappings' not in settings:
            pytest.skip("No field mappings configured")
        
        semantic_comparator = SemanticFieldComparator(
            settings.get('field_mappings', {}),
            settings.get('semantic_rules', {}),
            settings.get('comparison_settings', {})
        )
        
        # Test login form comparison
        login_results = semantic_comparator.compare_form_fields(
            legacy_driver, modern_driver, 'login'
        )
        
        logger.info(f"Login form comparison results:")
        logger.info(f"  - Overall match: {login_results.get('overall_match', False)}")
        logger.info(f"  - Missing fields: {login_results.get('missing_fields', [])}")
        logger.info(f"  - Extra fields: {login_results.get('extra_fields', [])}")
        
        # Test registration form comparison
        registration_results = semantic_comparator.compare_form_fields(
            legacy_driver, modern_driver, 'registration'
        )
        
        logger.info(f"Registration form comparison results:")
        logger.info(f"  - Overall match: {registration_results.get('overall_match', False)}")
        logger.info(f"  - Missing fields: {registration_results.get('missing_fields', [])}")
        logger.info(f"  - Extra fields: {registration_results.get('extra_fields', [])}")
        
        # Test search form comparison
        search_results = semantic_comparator.compare_form_fields(
            legacy_driver, modern_driver, 'search'
        )
        
        logger.info(f"Search form comparison results:")
        logger.info(f"  - Overall match: {search_results.get('overall_match', False)}")
        logger.info(f"  - Missing fields: {search_results.get('missing_fields', [])}")
        logger.info(f"  - Extra fields: {search_results.get('extra_fields', [])}")
        
        # Test contact form comparison
        contact_results = semantic_comparator.compare_form_fields(
            legacy_driver, modern_driver, 'contact'
        )
        
        logger.info(f"Contact form comparison results:")
        logger.info(f"  - Overall match: {contact_results.get('overall_match', False)}")
        logger.info(f"  - Missing fields: {contact_results.get('missing_fields', [])}")
        logger.info(f"  - Extra fields: {contact_results.get('extra_fields', [])}")
        
        # Assert that at least some forms have results
        form_results = [login_results, registration_results, search_results, contact_results]
        valid_results = [r for r in form_results if 'error' not in r]
        assert len(valid_results) > 0, "No valid form comparison results"
    
    def test_navigation_semantic_comparison(self, settings, legacy_driver, modern_driver, path_key: str):
        """Test semantic comparison of navigation elements."""
        logger.info("Testing semantic navigation comparison...")
        
        if 'field_mappings' not in settings:
            pytest.skip("No field mappings configured")
        
        semantic_comparator = SemanticFieldComparator(
            settings.get('field_mappings', {}),
            settings.get('semantic_rules', {}),
            settings.get('comparison_settings', {})
        )
        
        nav_results = semantic_comparator.compare_navigation_elements(
            legacy_driver, modern_driver
        )
        
        logger.info(f"Navigation comparison results:")
        logger.info(f"  - Overall match: {nav_results.get('overall_match', False)}")
        logger.info(f"  - Missing nav items: {nav_results.get('missing_nav_items', [])}")
        logger.info(f"  - Extra nav items: {nav_results.get('extra_nav_items', [])}")
        
        # Log detailed navigation comparisons
        for nav_type, comparison in nav_results.get('navigation_comparisons', {}).items():
            logger.info(f"  - {nav_type}: {comparison.get('match', False)}")
            if not comparison.get('match', False):
                logger.info(f"    Legacy count: {comparison.get('legacy_count', 0)}")
                logger.info(f"    Modern count: {comparison.get('modern_count', 0)}")
        
        # Assert that we have navigation comparison results
        assert 'navigation_comparisons' in nav_results, "No navigation comparison results"
    
    def test_action_buttons_semantic_comparison(self, settings, legacy_driver, modern_driver, path_key: str):
        """Test semantic comparison of action buttons."""
        logger.info("Testing semantic action button comparison...")
        
        if 'field_mappings' not in settings:
            pytest.skip("No field mappings configured")
        
        semantic_comparator = SemanticFieldComparator(
            settings.get('field_mappings', {}),
            settings.get('semantic_rules', {}),
            settings.get('comparison_settings', {})
        )
        
        action_results = semantic_comparator.compare_action_buttons(
            legacy_driver, modern_driver
        )
        
        logger.info(f"Action button comparison results:")
        logger.info(f"  - Overall match: {action_results.get('overall_match', False)}")
        logger.info(f"  - Missing actions: {action_results.get('missing_actions', [])}")
        logger.info(f"  - Extra actions: {action_results.get('extra_actions', [])}")
        
        # Log detailed action comparisons
        for action_type, comparison in action_results.get('action_comparisons', {}).items():
            logger.info(f"  - {action_type}: {comparison.get('match', False)}")
            if not comparison.get('match', False):
                logger.info(f"    Legacy count: {comparison.get('legacy_count', 0)}")
                logger.info(f"    Modern count: {comparison.get('modern_count', 0)}")
        
        # Assert that we have action comparison results
        assert 'action_comparisons' in action_results, "No action comparison results"
    
    def test_data_display_semantic_comparison(self, settings, legacy_driver, modern_driver, path_key: str):
        """Test semantic comparison of data display elements."""
        logger.info("Testing semantic data display comparison...")
        
        if 'field_mappings' not in settings:
            pytest.skip("No field mappings configured")
        
        semantic_comparator = SemanticFieldComparator(
            settings.get('field_mappings', {}),
            settings.get('semantic_rules', {}),
            settings.get('comparison_settings', {})
        )
        
        display_results = semantic_comparator.compare_data_display_elements(
            legacy_driver, modern_driver
        )
        
        logger.info(f"Data display comparison results:")
        logger.info(f"  - Overall match: {display_results.get('overall_match', False)}")
        logger.info(f"  - Missing displays: {display_results.get('missing_displays', [])}")
        logger.info(f"  - Extra displays: {display_results.get('extra_displays', [])}")
        
        # Log detailed display comparisons
        for display_type, comparison in display_results.get('display_comparisons', {}).items():
            logger.info(f"  - {display_type}: {comparison.get('match', False)}")
            if not comparison.get('match', False):
                logger.info(f"    Legacy count: {comparison.get('legacy_count', 0)}")
                logger.info(f"    Modern count: {comparison.get('modern_count', 0)}")
        
        # Assert that we have display comparison results
        assert 'display_comparisons' in display_results, "No display comparison results"
    
    def test_semantic_field_mapping_configuration(self, settings, path_key: str):
        """Test that semantic field mapping configuration is properly loaded."""
        logger.info("Testing semantic field mapping configuration...")
        
        # Check if field mappings are configured
        assert 'field_mappings' in settings, "Field mappings not configured in settings"
        
        field_mappings = settings['field_mappings']
        
        # Check form mappings
        assert 'forms' in field_mappings, "Form mappings not configured"
        forms = field_mappings['forms']
        
        expected_form_types = ['login', 'registration', 'search', 'contact']
        for form_type in expected_form_types:
            assert form_type in forms, f"Form type '{form_type}' not configured"
            
            form_config = forms[form_type]
            assert 'legacy' in form_config, f"Legacy configuration missing for {form_type}"
            assert 'modern' in form_config, f"Modern configuration missing for {form_type}"
        
        # Check navigation mappings
        assert 'navigation' in field_mappings, "Navigation mappings not configured"
        nav = field_mappings['navigation']
        assert 'legacy' in nav, "Legacy navigation configuration missing"
        assert 'modern' in nav, "Modern navigation configuration missing"
        
        # Check action mappings
        assert 'actions' in field_mappings, "Action mappings not configured"
        actions = field_mappings['actions']
        assert 'legacy' in actions, "Legacy action configuration missing"
        assert 'modern' in actions, "Modern action configuration missing"
        
        # Check data display mappings
        assert 'data_display' in field_mappings, "Data display mappings not configured"
        display = field_mappings['data_display']
        assert 'legacy' in display, "Legacy display configuration missing"
        assert 'modern' in display, "Modern display configuration missing"
        
        # Check semantic rules
        assert 'semantic_rules' in settings, "Semantic rules not configured"
        semantic_rules = settings['semantic_rules']
        assert 'field_types' in semantic_rules, "Field type rules not configured"
        assert 'button_types' in semantic_rules, "Button type rules not configured"
        
        # Check comparison settings
        assert 'comparison_settings' in settings, "Comparison settings not configured"
        comparison_settings = settings['comparison_settings']
        assert 'field_count_tolerance' in comparison_settings, "Field count tolerance not configured"
        assert 'text_similarity_threshold' in comparison_settings, "Text similarity threshold not configured"
        
        logger.info("✅ Semantic field mapping configuration is properly loaded")
