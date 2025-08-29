"""
Semantic Field Comparator - Compares elements based on their functional purpose rather than exact structure.
"""

from __future__ import annotations
import re
from typing import Dict, List, Any, Optional, Tuple
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from utils.logging_utils import get_logger
from fuzzywuzzy import fuzz

logger = get_logger("semantic_field_comparator")


class SemanticFieldComparator:
    """Compares UI elements based on their semantic meaning and functional purpose."""
    
    def __init__(self, field_mappings: Dict, semantic_rules: Dict, comparison_settings: Dict):
        self.field_mappings = field_mappings
        self.semantic_rules = semantic_rules
        self.comparison_settings = comparison_settings
        self.text_similarity_threshold = comparison_settings.get('text_similarity_threshold', 0.8)
        self.field_count_tolerance = comparison_settings.get('field_count_tolerance', 2)
    
    def compare_form_fields(self, legacy_driver: WebDriver, modern_driver: WebDriver, form_type: str) -> Dict[str, Any]:
        """Compare form fields between legacy and modern applications based on semantic mapping."""
        logger.info(f"Comparing {form_type} form fields semantically...")
        
        if form_type not in self.field_mappings.get('forms', {}):
            logger.warning(f"No field mappings found for form type: {form_type}")
            return {'error': f'No mappings for form type: {form_type}'}
        
        form_mapping = self.field_mappings['forms'][form_type]
        results = {
            'form_type': form_type,
            'field_comparisons': {},
            'overall_match': True,
            'missing_fields': [],
            'extra_fields': []
        }
        
        # Compare each field type
        for field_name, legacy_selectors in form_mapping.get('legacy', {}).items():
            modern_selectors = form_mapping.get('modern', {}).get(field_name, '')
            
            legacy_elements = self._find_elements_by_selectors(legacy_driver, legacy_selectors)
            modern_elements = self._find_elements_by_selectors(modern_driver, modern_selectors)
            
            field_comparison = self._compare_field_elements(
                field_name, legacy_elements, modern_elements
            )
            
            results['field_comparisons'][field_name] = field_comparison
            
            if not field_comparison['match']:
                results['overall_match'] = False
                if field_comparison['legacy_count'] == 0:
                    results['missing_fields'].append(f"legacy_{field_name}")
                if field_comparison['modern_count'] == 0:
                    results['missing_fields'].append(f"modern_{field_name}")
        
        # Check for extra fields in modern app
        for field_name, modern_selectors in form_mapping.get('modern', {}).items():
            if field_name not in form_mapping.get('legacy', {}):
                modern_elements = self._find_elements_by_selectors(modern_driver, modern_selectors)
                if modern_elements:
                    results['extra_fields'].append(field_name)
        
        logger.info(f"Form comparison results: {results['overall_match']}")
        return results
    
    def compare_navigation_elements(self, legacy_driver: WebDriver, modern_driver: WebDriver) -> Dict[str, Any]:
        """Compare navigation elements semantically."""
        logger.info("Comparing navigation elements semantically...")
        
        nav_mapping = self.field_mappings.get('navigation', {})
        results = {
            'navigation_comparisons': {},
            'overall_match': True,
            'missing_nav_items': [],
            'extra_nav_items': []
        }
        
        # Compare each navigation element type
        for nav_type, legacy_selectors in nav_mapping.get('legacy', {}).items():
            modern_selectors = nav_mapping.get('modern', {}).get(nav_type, '')
            
            legacy_elements = self._find_elements_by_selectors(legacy_driver, legacy_selectors)
            modern_elements = self._find_elements_by_selectors(modern_driver, modern_selectors)
            
            nav_comparison = self._compare_navigation_elements(
                nav_type, legacy_elements, modern_elements
            )
            
            results['navigation_comparisons'][nav_type] = nav_comparison
            
            if not nav_comparison['match']:
                results['overall_match'] = False
                if nav_comparison['legacy_count'] == 0:
                    results['missing_nav_items'].append(f"legacy_{nav_type}")
                if nav_comparison['modern_count'] == 0:
                    results['missing_nav_items'].append(f"modern_{nav_type}")
        
        return results
    
    def compare_action_buttons(self, legacy_driver: WebDriver, modern_driver: WebDriver) -> Dict[str, Any]:
        """Compare action buttons semantically."""
        logger.info("Comparing action buttons semantically...")
        
        action_mapping = self.field_mappings.get('actions', {})
        results = {
            'action_comparisons': {},
            'overall_match': True,
            'missing_actions': [],
            'extra_actions': []
        }
        
        # Compare each action button type
        for action_type, legacy_selectors in action_mapping.get('legacy', {}).items():
            modern_selectors = action_mapping.get('modern', {}).get(action_type, '')
            
            legacy_elements = self._find_elements_by_selectors(legacy_driver, legacy_selectors)
            modern_elements = self._find_elements_by_selectors(modern_driver, modern_selectors)
            
            action_comparison = self._compare_action_elements(
                action_type, legacy_elements, modern_elements
            )
            
            results['action_comparisons'][action_type] = action_comparison
            
            if not action_comparison['match']:
                results['overall_match'] = False
                if action_comparison['legacy_count'] == 0:
                    results['missing_actions'].append(f"legacy_{action_type}")
                if action_comparison['modern_count'] == 0:
                    results['missing_actions'].append(f"modern_{action_type}")
        
        return results
    
    def compare_data_display_elements(self, legacy_driver: WebDriver, modern_driver: WebDriver) -> Dict[str, Any]:
        """Compare data display elements semantically."""
        logger.info("Comparing data display elements semantically...")
        
        display_mapping = self.field_mappings.get('data_display', {})
        results = {
            'display_comparisons': {},
            'overall_match': True,
            'missing_displays': [],
            'extra_displays': []
        }
        
        # Compare each display element type
        for display_type, legacy_selectors in display_mapping.get('legacy', {}).items():
            modern_selectors = display_mapping.get('modern', {}).get(display_type, '')
            
            legacy_elements = self._find_elements_by_selectors(legacy_driver, legacy_selectors)
            modern_elements = self._find_elements_by_selectors(modern_driver, modern_selectors)
            
            display_comparison = self._compare_display_elements(
                display_type, legacy_elements, modern_elements
            )
            
            results['display_comparisons'][display_type] = display_comparison
            
            if not display_comparison['match']:
                results['overall_match'] = False
                if display_comparison['legacy_count'] == 0:
                    results['missing_displays'].append(f"legacy_{display_type}")
                if display_comparison['modern_count'] == 0:
                    results['missing_displays'].append(f"modern_{display_type}")
        
        return results
    
    def _find_elements_by_selectors(self, driver: WebDriver, selectors: str) -> List[WebElement]:
        """Find elements using multiple CSS selectors, handling :contains() pseudo-class."""
        if not selectors:
            return []
        
        elements = []
        selector_list = [s.strip() for s in selectors.split(',')]
        
        for selector in selector_list:
            try:
                # Check if selector contains :contains() pseudo-class
                if ':contains(' in selector:
                    elements.extend(self._find_elements_with_contains(driver, selector))
                else:
                    # Use regular CSS selector
                    found_elements = driver.find_elements("css selector", selector)
                    elements.extend(found_elements)
            except Exception as e:
                logger.warning(f"Error finding elements with selector '{selector}': {e}")
        
        return elements
    
    def _find_elements_with_contains(self, driver: WebDriver, selector: str) -> List[WebElement]:
        """Find elements using selectors with :contains() pseudo-class via JavaScript."""
        try:
            # Extract the base selector and the text to search for
            # Example: "button:contains('Login')" -> base: "button", text: "Login"
            if ':contains(' in selector:
                # Split on :contains( and extract the text
                parts = selector.split(':contains(')
                base_selector = parts[0].strip()
                text_part = parts[1].rstrip(')').strip()
                # Remove quotes if present
                search_text = text_part.strip("'\"")
                
                # Use JavaScript to find elements with the specified text
                js_script = f"""
                const elements = document.querySelectorAll('{base_selector}');
                const matchingElements = [];
                for (let element of elements) {{
                    if (element.textContent && element.textContent.toLowerCase().includes('{search_text.lower()}')) {{
                        matchingElements.push(element);
                    }}
                }}
                return matchingElements;
                """
                
                return driver.execute_script(js_script)
            else:
                return driver.find_elements("css selector", selector)
        except Exception as e:
            logger.warning(f"Error finding elements with contains selector '{selector}': {e}")
            return []
    
    def _compare_field_elements(self, field_name: str, legacy_elements: List[WebElement], 
                               modern_elements: List[WebElement]) -> Dict[str, Any]:
        """Compare form field elements semantically."""
        legacy_count = len(legacy_elements)
        modern_count = len(modern_elements)
        
        # Check if counts are within tolerance
        count_match = abs(legacy_count - modern_count) <= self.field_count_tolerance
        
        # Compare field properties
        field_properties = self._compare_field_properties(legacy_elements, modern_elements)
        
        # Compare field labels/placeholders
        label_match = self._compare_field_labels(legacy_elements, modern_elements)
        
        return {
            'field_name': field_name,
            'legacy_count': legacy_count,
            'modern_count': modern_count,
            'count_match': count_match,
            'properties_match': field_properties['match'],
            'label_match': label_match['match'],
            'match': count_match and field_properties['match'] and label_match['match'],
            'details': {
                'properties': field_properties,
                'labels': label_match
            }
        }
    
    def _compare_field_properties(self, legacy_elements: List[WebElement], 
                                 modern_elements: List[WebElement]) -> Dict[str, Any]:
        """Compare field properties like type, required, etc."""
        if not legacy_elements or not modern_elements:
            return {'match': False, 'reason': 'No elements to compare'}
        
        legacy_props = self._extract_field_properties(legacy_elements[0])
        modern_props = self._extract_field_properties(modern_elements[0])
        
        # Compare field types semantically
        type_match = self._compare_field_types(legacy_props.get('type'), modern_props.get('type'))
        
        # Compare required status
        required_match = legacy_props.get('required') == modern_props.get('required')
        
        return {
            'match': type_match and required_match,
            'type_match': type_match,
            'required_match': required_match,
            'legacy_properties': legacy_props,
            'modern_properties': modern_props
        }
    
    def _extract_field_properties(self, element: WebElement) -> Dict[str, Any]:
        """Extract properties from a form field element."""
        try:
            tag_name = element.tag_name.lower()
            field_type = element.get_attribute('type') or 'text'
            required = element.get_attribute('required') is not None
            placeholder = element.get_attribute('placeholder') or ''
            name = element.get_attribute('name') or ''
            id_attr = element.get_attribute('id') or ''
            
            return {
                'tag_name': tag_name,
                'type': field_type,
                'required': required,
                'placeholder': placeholder,
                'name': name,
                'id': id_attr
            }
        except Exception as e:
            logger.warning(f"Error extracting field properties: {e}")
            return {}
    
    def _compare_field_types(self, legacy_type: str, modern_type: str) -> bool:
        """Compare field types semantically."""
        if not legacy_type or not modern_type:
            return True  # Allow if type is not specified
        
        # Get semantic field type mappings
        field_types = self.semantic_rules.get('field_types', {})
        
        # Check if both types belong to the same semantic category
        for semantic_type, selectors in field_types.items():
            legacy_matches = any(legacy_type in selector for selector in selectors)
            modern_matches = any(modern_type in selector for selector in selectors)
            
            if legacy_matches and modern_matches:
                return True
        
        # Direct comparison as fallback
        return legacy_type == modern_type
    
    def _compare_field_labels(self, legacy_elements: List[WebElement], 
                             modern_elements: List[WebElement]) -> Dict[str, Any]:
        """Compare field labels and placeholders semantically."""
        if not legacy_elements or not modern_elements:
            return {'match': False, 'reason': 'No elements to compare'}
        
        legacy_text = self._extract_field_text(legacy_elements[0])
        modern_text = self._extract_field_text(modern_elements[0])
        
        # Use fuzzy matching for text comparison
        similarity = fuzz.ratio(legacy_text.lower(), modern_text.lower()) / 100.0
        text_match = similarity >= self.text_similarity_threshold
        
        return {
            'match': text_match,
            'similarity': similarity,
            'legacy_text': legacy_text,
            'modern_text': modern_text
        }
    
    def _extract_field_text(self, element: WebElement) -> str:
        """Extract text content from a field element."""
        try:
            # Try placeholder first
            placeholder = element.get_attribute('placeholder') or ''
            if placeholder:
                return placeholder
            
            # Try label text
            label = element.find_element("xpath", "preceding-sibling::label")
            if label:
                return label.text
            
            # Try aria-label
            aria_label = element.get_attribute('aria-label') or ''
            if aria_label:
                return aria_label
            
            # Try title attribute
            title = element.get_attribute('title') or ''
            if title:
                return title
            
            return ''
        except Exception:
            return ''
    
    def _compare_navigation_elements(self, nav_type: str, legacy_elements: List[WebElement], 
                                   modern_elements: List[WebElement]) -> Dict[str, Any]:
        """Compare navigation elements semantically."""
        legacy_count = len(legacy_elements)
        modern_count = len(modern_elements)
        
        count_match = abs(legacy_count - modern_count) <= self.field_count_tolerance
        
        # Compare navigation text/labels
        text_match = self._compare_navigation_text(legacy_elements, modern_elements)
        
        return {
            'nav_type': nav_type,
            'legacy_count': legacy_count,
            'modern_count': modern_count,
            'count_match': count_match,
            'text_match': text_match['match'],
            'match': count_match and text_match['match'],
            'details': text_match
        }
    
    def _compare_navigation_text(self, legacy_elements: List[WebElement], 
                                modern_elements: List[WebElement]) -> Dict[str, Any]:
        """Compare navigation text content."""
        if not legacy_elements or not modern_elements:
            return {'match': False, 'reason': 'No elements to compare'}
        
        legacy_text = legacy_elements[0].text.strip()
        modern_text = modern_elements[0].text.strip()
        
        similarity = fuzz.ratio(legacy_text.lower(), modern_text.lower()) / 100.0
        text_match = similarity >= self.text_similarity_threshold
        
        return {
            'match': text_match,
            'similarity': similarity,
            'legacy_text': legacy_text,
            'modern_text': modern_text
        }
    
    def _compare_action_elements(self, action_type: str, legacy_elements: List[WebElement], 
                               modern_elements: List[WebElement]) -> Dict[str, Any]:
        """Compare action elements semantically."""
        legacy_count = len(legacy_elements)
        modern_count = len(modern_elements)
        
        count_match = abs(legacy_count - modern_count) <= self.field_count_tolerance
        
        # Compare action text
        text_match = self._compare_action_text(legacy_elements, modern_elements)
        
        # Compare action types
        type_match = self._compare_action_types(legacy_elements, modern_elements)
        
        return {
            'action_type': action_type,
            'legacy_count': legacy_count,
            'modern_count': modern_count,
            'count_match': count_match,
            'text_match': text_match['match'],
            'type_match': type_match['match'],
            'match': count_match and text_match['match'] and type_match['match'],
            'details': {
                'text': text_match,
                'type': type_match
            }
        }
    
    def _compare_action_text(self, legacy_elements: List[WebElement], 
                           modern_elements: List[WebElement]) -> Dict[str, Any]:
        """Compare action button text."""
        if not legacy_elements or not modern_elements:
            return {'match': False, 'reason': 'No elements to compare'}
        
        legacy_text = legacy_elements[0].text.strip()
        modern_text = modern_elements[0].text.strip()
        
        similarity = fuzz.ratio(legacy_text.lower(), modern_text.lower()) / 100.0
        text_match = similarity >= self.text_similarity_threshold
        
        return {
            'match': text_match,
            'similarity': similarity,
            'legacy_text': legacy_text,
            'modern_text': modern_text
        }
    
    def _compare_action_types(self, legacy_elements: List[WebElement], 
                            modern_elements: List[WebElement]) -> Dict[str, Any]:
        """Compare action button types semantically."""
        if not legacy_elements or not modern_elements:
            return {'match': False, 'reason': 'No elements to compare'}
        
        legacy_type = self._extract_action_type(legacy_elements[0])
        modern_type = self._extract_action_type(modern_elements[0])
        
        # Get semantic button type mappings
        button_types = self.semantic_rules.get('button_types', {})
        
        # Check if both types belong to the same semantic category
        for semantic_type, selectors in button_types.items():
            legacy_matches = any(legacy_type in selector for selector in selectors)
            modern_matches = any(modern_type in selector for selector in selectors)
            
            if legacy_matches and modern_matches:
                return {'match': True, 'semantic_type': semantic_type}
        
        # Direct comparison as fallback
        type_match = legacy_type == modern_type
        
        return {
            'match': type_match,
            'legacy_type': legacy_type,
            'modern_type': modern_type
        }
    
    def _extract_action_type(self, element: WebElement) -> str:
        """Extract action type from an element."""
        try:
            # Check for submit type
            if element.get_attribute('type') == 'submit':
                return 'submit'
            
            # Check for button type
            if element.tag_name.lower() == 'button':
                return 'button'
            
            # Check for input type
            if element.tag_name.lower() == 'input':
                return element.get_attribute('type') or 'text'
            
            # Check for link type
            if element.tag_name.lower() == 'a':
                return 'link'
            
            return 'unknown'
        except Exception:
            return 'unknown'
    
    def _compare_display_elements(self, display_type: str, legacy_elements: List[WebElement], 
                                modern_elements: List[WebElement]) -> Dict[str, Any]:
        """Compare data display elements semantically."""
        legacy_count = len(legacy_elements)
        modern_count = len(modern_elements)
        
        count_match = abs(legacy_count - modern_count) <= self.field_count_tolerance
        
        # Compare display structure
        structure_match = self._compare_display_structure(legacy_elements, modern_elements)
        
        return {
            'display_type': display_type,
            'legacy_count': legacy_count,
            'modern_count': modern_count,
            'count_match': count_match,
            'structure_match': structure_match['match'],
            'match': count_match and structure_match['match'],
            'details': structure_match
        }
    
    def _compare_display_structure(self, legacy_elements: List[WebElement], 
                                 modern_elements: List[WebElement]) -> Dict[str, Any]:
        """Compare display structure semantically."""
        if not legacy_elements or not modern_elements:
            return {'match': False, 'reason': 'No elements to compare'}
        
        legacy_structure = self._extract_display_structure(legacy_elements[0])
        modern_structure = self._extract_display_structure(modern_elements[0])
        
        # Check structural equivalence
        structural_equivalence = self.comparison_settings.get('structural_equivalence', [])
        
        for equivalent_group in structural_equivalence:
            if (legacy_structure['tag_name'] in equivalent_group and 
                modern_structure['tag_name'] in equivalent_group):
                return {'match': True, 'equivalent_group': equivalent_group}
        
        # Direct comparison as fallback
        structure_match = legacy_structure['tag_name'] == modern_structure['tag_name']
        
        return {
            'match': structure_match,
            'legacy_structure': legacy_structure,
            'modern_structure': modern_structure
        }
    
    def _extract_display_structure(self, element: WebElement) -> Dict[str, Any]:
        """Extract display structure information."""
        try:
            tag_name = element.tag_name.lower()
            role = element.get_attribute('role') or ''
            class_name = element.get_attribute('class') or ''
            
            return {
                'tag_name': tag_name,
                'role': role,
                'class': class_name
            }
        except Exception as e:
            logger.warning(f"Error extracting display structure: {e}")
            return {'tag_name': 'unknown', 'role': '', 'class': ''}
