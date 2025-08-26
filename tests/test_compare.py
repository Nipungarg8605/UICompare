
import pytest
from utils.test_orchestrator import TestOrchestrator


@pytest.mark.compare
@pytest.mark.parametrize("path_key", [""])
class TestComparisonClean:
    """Clean comparison test class with separated implementation details."""
    
    def test_compare(self, settings, legacy_driver, modern_driver, path_key: str):
       
        orchestrator = TestOrchestrator(settings)
        test_results = orchestrator.run_comparison_test(legacy_driver, modern_driver, path_key)
        orchestrator.assert_test_success(test_results)