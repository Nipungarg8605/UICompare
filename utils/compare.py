from __future__ import annotations

import re
import logging
from typing import Dict, List, Tuple, Any
from difflib import SequenceMatcher
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class ComparisonType(Enum):
    """Types of comparisons supported by the framework."""
    EXACT_TEXT = "exact_text"
    FUZZY_TEXT = "fuzzy_text"
    SEMANTIC_TEXT = "semantic_text"
    PATTERN_MATCH = "pattern_match"
    STRUCTURE = "structure"
    COUNT = "count"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    NUMERIC_RANGE = "numeric_range"
    DATE_TIME = "date_time"
    URL_STRUCTURE = "url_structure"


class ComparisonResult:
    """Result of a comparison operation."""
    
    def __init__(self, success: bool, message: str = "", details: Dict[str, Any] = None, similarity_score: float = None):
        self.success = success
        self.message = message
        self.details = details or {}
        self.similarity_score = similarity_score
        self.timestamp = datetime.now()
    
    def __bool__(self) -> bool:
        return self.success
    
    def __str__(self) -> str:
        score_info = f" (similarity: {self.similarity_score:.2%})" if self.similarity_score is not None else ""
        return f"ComparisonResult(success={self.success}, message='{self.message}'{score_info})"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            "success": self.success,
            "message": self.message,
            "details": self.details,
            "similarity_score": self.similarity_score,
            "timestamp": self.timestamp.isoformat()
        }


class IntegratedComparator:
    """Integrated comparator that handles both text and structure comparisons."""
    
    def __init__(self, fuzzy_threshold: float = 0.9, semantic_threshold: float = 0.8, 
                 numeric_tolerance: float = 0.1, date_tolerance_seconds: int = 300):
        self.fuzzy_threshold = fuzzy_threshold
        self.semantic_threshold = semantic_threshold
        self.numeric_tolerance = numeric_tolerance
        self.date_tolerance_seconds = date_tolerance_seconds
        self._whitespace_re = re.compile(r"\s+")
        self._html_entity_re = re.compile(r"&[a-zA-Z0-9#]+;")
        self._url_re = re.compile(r"https?://[^\s]+")
        
        # Common HTML entities mapping
        self._html_entities = {
            "&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"', "&#39;": "'",
            "&nbsp;": " ", "&copy;": "©", "&reg;": "®", "&trade;": "™"
        }
    
    def normalize_text(self, value: str) -> str:
        """Normalize text by removing extra whitespace, HTML entities, and standardizing format."""
        if not value:
            return ""
        
        try:
            text = str(value).strip()
            
            # Decode HTML entities
            for entity, replacement in self._html_entities.items():
                text = text.replace(entity, replacement)
            
            # Remove extra whitespace
            text = self._whitespace_re.sub(" ", text)
            
            # Normalize quotes and dashes
            text = text.replace('"', '"').replace('"', '"')
            text = text.replace(''', "'").replace(''', "'")
            text = text.replace('–', '-').replace('—', '-')
            
            return text
        except Exception as e:
            logger.warning(f"Error normalizing text '{value}': {e}")
            return str(value) if value else ""
    
    def _safe_compare(self, a: Any, b: Any, operation: str) -> bool:
        """Safely compare two values with error handling."""
        try:
            if operation == "equals":
                return a == b
            elif operation == "contains":
                return a in b if hasattr(b, '__contains__') else False
            elif operation == "regex":
                return bool(re.search(a, b)) if isinstance(a, str) and isinstance(b, str) else False
            else:
                return False
        except Exception as e:
            logger.warning(f"Error in {operation} comparison: {e}")
            return False
    
    def compare_text(self, a: str, b: str, comparison_type: ComparisonType = ComparisonType.EXACT_TEXT, 
                    case_sensitive: bool = True) -> ComparisonResult:
        """Compare two text values using the specified comparison type."""
        try:
            a_norm = self.normalize_text(a)
            b_norm = self.normalize_text(b)
            
            if not case_sensitive:
                a_norm = a_norm.lower()
                b_norm = b_norm.lower()
            
            if comparison_type == ComparisonType.EXACT_TEXT:
                if a_norm == b_norm:
                    return ComparisonResult(True, "Text matches exactly")
                return ComparisonResult(False, f"Text mismatch:\nLEGACY: '{a_norm}'\nMODERN: '{b_norm}'")
            
            elif comparison_type == ComparisonType.FUZZY_TEXT:
                similarity = SequenceMatcher(None, a_norm, b_norm).ratio()
                if similarity >= self.fuzzy_threshold:
                    return ComparisonResult(True, f"Text similarity: {similarity:.2%}", similarity_score=similarity)
                return ComparisonResult(False, f"Text similarity {similarity:.2%} below threshold {self.fuzzy_threshold:.2%}:\nLEGACY: '{a_norm}'\nMODERN: '{b_norm}'", similarity_score=similarity)
            
            elif comparison_type == ComparisonType.SEMANTIC_TEXT:
                # Simple semantic comparison based on keyword matching
                a_words = set(a_norm.lower().split())
                b_words = set(b_norm.lower().split())
                if a_words and b_words:
                    intersection = a_words & b_words
                    union = a_words | b_words
                    similarity = len(intersection) / len(union) if union else 0
                    if similarity >= self.semantic_threshold:
                        return ComparisonResult(True, f"Semantic similarity: {similarity:.2%}", similarity_score=similarity)
                    return ComparisonResult(False, f"Semantic similarity {similarity:.2%} below threshold {self.semantic_threshold:.2%}", similarity_score=similarity)
                return ComparisonResult(False, "Cannot perform semantic comparison on empty text")
            
            elif comparison_type == ComparisonType.PATTERN_MATCH:
                # Treat 'a' as pattern and 'b' as text to match
                try:
                    if re.search(a_norm, b_norm, re.IGNORECASE):
                        return ComparisonResult(True, f"Pattern '{a_norm}' matches text")
                    return ComparisonResult(False, f"Pattern '{a_norm}' does not match text: '{b_norm}'")
                except re.error as e:
                    return ComparisonResult(False, f"Invalid regex pattern '{a_norm}': {e}")
            
            else:
                raise ValueError(f"Unsupported comparison type for text: {comparison_type}")
                
        except Exception as e:
            logger.error(f"Error in text comparison: {e}")
            return ComparisonResult(False, f"Text comparison failed: {e}")
    
    def compare_lists(self, a: List[str], b: List[str], comparison_type: ComparisonType = ComparisonType.EXACT_TEXT,
                     partial_match: bool = False) -> ComparisonResult:
        """Compare two lists of strings with enhanced options."""
        try:
            if comparison_type == ComparisonType.EXACT_TEXT:
                a_norm = [self.normalize_text(x) for x in a]
                b_norm = [self.normalize_text(x) for x in b]
                if a_norm == b_norm:
                    return ComparisonResult(True, f"Lists match exactly: {len(a_norm)} items")
                
                if partial_match:
                    # Check for partial matches
                    a_set = set(a_norm)
                    b_set = set(b_norm)
                    intersection = a_set & b_set
                    union = a_set | b_set
                    similarity = len(intersection) / len(union) if union else 0
                    if similarity >= self.fuzzy_threshold:
                        return ComparisonResult(True, f"Lists partially match: {similarity:.2%} similarity", similarity_score=similarity)
                
                return ComparisonResult(False, f"List mismatch:\nLEGACY: {a_norm}\nMODERN: {b_norm}")
            
            elif comparison_type == ComparisonType.COUNT:
                if len(a) == len(b):
                    return ComparisonResult(True, f"List count matches: {len(a)}")
                return ComparisonResult(False, f"List count differs: L={len(a)} M={len(b)}")
            
            elif comparison_type == ComparisonType.FUZZY_TEXT:
                # Compare lists using fuzzy matching
                if len(a) != len(b):
                    return ComparisonResult(False, f"List length differs: L={len(a)} M={len(b)}")
                
                total_similarity = 0
                for i, (ai, bi) in enumerate(zip(a, b)):
                    similarity = SequenceMatcher(None, self.normalize_text(ai), self.normalize_text(bi)).ratio()
                    total_similarity += similarity
                
                avg_similarity = total_similarity / len(a) if a else 0
                if avg_similarity >= self.fuzzy_threshold:
                    return ComparisonResult(True, f"Lists fuzzy match: {avg_similarity:.2%} average similarity", similarity_score=avg_similarity)
                return ComparisonResult(False, f"Lists fuzzy similarity {avg_similarity:.2%} below threshold", similarity_score=avg_similarity)
            
            else:
                raise ValueError(f"Unsupported comparison type for lists: {comparison_type}")
                
        except Exception as e:
            logger.error(f"Error in list comparison: {e}")
            return ComparisonResult(False, f"List comparison failed: {e}")
    
    def compare_links_map(self, a: List[Tuple[str, str]], b: List[Tuple[str, str]], 
                         compare_urls: bool = True, fuzzy_text: bool = False) -> ComparisonResult:
        """Compare link mappings with enhanced options."""
        try:
            if fuzzy_text:
                # Use fuzzy text comparison for link text
                a_norm = [(self.normalize_text(text), href) for text, href in a]
                b_norm = [(self.normalize_text(text), href) for text, href in b]
                
                # Compare using fuzzy matching
                if len(a_norm) != len(b_norm):
                    return ComparisonResult(False, f"Link count differs: L={len(a_norm)} M={len(b_norm)}")
                
                total_similarity = 0
                for i, ((a_text, a_href), (b_text, b_href)) in enumerate(zip(a_norm, b_norm)):
                    text_similarity = SequenceMatcher(None, a_text, b_text).ratio()
                    url_similarity = 1.0 if a_href == b_href else 0.0
                    total_similarity += (text_similarity + url_similarity) / 2
                
                avg_similarity = total_similarity / len(a_norm) if a_norm else 0
                if avg_similarity >= self.fuzzy_threshold:
                    return ComparisonResult(True, f"Links fuzzy match: {avg_similarity:.2%} similarity", similarity_score=avg_similarity)
                return ComparisonResult(False, f"Links fuzzy similarity {avg_similarity:.2%} below threshold", similarity_score=avg_similarity)
            else:
                # Original exact comparison logic
                a_norm = [(self.normalize_text(text), href) for text, href in a]
                b_norm = [(self.normalize_text(text), href) for text, href in b]
                
                if a_norm == b_norm:
                    return ComparisonResult(True, f"Links match exactly: {len(a_norm)} links")
                
                # Find differences
                a_set = set(a_norm)
                b_set = set(b_norm)
                only_in_legacy = a_set - b_set
                only_in_modern = b_set - a_set
                
                details = {
                    "legacy_count": len(a_norm),
                    "modern_count": len(b_norm),
                    "only_in_legacy": list(only_in_legacy),
                    "only_in_modern": list(only_in_modern)
                }
                
                return ComparisonResult(False, f"Links differ: L={len(a_norm)} M={len(b_norm)}", details)
                
        except Exception as e:
            logger.error(f"Error in links comparison: {e}")
            return ComparisonResult(False, f"Links comparison failed: {e}")
    
    def compare_table_structure(self, a: Dict[str, List], b: Dict[str, List]) -> ComparisonResult:
        """Compare table structure including headers and row data."""
        try:
            # Compare headers
            a_headers = [self.normalize_text(h) for h in a.get("headers", [])]
            b_headers = [self.normalize_text(h) for h in b.get("headers", [])]
            
            if a_headers != b_headers:
                return ComparisonResult(False, f"Table headers differ:\nLEGACY: {a_headers}\nMODERN: {b_headers}")
            
            # Compare rows
            a_rows = [[self.normalize_text(c) for c in row] for row in a.get("rows", [])]
            b_rows = [[self.normalize_text(c) for c in row] for row in b.get("rows", [])]
            
            if a_rows != b_rows:
                return ComparisonResult(False, f"Table rows differ:\nLEGACY: {a_rows}\nMODERN: {b_rows}")
            
            return ComparisonResult(True, f"Table structure matches: {len(a_headers)} columns, {len(a_rows)} rows")
        except Exception as e:
            logger.error(f"Error in table structure comparison: {e}")
            return ComparisonResult(False, f"Table structure comparison failed: {e}")
    
    def compare_form_structure(self, a: Dict[str, Any], b: Dict[str, Any]) -> ComparisonResult:
        """Compare form structure including inputs, labels, and validation."""
        try:
            a_inputs = a.get("inputs", [])
            b_inputs = b.get("inputs", [])
            
            # Compare input count
            if len(a_inputs) != len(b_inputs):
                return ComparisonResult(False, f"Form input count differs: L={len(a_inputs)} M={len(b_inputs)}")
            
            # Compare each input
            differences = []
            for i, (ai, bi) in enumerate(zip(a_inputs, b_inputs)):
                for field in ["name", "type", "label", "required", "placeholder"]:
                    a_val = str(ai.get(field, ""))
                    b_val = str(bi.get(field, ""))
                    if a_val != b_val:
                        differences.append(f"Input[{i}] {field}: L='{a_val}' M='{b_val}'")
            
            if differences:
                return ComparisonResult(False, f"Form structure differs:\n" + "\n".join(differences))
            
            return ComparisonResult(True, f"Form structure matches: {len(a_inputs)} inputs")
        except Exception as e:
            logger.error(f"Error in form structure comparison: {e}")
            return ComparisonResult(False, f"Form structure comparison failed: {e}")
    
    def compare_meta_structure(self, a: Dict[str, str], b: Dict[str, str], fuzzy_keys: List[str] = None) -> ComparisonResult:
        """Compare meta tag structure with fuzzy comparison for certain keys."""
        try:
            fuzzy_keys = fuzzy_keys or ["description", "og_description"]
            differences = []
            
            # Exact comparison for critical keys
            exact_keys = ["title", "robots", "canonical", "og_title"]
            for key in exact_keys:
                a_val = self.normalize_text(a.get(key, ""))
                b_val = self.normalize_text(b.get(key, ""))
                if a_val != b_val:
                    differences.append(f"Meta {key}: L='{a_val}' M='{b_val}'")
            
            # Fuzzy comparison for descriptive keys
            for key in fuzzy_keys:
                a_val = self.normalize_text(a.get(key, ""))
                b_val = self.normalize_text(b.get(key, ""))
                similarity = SequenceMatcher(None, a_val, b_val).ratio()
                if similarity < self.fuzzy_threshold:
                    differences.append(f"Meta {key} similarity {similarity:.2%}: L='{a_val}' M='{b_val}'")
            
            if differences:
                return ComparisonResult(False, f"Meta structure differs:\n" + "\n".join(differences))
            
            return ComparisonResult(True, "Meta structure matches")
        except Exception as e:
            logger.error(f"Error in meta structure comparison: {e}")
            return ComparisonResult(False, f"Meta structure comparison failed: {e}")
    
    def compare_accessibility_structure(self, a: Dict[str, int], b: Dict[str, int]) -> ComparisonResult:
        """Compare accessibility metrics and identify regressions."""
        try:
            regressions = []
            improvements = []
            
            for key, a_val in a.items():
                b_val = b.get(key, 0)
                if b_val > a_val:
                    regressions.append((key, a_val, b_val))
                elif b_val < a_val:
                    improvements.append((key, a_val, b_val))
            
            if regressions:
                reg_msg = ", ".join([f"{k}: {a_v}→{b_v}" for k, a_v, b_v in regressions])
                return ComparisonResult(False, f"Accessibility regressions: {reg_msg}")
            
            if improvements:
                imp_msg = ", ".join([f"{k}: {a_v}→{b_v}" for k, a_v, b_v in improvements])
                return ComparisonResult(True, f"Accessibility improvements: {imp_msg}")
            
            return ComparisonResult(True, "Accessibility metrics unchanged")
        except Exception as e:
            logger.error(f"Error in accessibility comparison: {e}")
            return ComparisonResult(False, f"Accessibility comparison failed: {e}")
    
    def compare_interactive_elements(self, a: List[Dict[str, Any]], b: List[Dict[str, Any]], element_type: str) -> ComparisonResult:
        """Compare interactive elements like tabs, accordions, etc."""
        try:
            if element_type == "tabs":
                a_norm = [(self.normalize_text(t.get("label", "")), bool(t.get("selected"))) for t in a]
                b_norm = [(self.normalize_text(t.get("label", "")), bool(t.get("selected"))) for t in b]
            elif element_type == "accordions":
                a_norm = [(self.normalize_text(t.get("text", "")), bool(t.get("expanded"))) for t in a]
                b_norm = [(self.normalize_text(t.get("text", "")), bool(t.get("expanded"))) for t in b]
            else:
                raise ValueError(f"Unsupported interactive element type: {element_type}")
            
            if a_norm == b_norm:
                return ComparisonResult(True, f"{element_type.title()} structure matches: {len(a_norm)} elements")
            
            return ComparisonResult(False, f"{element_type.title()} structure differs:\nLEGACY: {a_norm}\nMODERN: {b_norm}")
        except Exception as e:
            logger.error(f"Error in interactive elements comparison: {e}")
            return ComparisonResult(False, f"Interactive elements comparison failed: {e}")
    
    def compare_boolean_structure(self, a: Dict[str, bool], b: Dict[str, bool]) -> ComparisonResult:
        """Compare boolean structures like landmarks."""
        try:
            differences = []
            for key in a.keys() | b.keys():
                a_val = bool(a.get(key, False))
                b_val = bool(b.get(key, False))
                if a_val != b_val:
                    differences.append(f"{key}: L={a_val} M={b_val}")
            
            if differences:
                return ComparisonResult(False, f"Boolean structure differs:\n" + "\n".join(differences))
            
            return ComparisonResult(True, "Boolean structure matches")
        except Exception as e:
            logger.error(f"Error in boolean structure comparison: {e}")
            return ComparisonResult(False, f"Boolean structure comparison failed: {e}")
    
    def compare_performance_metrics(self, a: Dict[str, Any], b: Dict[str, Any], tolerance_ms: float = 500.0) -> ComparisonResult:
        """Compare performance metrics with tolerance."""
        try:
            differences = []
            for key in ["domContentLoaded", "loadEventEnd"]:
                a_val = float(a.get(key, 0) or 0)
                b_val = float(b.get(key, 0) or 0)
                diff = abs(a_val - b_val)
                if diff > tolerance_ms:
                    differences.append(f"{key}: L={a_val:.0f}ms M={b_val:.0f}ms (diff={diff:.0f}ms)")
            
            if differences:
                return ComparisonResult(False, f"Performance differs by >{tolerance_ms}ms:\n" + "\n".join(differences))
            
            return ComparisonResult(True, "Performance metrics within tolerance")
        except Exception as e:
            logger.error(f"Error in performance comparison: {e}")
            return ComparisonResult(False, f"Performance comparison failed: {e}")
    
    def compare_pagination(self, a: Dict[str, Any], b: Dict[str, Any]) -> ComparisonResult:
        """Compare pagination structure."""
        try:
            keys = ["current", "total", "has_next", "has_prev"]
            for k in keys:
                if str(a.get(k, "")) != str(b.get(k, "")):
                    return ComparisonResult(False, f"Pagination {k} differs: L='{a.get(k)}' M='{b.get(k)}'")
            return ComparisonResult(True, "Pagination structure matches")
        except Exception as e:
            logger.error(f"Error in pagination comparison: {e}")
            return ComparisonResult(False, f"Pagination comparison failed: {e}")
    
    def compare_widgets(self, a: Dict[str, List[str]], b: Dict[str, List[str]]) -> ComparisonResult:
        """Compare widgets structure."""
        try:
            for k in ["toasts", "dialogs", "tooltips"]:
                if a.get(k, []) != b.get(k, []):
                    return ComparisonResult(False, f"Widgets {k} differ: L={a.get(k, [])} M={b.get(k, [])}")
            return ComparisonResult(True, "Widgets structure matches")
        except Exception as e:
            logger.error(f"Error in widgets comparison: {e}")
            return ComparisonResult(False, f"Widgets comparison failed: {e}")
    
    def compare_images_preview(self, a: List[Dict[str, Any]], b: List[Dict[str, Any]], max_compare: int = 10) -> ComparisonResult:
        """Compare images preview structure."""
        try:
            an = a[:max_compare]
            bn = b[:max_compare]
            if len(an) != len(bn):
                return ComparisonResult(False, f"Images count differs: L={len(an)} M={len(bn)}")
            for i, (ai, bi) in enumerate(zip(an, bn)):
                for k in ["alt", "loading"]:
                    if self.normalize_text(str(ai.get(k, ""))) != self.normalize_text(str(bi.get(k, ""))):
                        return ComparisonResult(False, f"Image[{i}] {k} differs: L='{ai.get(k)}' M='{bi.get(k)}'")
            return ComparisonResult(True, f"Images structure matches: {len(an)} images")
        except Exception as e:
            logger.error(f"Error in images comparison: {e}")
            return ComparisonResult(False, f"Images comparison failed: {e}")
    
    def compare_interactive_roles(self, a: List[Tuple[str, str]], b: List[Tuple[str, str]], max_compare: int = 50) -> ComparisonResult:
        """Compare interactive roles structure."""
        try:
            an = a[:max_compare]
            bn = b[:max_compare]
            if an == bn:
                return ComparisonResult(True, f"Interactive roles match: {len(an)} roles")
            return ComparisonResult(False, f"Interactive roles differ: L={an} M={bn}")
        except Exception as e:
            logger.error(f"Error in interactive roles comparison: {e}")
            return ComparisonResult(False, f"Interactive roles comparison failed: {e}")
    
    def compare_i18n(self, a: Dict[str, str], b: Dict[str, str]) -> ComparisonResult:
        """Compare i18n structure."""
        try:
            for k in ["lang"]:
                if (a.get(k, "") or "").lower() != (b.get(k, "") or "").lower():
                    return ComparisonResult(False, f"i18n {k} differs: L='{a.get(k)}' M='{b.get(k)}'")
            return ComparisonResult(True, "i18n structure matches")
        except Exception as e:
            logger.error(f"Error in i18n comparison: {e}")
            return ComparisonResult(False, f"i18n comparison failed: {e}")

    # New comparator methods for modern web features

    def compare_carousel_structure(self, a: List[Dict[str, Any]], b: List[Dict[str, Any]]) -> ComparisonResult:
        """Compare carousel/slider configurations."""
        try:
            if len(a) != len(b):
                return ComparisonResult(False, f"Carousel count differs: L={len(a)} M={len(b)}")
            
            differences = []
            for i, (ai, bi) in enumerate(zip(a, b)):
                for key in ["total_slides", "total_indicators", "active_slide", "has_controls"]:
                    if ai.get(key) != bi.get(key):
                        differences.append(f"Carousel[{i}] {key}: L={ai.get(key)} M={bi.get(key)}")
            
            if differences:
                return ComparisonResult(False, f"Carousel structure differs:\n" + "\n".join(differences))
            
            return ComparisonResult(True, f"Carousel structure matches: {len(a)} carousels")
        except Exception as e:
            logger.error(f"Error in carousel comparison: {e}")
            return ComparisonResult(False, f"Carousel comparison failed: {e}")

    def compare_search_functionality(self, a: Dict[str, Any], b: Dict[str, Any]) -> ComparisonResult:
        """Compare search features and capabilities."""
        try:
            differences = []
            
            # Compare search inputs
            a_inputs = a.get("search_inputs", [])
            b_inputs = b.get("search_inputs", [])
            if len(a_inputs) != len(b_inputs):
                differences.append(f"Search inputs count: L={len(a_inputs)} M={len(b_inputs)}")
            
            # Compare search buttons
            a_buttons = a.get("search_buttons", [])
            b_buttons = b.get("search_buttons", [])
            if len(a_buttons) != len(b_buttons):
                differences.append(f"Search buttons count: L={len(a_buttons)} M={len(b_buttons)}")
            
            # Compare autocomplete
            a_autocomplete = a.get("has_autocomplete", False)
            b_autocomplete = b.get("has_autocomplete", False)
            if a_autocomplete != b_autocomplete:
                differences.append(f"Autocomplete: L={a_autocomplete} M={b_autocomplete}")
            
            if differences:
                return ComparisonResult(False, f"Search functionality differs:\n" + "\n".join(differences))
            
            return ComparisonResult(True, "Search functionality matches")
        except Exception as e:
            logger.error(f"Error in search functionality comparison: {e}")
            return ComparisonResult(False, f"Search functionality comparison failed: {e}")

    def compare_notification_systems(self, a: List[Dict[str, Any]], b: List[Dict[str, Any]]) -> ComparisonResult:
        """Compare notification patterns and systems."""
        try:
            if len(a) != len(b):
                return ComparisonResult(False, f"Notification count differs: L={len(a)} M={len(b)}")
            
            differences = []
            for i, (ai, bi) in enumerate(zip(a, b)):
                for key in ["text", "type", "aria_live", "visible"]:
                    if ai.get(key) != bi.get(key):
                        differences.append(f"Notification[{i}] {key}: L='{ai.get(key)}' M='{bi.get(key)}'")
            
            if differences:
                return ComparisonResult(False, f"Notification systems differ:\n" + "\n".join(differences))
            
            return ComparisonResult(True, f"Notification systems match: {len(a)} notifications")
        except Exception as e:
            logger.error(f"Error in notification comparison: {e}")
            return ComparisonResult(False, f"Notification comparison failed: {e}")

    def compare_loading_states(self, a: Dict[str, Any], b: Dict[str, Any]) -> ComparisonResult:
        """Compare loading states and indicators."""
        try:
            differences = []
            for key in ["spinners", "skeletons", "overlays", "total_loading_elements", "has_aria_busy", "has_loading_text"]:
                a_val = a.get(key, 0)
                b_val = b.get(key, 0)
                if a_val != b_val:
                    differences.append(f"Loading {key}: L={a_val} M={b_val}")
            
            if differences:
                return ComparisonResult(False, f"Loading states differ:\n" + "\n".join(differences))
            
            return ComparisonResult(True, "Loading states match")
        except Exception as e:
            logger.error(f"Error in loading states comparison: {e}")
            return ComparisonResult(False, f"Loading states comparison failed: {e}")

    def compare_social_media_integration(self, a: List[Dict[str, str]], b: List[Dict[str, str]]) -> ComparisonResult:
        """Compare social media links and sharing functionality."""
        try:
            if len(a) != len(b):
                return ComparisonResult(False, f"Social media links count differs: L={len(a)} M={len(b)}")
            
            differences = []
            for i, (ai, bi) in enumerate(zip(a, b)):
                for key in ["platform", "text", "href"]:
                    if ai.get(key) != bi.get(key):
                        differences.append(f"Social[{i}] {key}: L='{ai.get(key)}' M='{bi.get(key)}'")
            
            if differences:
                return ComparisonResult(False, f"Social media integration differs:\n" + "\n".join(differences))
            
            return ComparisonResult(True, f"Social media integration matches: {len(a)} links")
        except Exception as e:
            logger.error(f"Error in social media comparison: {e}")
            return ComparisonResult(False, f"Social media comparison failed: {e}")

    def compare_video_audio_content(self, a: Dict[str, Any], b: Dict[str, Any]) -> ComparisonResult:
        """Compare video and audio player configurations."""
        try:
            differences = []
            
            # Compare video configurations
            a_videos = a.get("videos", [])
            b_videos = b.get("videos", [])
            if len(a_videos) != len(b_videos):
                differences.append(f"Video count: L={len(a_videos)} M={len(b_videos)}")
            
            # Compare audio configurations
            a_audios = a.get("audios", [])
            b_audios = b.get("audios", [])
            if len(a_audios) != len(b_audios):
                differences.append(f"Audio count: L={len(a_audios)} M={len(b_audios)}")
            
            # Compare total media
            a_total = a.get("total_media", 0)
            b_total = b.get("total_media", 0)
            if a_total != b_total:
                differences.append(f"Total media: L={a_total} M={b_total}")
            
            if differences:
                return ComparisonResult(False, f"Media content differs:\n" + "\n".join(differences))
            
            return ComparisonResult(True, "Media content matches")
        except Exception as e:
            logger.error(f"Error in media content comparison: {e}")
            return ComparisonResult(False, f"Media content comparison failed: {e}")

    def compare_data_attributes(self, a: Dict[str, List[str]], b: Dict[str, List[str]]) -> ComparisonResult:
        """Compare framework-specific data attributes."""
        try:
            a_keys = set(a.keys())
            b_keys = set(b.keys())
            
            if a_keys != b_keys:
                only_in_legacy = a_keys - b_keys
                only_in_modern = b_keys - a_keys
                return ComparisonResult(False, f"Data attributes differ:\nOnly in legacy: {list(only_in_legacy)}\nOnly in modern: {list(only_in_modern)}")
            
            differences = []
            for key in a_keys:
                a_values = a[key]
                b_values = b[key]
                if a_values != b_values:
                    differences.append(f"Data attribute '{key}': L={a_values} M={b_values}")
            
            if differences:
                return ComparisonResult(False, f"Data attribute values differ:\n" + "\n".join(differences))
            
            return ComparisonResult(True, f"Data attributes match: {len(a_keys)} attributes")
        except Exception as e:
            logger.error(f"Error in data attributes comparison: {e}")
            return ComparisonResult(False, f"Data attributes comparison failed: {e}")

    def compare_custom_elements(self, a: List[str], b: List[str]) -> ComparisonResult:
        """Compare Web Components and custom HTML elements."""
        try:
            if a == b:
                return ComparisonResult(True, f"Custom elements match: {len(a)} elements")
            
            only_in_legacy = set(a) - set(b)
            only_in_modern = set(b) - set(a)
            
            details = {
                "legacy_elements": a,
                "modern_elements": b,
                "only_in_legacy": list(only_in_legacy),
                "only_in_modern": list(only_in_modern)
            }
            
            return ComparisonResult(False, f"Custom elements differ:\nOnly in legacy: {list(only_in_legacy)}\nOnly in modern: {list(only_in_modern)}", details)
        except Exception as e:
            logger.error(f"Error in custom elements comparison: {e}")
            return ComparisonResult(False, f"Custom elements comparison failed: {e}")

    def compare_analytics_implementation(self, a: Dict[str, Any], b: Dict[str, Any]) -> ComparisonResult:
        """Compare analytics and tracking implementations."""
        try:
            differences = []
            for key in ["google_analytics", "google_tag_manager", "facebook_pixel", "hotjar", "intercom", "segment", "custom_tracking", "data_layer", "gtm_data_layer", "tracking_attributes"]:
                a_val = a.get(key, False)
                b_val = b.get(key, False)
                if a_val != b_val:
                    differences.append(f"Analytics {key}: L={a_val} M={b_val}")
            
            if differences:
                return ComparisonResult(False, f"Analytics implementation differs:\n" + "\n".join(differences))
            
            return ComparisonResult(True, "Analytics implementation matches")
        except Exception as e:
            logger.error(f"Error in analytics comparison: {e}")
            return ComparisonResult(False, f"Analytics comparison failed: {e}")

    def compare_error_handling(self, a: List[Dict[str, Any]], b: List[Dict[str, Any]]) -> ComparisonResult:
        """Compare error states and validation patterns."""
        try:
            if len(a) != len(b):
                return ComparisonResult(False, f"Error count differs: L={len(a)} M={len(b)}")
            
            differences = []
            for i, (ai, bi) in enumerate(zip(a, b)):
                for key in ["text", "type", "role", "aria_live", "visible", "associated_field"]:
                    if ai.get(key) != bi.get(key):
                        differences.append(f"Error[{i}] {key}: L='{ai.get(key)}' M='{bi.get(key)}'")
            
            if differences:
                return ComparisonResult(False, f"Error handling differs:\n" + "\n".join(differences))
            
            return ComparisonResult(True, f"Error handling matches: {len(a)} errors")
        except Exception as e:
            logger.error(f"Error in error handling comparison: {e}")
            return ComparisonResult(False, f"Error handling comparison failed: {e}")

    def compare_theme_design(self, a: Dict[str, List[str]], b: Dict[str, List[str]]) -> ComparisonResult:
        """Compare design systems and theme configurations."""
        try:
            differences = []
            for key in ["background_colors", "text_colors", "accent_colors", "css_variables"]:
                a_values = a.get(key, [])
                b_values = b.get(key, [])
                if a_values != b_values:
                    differences.append(f"Theme {key}: L={a_values} M={b_values}")
            
            if differences:
                return ComparisonResult(False, f"Theme design differs:\n" + "\n".join(differences))
            
            return ComparisonResult(True, "Theme design matches")
        except Exception as e:
            logger.error(f"Error in theme design comparison: {e}")
            return ComparisonResult(False, f"Theme design comparison failed: {e}")

    def compare_page_architecture(self, a: Dict[str, Any], b: Dict[str, Any]) -> ComparisonResult:
        """Compare overall page structure and complexity."""
        try:
            differences = []
            for key in ["total_elements", "divs", "spans", "paragraphs", "sections", "articles", "asides", "lists", "list_items", "forms", "tables", "images", "links", "buttons", "inputs", "selects", "textareas", "iframes", "scripts", "styles", "meta_tags", "title_tags", "headings", "landmarks"]:
                a_val = a.get(key, 0)
                b_val = a.get(key, 0)
                if a_val != b_val:
                    differences.append(f"Architecture {key}: L={a_val} M={b_val}")
            
            # Compare ratios
            for key in ["element_density", "semantic_ratio", "interactive_ratio"]:
                a_val = a.get(key, 0)
                b_val = a.get(key, 0)
                if abs(a_val - b_val) > 0.1:  # 10% tolerance
                    differences.append(f"Architecture ratio {key}: L={a_val:.3f} M={b_val:.3f}")
            
            if differences:
                return ComparisonResult(False, f"Page architecture differs:\n" + "\n".join(differences))
            
            return ComparisonResult(True, "Page architecture matches")
        except Exception as e:
            logger.error(f"Error in page architecture comparison: {e}")
            return ComparisonResult(False, f"Page architecture comparison failed: {e}")

    def compare_with_weights(self, comparisons: List[Tuple[Any, Any, float, str]]) -> ComparisonResult:
        """Compare multiple aspects with weighted importance."""
        try:
            total_weight = 0
            weighted_score = 0
            details = {}
            
            for a, b, weight, description in comparisons:
                total_weight += weight
                result = self.compare_text(a, b) if isinstance(a, str) and isinstance(b, str) else self.compare_lists(a, b)
                score = result.similarity_score if result.similarity_score is not None else (1.0 if result.success else 0.0)
                weighted_score += score * weight
                details[description] = {
                    "success": result.success,
                    "score": score,
                    "weight": weight
                }
            
            if total_weight == 0:
                return ComparisonResult(False, "No valid comparisons provided")
            
            final_score = weighted_score / total_weight
            success = final_score >= self.fuzzy_threshold
            
            return ComparisonResult(
                success=success,
                message=f"Weighted comparison score: {final_score:.2%}",
                details=details,
                similarity_score=final_score
            )
        except Exception as e:
            logger.error(f"Error in weighted comparison: {e}")
            return ComparisonResult(False, f"Weighted comparison failed: {e}")


# Convenience functions for backward compatibility
def compare_texts(a: str, b: str) -> Tuple[bool, str]:
    """Legacy function for text comparison."""
    comparator = IntegratedComparator()
    result = comparator.compare_text(a, b, ComparisonType.EXACT_TEXT)
    return result.success, result.message


def compare_texts_fuzzy(a: str, b: str, threshold: float = 0.9) -> Tuple[bool, str]:
    """Legacy function for fuzzy text comparison."""
    comparator = IntegratedComparator(fuzzy_threshold=threshold)
    result = comparator.compare_text(a, b, ComparisonType.FUZZY_TEXT)
    return result.success, result.message


def normalize_text(value: str) -> str:
    """Legacy function for text normalization."""
    comparator = IntegratedComparator()
    return comparator.normalize_text(value)


# Additional comparison methods for comprehensive UI testing

def compare_list_structure(self, a: Dict[str, Any], b: Dict[str, Any]) -> ComparisonResult:
    """Compare list structure and content."""
    try:
        differences = []
        
        # Compare summary
        a_summary = a.get('summary', {})
        b_summary = b.get('summary', {})
        for key in ['total_ul', 'total_ol', 'total_li', 'total_nested_lists']:
            a_val = a_summary.get(key, 0)
            b_val = b_summary.get(key, 0)
            if a_val != b_val:
                differences.append(f"List summary {key}: L={a_val} M={b_val}")
        
        # Compare lists
        a_lists = a.get('lists', [])
        b_lists = b.get('lists', [])
        if len(a_lists) != len(b_lists):
            differences.append(f"Number of lists: L={len(a_lists)} M={len(b_lists)}")
        
        if differences:
            return ComparisonResult(False, f"List structure differs:\n" + "\n".join(differences))
        
        return ComparisonResult(True, "List structure matches")
    except Exception as e:
        logger.error(f"Error in list structure comparison: {e}")
        return ComparisonResult(False, f"List structure comparison failed: {e}")


def compare_navigation_structure(self, a: List[Dict[str, Any]], b: List[Dict[str, Any]]) -> ComparisonResult:
    """Compare navigation structure."""
    try:
        if len(a) != len(b):
            return ComparisonResult(False, f"Navigation count: L={len(a)} M={len(b)}")
        
        differences = []
        for i, (nav_a, nav_b) in enumerate(zip(a, b)):
            if nav_a.get('total_items') != nav_b.get('total_items'):
                differences.append(f"Navigation {i} items: L={nav_a.get('total_items')} M={nav_b.get('total_items')}")
        
        if differences:
            return ComparisonResult(False, f"Navigation structure differs:\n" + "\n".join(differences))
        
        return ComparisonResult(True, "Navigation structure matches")
    except Exception as e:
        logger.error(f"Error in navigation structure comparison: {e}")
        return ComparisonResult(False, f"Navigation structure comparison failed: {e}")


def compare_breadcrumb_structure(self, a: List[Dict[str, Any]], b: List[Dict[str, Any]]) -> ComparisonResult:
    """Compare breadcrumb structure."""
    try:
        if len(a) != len(b):
            return ComparisonResult(False, f"Breadcrumb count: L={len(a)} M={len(b)}")
        
        differences = []
        for i, (bread_a, bread_b) in enumerate(zip(a, b)):
            if bread_a.get('total_items') != bread_b.get('total_items'):
                differences.append(f"Breadcrumb {i} items: L={bread_a.get('total_items')} M={bread_b.get('total_items')}")
        
        if differences:
            return ComparisonResult(False, f"Breadcrumb structure differs:\n" + "\n".join(differences))
        
        return ComparisonResult(True, "Breadcrumb structure matches")
    except Exception as e:
        logger.error(f"Error in breadcrumb structure comparison: {e}")
        return ComparisonResult(False, f"Breadcrumb structure comparison failed: {e}")


def compare_feature_structure(self, a: List[Dict[str, Any]], b: List[Dict[str, Any]]) -> ComparisonResult:
    """Compare feature list structure."""
    try:
        if len(a) != len(b):
            return ComparisonResult(False, f"Feature list count: L={len(a)} M={len(b)}")
        
        differences = []
        for i, (feat_a, feat_b) in enumerate(zip(a, b)):
            if feat_a.get('total_items') != feat_b.get('total_items'):
                differences.append(f"Feature list {i} items: L={feat_a.get('total_items')} M={feat_b.get('total_items')}")
        
        if differences:
            return ComparisonResult(False, f"Feature structure differs:\n" + "\n".join(differences))
        
        return ComparisonResult(True, "Feature structure matches")
    except Exception as e:
        logger.error(f"Error in feature structure comparison: {e}")
        return ComparisonResult(False, f"Feature structure comparison failed: {e}")


def compare_semantic_structure(self, a: Dict[str, Any], b: Dict[str, Any]) -> ComparisonResult:
    """Compare semantic content structure."""
    try:
        differences = []
        a_summary = a.get('summary', {})
        b_summary = b.get('summary', {})
        
        for key in ['emphasis_elements', 'code_elements', 'quotations', 'definitions', 'time_elements', 'interactive_elements', 'form_structure', 'progress_indicators', 'graphics_elements']:
            a_val = a_summary.get(key, 0)
            b_val = b_summary.get(key, 0)
            if a_val != b_val:
                differences.append(f"Semantic {key}: L={a_val} M={b_val}")
        
        if differences:
            return ComparisonResult(False, f"Semantic structure differs:\n" + "\n".join(differences))
        
        return ComparisonResult(True, "Semantic structure matches")
    except Exception as e:
        logger.error(f"Error in semantic structure comparison: {e}")
        return ComparisonResult(False, f"Semantic structure comparison failed: {e}")


def compare_semantic_elements(self, a: Dict[str, List[Dict[str, Any]]], b: Dict[str, List[Dict[str, Any]]]) -> ComparisonResult:
    """Compare semantic elements."""
    try:
        differences = []
        for key in ['emphasis', 'code_elements', 'quotations', 'definitions', 'time_elements', 'abbreviations', 'content_changes']:
            a_elements = a.get(key, [])
            b_elements = b.get(key, [])
            if len(a_elements) != len(b_elements):
                differences.append(f"Semantic {key} count: L={len(a_elements)} M={len(b_elements)}")
        
        if differences:
            return ComparisonResult(False, f"Semantic elements differ:\n" + "\n".join(differences))
        
        return ComparisonResult(True, "Semantic elements match")
    except Exception as e:
        logger.error(f"Error in semantic elements comparison: {e}")
        return ComparisonResult(False, f"Semantic elements comparison failed: {e}")


def compare_interactive_structure(self, a: List[Dict[str, Any]], b: List[Dict[str, Any]]) -> ComparisonResult:
    """Compare interactive elements structure."""
    try:
        if len(a) != len(b):
            return ComparisonResult(False, f"Interactive elements count: L={len(a)} M={len(b)}")
        
        return ComparisonResult(True, "Interactive structure matches")
    except Exception as e:
        logger.error(f"Error in interactive structure comparison: {e}")
        return ComparisonResult(False, f"Interactive structure comparison failed: {e}")


def compare_form_structure_detailed(self, a: Dict[str, List[Dict[str, Any]]], b: Dict[str, List[Dict[str, Any]]]) -> ComparisonResult:
    """Compare detailed form structure."""
    try:
        differences = []
        for key in ['fieldsets', 'option_groups', 'options', 'datalists']:
            a_items = a.get(key, [])
            b_items = b.get(key, [])
            if len(a_items) != len(b_items):
                differences.append(f"Form {key} count: L={len(a_items)} M={len(b_items)}")
        
        if differences:
            return ComparisonResult(False, f"Form structure differs:\n" + "\n".join(differences))
        
        return ComparisonResult(True, "Form structure matches")
    except Exception as e:
        logger.error(f"Error in form structure comparison: {e}")
        return ComparisonResult(False, f"Form structure comparison failed: {e}")


def compare_form_details(self, a: Dict[str, Any], b: Dict[str, Any]) -> ComparisonResult:
    """Compare form details."""
    try:
        differences = []
        a_inputs = a.get('inputs', [])
        b_inputs = b.get('inputs', [])
        if len(a_inputs) != len(b_inputs):
            differences.append(f"Form inputs count: L={len(a_inputs)} M={len(b_inputs)}")
        
        a_validations = a.get('validations', [])
        b_validations = b.get('validations', [])
        if len(a_validations) != len(b_validations):
            differences.append(f"Form validations count: L={len(a_validations)} M={len(b_validations)}")
        
        if differences:
            return ComparisonResult(False, f"Form details differ:\n" + "\n".join(differences))
        
        return ComparisonResult(True, "Form details match")
    except Exception as e:
        logger.error(f"Error in form details comparison: {e}")
        return ComparisonResult(False, f"Form details comparison failed: {e}")


def compare_progress_structure(self, a: Dict[str, List[Dict[str, Any]]], b: Dict[str, List[Dict[str, Any]]]) -> ComparisonResult:
    """Compare progress indicators structure."""
    try:
        differences = []
        for key in ['progress_bars', 'meters', 'outputs']:
            a_items = a.get(key, [])
            b_items = b.get(key, [])
            if len(a_items) != len(b_items):
                differences.append(f"Progress {key} count: L={len(a_items)} M={len(b_items)}")
        
        if differences:
            return ComparisonResult(False, f"Progress structure differs:\n" + "\n".join(differences))
        
        return ComparisonResult(True, "Progress structure matches")
    except Exception as e:
        logger.error(f"Error in progress structure comparison: {e}")
        return ComparisonResult(False, f"Progress structure comparison failed: {e}")


def compare_graphics_structure(self, a: Dict[str, List[Dict[str, Any]]], b: Dict[str, List[Dict[str, Any]]]) -> ComparisonResult:
    """Compare graphics elements structure."""
    try:
        differences = []
        for key in ['canvas_elements', 'svg_elements', 'embedded_objects']:
            a_items = a.get(key, [])
            b_items = b.get(key, [])
            if len(a_items) != len(b_items):
                differences.append(f"Graphics {key} count: L={len(a_items)} M={len(b_items)}")
        
        if differences:
            return ComparisonResult(False, f"Graphics structure differs:\n" + "\n".join(differences))
        
        return ComparisonResult(True, "Graphics structure matches")
    except Exception as e:
        logger.error(f"Error in graphics structure comparison: {e}")
        return ComparisonResult(False, f"Graphics structure comparison failed: {e}")


def compare_carousel_structure(self, a: List[Dict[str, Any]], b: List[Dict[str, Any]]) -> ComparisonResult:
    """Compare carousel structure."""
    try:
        if len(a) != len(b):
            return ComparisonResult(False, f"Carousel count: L={len(a)} M={len(b)}")
        
        return ComparisonResult(True, "Carousel structure matches")
    except Exception as e:
        logger.error(f"Error in carousel structure comparison: {e}")
        return ComparisonResult(False, f"Carousel structure comparison failed: {e}")


def compare_search_structure(self, a: Dict[str, Any], b: Dict[str, Any]) -> ComparisonResult:
    """Compare search functionality structure."""
    try:
        differences = []
        a_inputs = a.get('search_inputs', [])
        b_inputs = b.get('search_inputs', [])
        if len(a_inputs) != len(b_inputs):
            differences.append(f"Search inputs count: L={len(a_inputs)} M={len(b_inputs)}")
        
        if differences:
            return ComparisonResult(False, f"Search structure differs:\n" + "\n".join(differences))
        
        return ComparisonResult(True, "Search structure matches")
    except Exception as e:
        logger.error(f"Error in search structure comparison: {e}")
        return ComparisonResult(False, f"Search structure comparison failed: {e}")


def compare_notification_structure(self, a: List[Dict[str, Any]], b: List[Dict[str, Any]]) -> ComparisonResult:
    """Compare notification structure."""
    try:
        if len(a) != len(b):
            return ComparisonResult(False, f"Notification count: L={len(a)} M={len(b)}")
        
        return ComparisonResult(True, "Notification structure matches")
    except Exception as e:
        logger.error(f"Error in notification structure comparison: {e}")
        return ComparisonResult(False, f"Notification structure comparison failed: {e}")


def compare_loading_structure(self, a: Dict[str, Any], b: Dict[str, Any]) -> ComparisonResult:
    """Compare loading states structure."""
    try:
        differences = []
        for key in ['spinners', 'skeletons', 'overlays', 'total_loading_elements']:
            a_val = a.get(key, 0)
            b_val = b.get(key, 0)
            if a_val != b_val:
                differences.append(f"Loading {key}: L={a_val} M={b_val}")
        
        if differences:
            return ComparisonResult(False, f"Loading structure differs:\n" + "\n".join(differences))
        
        return ComparisonResult(True, "Loading structure matches")
    except Exception as e:
        logger.error(f"Error in loading structure comparison: {e}")
        return ComparisonResult(False, f"Loading structure comparison failed: {e}")


def compare_social_structure(self, a: List[Dict[str, str]], b: List[Dict[str, str]]) -> ComparisonResult:
    """Compare social media structure."""
    try:
        if len(a) != len(b):
            return ComparisonResult(False, f"Social media count: L={len(a)} M={len(b)}")
        
        return ComparisonResult(True, "Social media structure matches")
    except Exception as e:
        logger.error(f"Error in social media structure comparison: {e}")
        return ComparisonResult(False, f"Social media structure comparison failed: {e}")


def compare_media_structure(self, a: Dict[str, Any], b: Dict[str, Any]) -> ComparisonResult:
    """Compare media elements structure."""
    try:
        differences = []
        for key in ['videos', 'audios', 'players', 'total_media']:
            a_val = a.get(key, 0) if key != 'videos' and key != 'audios' else len(a.get(key, []))
            b_val = b.get(key, 0) if key != 'videos' and key != 'audios' else len(b.get(key, []))
            if a_val != b_val:
                differences.append(f"Media {key}: L={a_val} M={b_val}")
        
        if differences:
            return ComparisonResult(False, f"Media structure differs:\n" + "\n".join(differences))
        
        return ComparisonResult(True, "Media structure matches")
    except Exception as e:
        logger.error(f"Error in media structure comparison: {e}")
        return ComparisonResult(False, f"Media structure comparison failed: {e}")


def compare_data_attributes(self, a: Dict[str, List[str]], b: Dict[str, List[str]]) -> ComparisonResult:
    """Compare data attributes."""
    try:
        if len(a) != len(b):
            return ComparisonResult(False, f"Data attributes count: L={len(a)} M={len(b)}")
        
        return ComparisonResult(True, "Data attributes match")
    except Exception as e:
        logger.error(f"Error in data attributes comparison: {e}")
        return ComparisonResult(False, f"Data attributes comparison failed: {e}")


def compare_custom_elements(self, a: List[str], b: List[str]) -> ComparisonResult:
    """Compare custom elements."""
    try:
        if len(a) != len(b):
            return ComparisonResult(False, f"Custom elements count: L={len(a)} M={len(b)}")
        
        return ComparisonResult(True, "Custom elements match")
    except Exception as e:
        logger.error(f"Error in custom elements comparison: {e}")
        return ComparisonResult(False, f"Custom elements comparison failed: {e}")


def compare_analytics_structure(self, a: Dict[str, Any], b: Dict[str, Any]) -> ComparisonResult:
    """Compare analytics tracking structure."""
    try:
        differences = []
        for key in ['google_analytics', 'google_tag_manager', 'facebook_pixel', 'hotjar', 'intercom', 'segment', 'custom_tracking', 'data_layer', 'gtm_data_layer', 'tracking_attributes']:
            a_val = a.get(key, False)
            b_val = b.get(key, False)
            if a_val != b_val:
                differences.append(f"Analytics {key}: L={a_val} M={b_val}")
        
        if differences:
            return ComparisonResult(False, f"Analytics structure differs:\n" + "\n".join(differences))
        
        return ComparisonResult(True, "Analytics structure matches")
    except Exception as e:
        logger.error(f"Error in analytics structure comparison: {e}")
        return ComparisonResult(False, f"Analytics structure comparison failed: {e}")


def compare_error_structure(self, a: List[Dict[str, Any]], b: List[Dict[str, Any]]) -> ComparisonResult:
    """Compare error states structure."""
    try:
        if len(a) != len(b):
            return ComparisonResult(False, f"Error states count: L={len(a)} M={len(b)}")
        
        return ComparisonResult(True, "Error structure matches")
    except Exception as e:
        logger.error(f"Error in error structure comparison: {e}")
        return ComparisonResult(False, f"Error structure comparison failed: {e}")


def compare_theme_structure(self, a: Dict[str, List[str]], b: Dict[str, List[str]]) -> ComparisonResult:
    """Compare theme structure."""
    try:
        differences = []
        for key in ['background_colors', 'text_colors', 'accent_colors', 'css_variables']:
            a_values = a.get(key, [])
            b_values = b.get(key, [])
            if len(a_values) != len(b_values):
                differences.append(f"Theme {key} count: L={len(a_values)} M={len(b_values)}")
        
        if differences:
            return ComparisonResult(False, f"Theme structure differs:\n" + "\n".join(differences))
        
        return ComparisonResult(True, "Theme structure matches")
    except Exception as e:
        logger.error(f"Error in theme structure comparison: {e}")
        return ComparisonResult(False, f"Theme structure comparison failed: {e}")


def compare_page_structure_ordered(self, a: Dict[str, Any], b: Dict[str, Any]) -> ComparisonResult:
    """Compare ordered page structure."""
    try:
        differences = []
        for key in ['title', 'headings', 'buttons', 'links', 'nav_links', 'form_elements', 'images']:
            a_items = a.get(key, [])
            b_items = b.get(key, [])
            if len(a_items) != len(b_items):
                differences.append(f"Page {key} count: L={len(a_items)} M={len(b_items)}")
        
        if differences:
            return ComparisonResult(False, f"Page structure differs:\n" + "\n".join(differences))
        
        return ComparisonResult(True, "Page structure matches")
    except Exception as e:
        logger.error(f"Error in page structure comparison: {e}")
        return ComparisonResult(False, f"Page structure comparison failed: {e}")


def compare_page_elements_ordered(self, a: Dict[str, List], b: Dict[str, List]) -> ComparisonResult:
    """Compare ordered page elements."""
    try:
        differences = []
        for key in ['headings', 'buttons', 'links', 'nav_links', 'form_elements', 'images', 'tables', 'lists', 'paragraphs', 'divs']:
            a_items = a.get(key, [])
            b_items = b.get(key, [])
            if len(a_items) != len(b_items):
                differences.append(f"Page elements {key} count: L={len(a_items)} M={len(b_items)}")
        
        if differences:
            return ComparisonResult(False, f"Page elements differ:\n" + "\n".join(differences))
        
        return ComparisonResult(True, "Page elements match")
    except Exception as e:
        logger.error(f"Error in page elements comparison: {e}")
        return ComparisonResult(False, f"Page elements comparison failed: {e}")


def compare_page_structure(self, a: Dict[str, Any], b: Dict[str, Any]) -> ComparisonResult:
    """Compare page structure."""
    try:
        differences = []
        for key in ['total_elements', 'divs', 'spans', 'paragraphs', 'sections', 'articles', 'asides', 'lists', 'list_items', 'forms', 'tables', 'images', 'links', 'buttons', 'inputs', 'selects', 'textareas', 'iframes', 'scripts', 'styles', 'meta_tags', 'title_tags', 'headings', 'landmarks']:
            a_val = a.get(key, 0)
            b_val = a.get(key, 0)
            if a_val != b_val:
                differences.append(f"Page {key}: L={a_val} M={b_val}")
        
        if differences:
            return ComparisonResult(False, f"Page structure differs:\n" + "\n".join(differences))
        
        return ComparisonResult(True, "Page structure matches")
    except Exception as e:
        logger.error(f"Error in page structure comparison: {e}")
        return ComparisonResult(False, f"Page structure comparison failed: {e}")


# Add the methods to the IntegratedComparator class
IntegratedComparator.compare_list_structure = compare_list_structure
IntegratedComparator.compare_navigation_structure = compare_navigation_structure
IntegratedComparator.compare_breadcrumb_structure = compare_breadcrumb_structure
IntegratedComparator.compare_feature_structure = compare_feature_structure
IntegratedComparator.compare_semantic_structure = compare_semantic_structure
IntegratedComparator.compare_semantic_elements = compare_semantic_elements
IntegratedComparator.compare_interactive_structure = compare_interactive_structure
IntegratedComparator.compare_form_structure_detailed = compare_form_structure_detailed
IntegratedComparator.compare_form_details = compare_form_details
IntegratedComparator.compare_progress_structure = compare_progress_structure
IntegratedComparator.compare_graphics_structure = compare_graphics_structure
IntegratedComparator.compare_carousel_structure = compare_carousel_structure
IntegratedComparator.compare_search_structure = compare_search_structure
IntegratedComparator.compare_notification_structure = compare_notification_structure
IntegratedComparator.compare_loading_structure = compare_loading_structure
IntegratedComparator.compare_social_structure = compare_social_structure
IntegratedComparator.compare_media_structure = compare_media_structure
IntegratedComparator.compare_data_attributes = compare_data_attributes
IntegratedComparator.compare_custom_elements = compare_custom_elements
IntegratedComparator.compare_analytics_structure = compare_analytics_structure
IntegratedComparator.compare_error_structure = compare_error_structure
IntegratedComparator.compare_theme_structure = compare_theme_structure
IntegratedComparator.compare_page_structure_ordered = compare_page_structure_ordered
IntegratedComparator.compare_page_elements_ordered = compare_page_elements_ordered
IntegratedComparator.compare_page_structure = compare_page_structure
