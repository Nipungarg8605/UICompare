from __future__ import annotations

from typing import List, Dict, Tuple, Any, Set
from urllib.parse import urlparse
import os
import logging
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, WebDriverException
from utils.highlight import highlight_element
import time

logger = logging.getLogger(__name__)

# Global tracking for highlighted elements to prevent duplicates
_highlighted_elements: Set[str] = set()
_current_page_url: str = ""
_element_collection_stats: Dict[str, int] = {}

def _reset_highlighting_tracker(url: str) -> None:
	"""Reset the highlighting tracker when navigating to a new page."""
	global _highlighted_elements, _current_page_url, _element_collection_stats
	if url != _current_page_url:
		_highlighted_elements.clear()
		_current_page_url = url
		_element_collection_stats.clear()
		logger.debug(f"Reset highlighting tracker for new page: {url}")

def _get_element_id(element: Any) -> str:
	"""Generate a unique ID for an element to track highlighting."""
	try:
		# Try multiple strategies for unique identification
		strategies = [
			# Strategy 1: Use ID if available
			lambda: element.get_attribute('id'),
			# Strategy 2: Use data-testid if available
			lambda: element.get_attribute('data-testid'),
			# Strategy 3: Use aria-label if available
			lambda: element.get_attribute('aria-label'),
			# Strategy 4: Use text content + tag name
			lambda: f"{element.tag_name}_{(element.text or '').strip()[:50]}",
			# Strategy 5: Use class + tag name
			lambda: f"{element.tag_name}_{(element.get_attribute('class') or '').split()[0]}",
			# Strategy 6: Use href for links
			lambda: f"{element.tag_name}_{(element.get_attribute('href') or '')[:50]}" if element.tag_name == 'a' else None,
			# Strategy 7: Use position as last resort
			lambda: f"{element.tag_name}_{element.rect['x']}_{element.rect['y']}_{element.rect['width']}_{element.rect['height']}"
		]
		
		for strategy in strategies:
			try:
				result = strategy()
				if result and result.strip():
					return f"{element.tag_name}_{result.strip()}"
			except Exception:
				continue
		
		# Ultimate fallback
		return f"{element.tag_name}_{id(element)}"
	except Exception:
		# If all else fails, use object ID
		return f"unknown_{id(element)}"

def _is_element_already_highlighted(element: Any) -> bool:
	"""Check if an element has already been highlighted."""
	try:
		element_id = _get_element_id(element)
		return element_id in _highlighted_elements
	except Exception as e:
		logger.debug(f"Error checking if element is highlighted: {e}")
		return False

def _mark_element_as_highlighted(element: Any) -> None:
	"""Mark an element as highlighted to prevent duplicates."""
	try:
		element_id = _get_element_id(element)
		_highlighted_elements.add(element_id)
		logger.debug(f"Marked element as highlighted: {element_id}")
	except Exception as e:
		logger.debug(f"Error marking element as highlighted: {e}")

def _get_elements_in_order(driver: WebDriver, selector: str) -> List[Any]:
	"""Get elements in top-to-bottom order based on their position on the page."""
	try:
		elements = driver.find_elements("css selector", selector)
		if not elements:
			return []
		
		# Get position information for each element
		element_positions = []
		for element in elements:
			try:
				rect = element.rect
				# Calculate a position score (top position is more important)
				position_score = rect['y'] * 1000 + rect['x']  # Prioritize vertical position
				element_positions.append((position_score, element))
			except Exception:
				# If we can't get position, put it at the end
				element_positions.append((999999, element))
		
		# Sort by position (top to bottom, left to right)
		element_positions.sort(key=lambda x: x[0])
		
		# Return only the elements, not the position scores
		return [element for _, element in element_positions]
	except Exception as e:
		logger.warning(f"Failed to get elements in order with selector '{selector}': {e}")
		return _safe_find_elements(driver, selector)

def _update_collection_stats(element_type: str, total_found: int, highlighted: int, skipped: int) -> None:
	"""Update collection statistics for monitoring."""
	global _element_collection_stats
	key = f"{element_type}_total"
	_element_collection_stats[key] = _element_collection_stats.get(key, 0) + total_found
	key = f"{element_type}_highlighted"
	_element_collection_stats[key] = _element_collection_stats.get(key, 0) + highlighted
	key = f"{element_type}_skipped"
	_element_collection_stats[key] = _element_collection_stats.get(key, 0) + skipped

def _get_collection_summary() -> Dict[str, Any]:
	"""Get a summary of element collection statistics."""
	global _element_collection_stats
	return _element_collection_stats.copy()

def _safe_execute_script(driver: WebDriver, script: str, *args) -> Any:
	"""Safely execute JavaScript with error handling and logging."""
	try:
		result = driver.execute_script(script, *args)
		return result
	except WebDriverException as e:
		logger.warning(f"JavaScript execution failed: {e}")
		return None
	except Exception as e:
		logger.error(f"Unexpected error in JavaScript execution: {e}")
		return None


def _safe_find_elements(driver: WebDriver, selector: str) -> List[Any]:
	"""Safely find elements with error handling."""
	try:
		elements = driver.find_elements("css selector", selector)
		return elements
	except Exception as e:
		logger.warning(f"Failed to find elements with selector '{selector}': {e}")
		return []


def _get_all_iframes(driver: WebDriver) -> List[Any]:
	"""Get all iframes in the current page, including nested iframes."""
	iframes = []
	try:
		# Get all iframe elements
		iframe_elements = driver.find_elements("css selector", "iframe")
		iframes.extend(iframe_elements)
		
		# Also get frame elements (older HTML)
		frame_elements = driver.find_elements("css selector", "frame")
		iframes.extend(frame_elements)
		
		logger.info(f"Found {len(iframes)} iframe/frame elements")
		return iframes
	except Exception as e:
		logger.warning(f"Failed to get iframes: {e}")
		return []


def _switch_to_iframe_safely(driver: WebDriver, iframe: Any) -> bool:
	"""Safely switch to an iframe with error handling."""
	try:
		# Check if iframe is still attached to DOM
		if not iframe.is_displayed():
			logger.debug("Iframe is not displayed, skipping")
			return False
		
		# Get iframe info for logging
		iframe_info = {
			'id': iframe.get_attribute('id'),
			'name': iframe.get_attribute('name'),
			'src': iframe.get_attribute('src'),
			'title': iframe.get_attribute('title')
		}
		iframe_desc = f"iframe(id={iframe_info['id']}, name={iframe_info['name']}, src={iframe_info['src']})"
		
		# Switch to iframe
		driver.switch_to.frame(iframe)
		logger.debug(f"Successfully switched to {iframe_desc}")
		return True
	except Exception as e:
		logger.warning(f"Failed to switch to iframe: {e}")
		return False


def _switch_to_default_content(driver: WebDriver) -> None:
	"""Safely switch back to default content."""
	try:
		driver.switch_to.default_content()
		logger.debug("Switched back to default content")
	except Exception as e:
		logger.warning(f"Failed to switch to default content: {e}")


def _collect_from_iframe(driver: WebDriver, iframe: Any, collector_func, **kwargs) -> List[Any]:
	"""Collect elements from a specific iframe using the provided collector function."""
	results = []
	
	try:
		# Get iframe info BEFORE switching (to avoid stale element reference)
		iframe_info = {
			'id': iframe.get_attribute('id'),
			'name': iframe.get_attribute('name'),
			'src': iframe.get_attribute('src'),
			'title': iframe.get_attribute('title')
		}
		iframe_desc = f"iframe(id={iframe_info['id']}, name={iframe_info['name']}, src={iframe_info['src']})"
		
		logger.info(f"Collecting from {iframe_desc}")
		
		# Switch to iframe
		if not _switch_to_iframe_safely(driver, iframe):
			return results
		
		# Collect elements from this iframe
		iframe_results = collector_func(driver, **kwargs)
		
		# Add iframe context to results
		if isinstance(iframe_results, (list, tuple)):
			# Handle list/tuple results
			for result in iframe_results:
				if isinstance(result, dict):
					result['_iframe_context'] = iframe_info
				elif isinstance(result, str):
					# Convert string to dict with iframe context
					results.append({
						'content': result,
						'_iframe_context': iframe_info
					})
				else:
					results.append({
						'element': result,
						'_iframe_context': iframe_info
					})
		else:
			# Handle single value results (like strings)
			if isinstance(iframe_results, dict):
				iframe_results['_iframe_context'] = iframe_info
				results.append(iframe_results)
			elif isinstance(iframe_results, str):
				results.append({
					'content': iframe_results,
					'_iframe_context': iframe_info
				})
			else:
				results.append({
					'element': iframe_results,
					'_iframe_context': iframe_info
				})
		
		logger.info(f"Collected {len(iframe_results)} elements from {iframe_desc}")
		
	except Exception as e:
		logger.warning(f"Error collecting from iframe: {e}")
	finally:
		# Always switch back to default content
		_switch_to_default_content(driver)
	
	return results


def _collect_from_all_contexts(driver: WebDriver, collector_func, include_iframes: bool = True, **kwargs) -> List[Any]:
	"""Collect elements from main document and all iframes."""
	all_results = []
	
	# Collect from main document
	logger.info("Collecting from main document")
	main_results = collector_func(driver, **kwargs)
	
	# Handle both single values and lists properly
	if isinstance(main_results, (list, tuple)):
		all_results.extend(main_results)
	else:
		all_results.append(main_results)
	
	if not include_iframes:
		return all_results
	
	# Collect from all iframes
	iframes = _get_all_iframes(driver)
	if not iframes:
		logger.info("No iframes found")
		return all_results
	
	logger.info(f"Found {len(iframes)} iframes, collecting from each")
	
	for i, iframe in enumerate(iframes):
		try:
			iframe_results = _collect_from_iframe(driver, iframe, collector_func, **kwargs)
			all_results.extend(iframe_results)
			logger.info(f"Completed iframe {i+1}/{len(iframes)}")
		except Exception as e:
			logger.warning(f"Failed to collect from iframe {i+1}: {e}")
			continue
	
	logger.info(f"Total elements collected: {len(all_results)} (main: {len(main_results) if isinstance(main_results, (list, tuple)) else 1}, iframes: {len(all_results) - (len(main_results) if isinstance(main_results, (list, tuple)) else 1)})")
	return all_results


def _highlight_enabled() -> bool:
	"""Check if highlighting is enabled from environment variable or settings file."""
	# First check environment variable
	env_enabled = os.environ.get("UI_COMPARE_HIGHLIGHT", "").lower() in ("1", "true", "yes")
	if env_enabled:
		return True
	
	# If not set in environment, try to load from settings file
	try:
		import yaml
		with open('config/settings.yaml', 'r') as f:
			settings = yaml.safe_load(f)
		highlight_config = settings.get('highlight', {})
		return highlight_config.get('enabled', False)
	except Exception:
		return False


def _highlight_duration() -> int:
	"""Get highlight duration from environment variable or settings file."""
	# First check environment variable
	env_duration = os.environ.get("UI_COMPARE_HIGHLIGHT_DURATION_MS")
	if env_duration:
		try:
			return int(env_duration)
		except Exception:
			pass
	
	# If not set in environment, try to load from settings file
	try:
		import yaml
		with open('config/settings.yaml', 'r') as f:
			settings = yaml.safe_load(f)
		highlight_config = settings.get('highlight', {})
		return int(highlight_config.get('duration_ms', 600))
	except Exception:
		return 600


def _highlight_color() -> str:
	"""Get highlight color from environment variable or settings file."""
	# First check environment variable
	env_color = os.environ.get("UI_COMPARE_HIGHLIGHT_COLOR")
	if env_color:
		return env_color
	
	# If not set in environment, try to load from settings file
	try:
		import yaml
		with open('config/settings.yaml', 'r') as f:
			settings = yaml.safe_load(f)
		highlight_config = settings.get('highlight', {})
		return highlight_config.get('color', "#00ffcc")
	except Exception:
		return "#00ffcc"


def _highlight_elements(driver: WebDriver, elements: List[Any], element_type: str = "unknown") -> None:
	"""Highlight a list of elements if highlighting is enabled - highlights every time for comparison."""
	if not _highlight_enabled() or not elements:
		return
	
	# Reset tracker if we're on a new page
	current_url = driver.current_url
	_reset_highlighting_tracker(current_url)
	
	logger.debug(f"Highlighting {len(elements)} {element_type} elements for comparison")
	
	# Highlight all elements every time for comparison
	successful_highlights = 0
	for element in elements:
		try:
			highlight_element(driver, element, _highlight_duration(), _highlight_color())
			successful_highlights += 1
		except Exception as e:
			logger.debug(f"Failed to highlight element: {e}")
	
	# Update collection statistics
	_update_collection_stats(element_type, len(elements), successful_highlights, 0)
	
	logger.debug(f"Successfully highlighted {successful_highlights}/{len(elements)} {element_type} elements for comparison")


def wait_for_document_ready(driver: WebDriver, timeout_seconds: int = 20) -> None:
	"""Wait for document to be ready with enhanced error handling."""
	try:
		WebDriverWait(driver, timeout_seconds).until(
			lambda d: d.execute_script("return document.readyState") == "complete"
		)
		logger.debug("Document ready state achieved")
	except TimeoutException:
		logger.warning(f"Document ready timeout after {timeout_seconds} seconds")
	except Exception as e:
		logger.error(f"Error waiting for document ready: {e}")


def wait_for_element_present(driver: WebDriver, selector: str, timeout_seconds: int = 10) -> bool:
	"""Wait for an element to be present on the page."""
	try:
		WebDriverWait(driver, timeout_seconds).until(
			lambda d: len(d.find_elements("css selector", selector)) > 0
		)
		return True
	except TimeoutException:
		logger.warning(f"Element '{selector}' not found within {timeout_seconds} seconds")
		return False
	except Exception as e:
		logger.error(f"Error waiting for element '{selector}': {e}")
		return False


def get_page_load_time(driver: WebDriver) -> float:
	"""Get the page load time in milliseconds."""
	try:
		load_time = driver.execute_script(
			"return performance.timing.loadEventEnd - performance.timing.navigationStart;"
		)
		return float(load_time) if load_time else 0.0
	except Exception as e:
		logger.warning(f"Could not get page load time: {e}")
		return 0.0


def page_title(driver: WebDriver) -> str:
	title = (driver.title or "").strip()
	logger.debug(f"Page title: '{title}'")
	return title


def page_title_with_iframes(driver: WebDriver) -> List[Dict[str, Any]]:
	"""Get page titles from main document and all iframes."""
	def _collect_title(driver: WebDriver) -> str:
		try:
			return (driver.title or "").strip()
		except Exception:
			return ""
	
	results = _collect_from_all_contexts(driver, _collect_title, include_iframes=True)
	
	# Convert results to proper format
	formatted_results = []
	for result in results:
		if isinstance(result, dict) and '_iframe_context' in result:
			formatted_results.append({
				'title': result.get('content', ''),
				'iframe_context': result['_iframe_context']
			})
		else:
			formatted_results.append({
				'title': result,
				'iframe_context': {'type': 'main_document'}
			})
	
	logger.info(f"Collected {len(formatted_results)} page titles (including iframes)")
	return formatted_results


def heading_texts(driver: WebDriver) -> List[str]:
	"""Collect heading texts in top-to-bottom order."""
	# Get elements in order first
	elements = _get_elements_in_order(driver, "h1,h2,h3,h4,h5,h6")
	
	# Extract text from elements in order
	texts = []
	for element in elements:
		try:
			text = (element.text or "").strip()
			if text:
				texts.append(text)
		except Exception as e:
			logger.debug(f"Failed to get text from heading element: {e}")
	
	# Highlight the heading elements (in order)
	if _highlight_enabled():
		_highlight_elements(driver, elements, "headings")
	
	logger.debug(f"Found {len(texts)} headings in order: {texts[:3]}...")  # Log first 3 headings
	return texts


def heading_texts_with_iframes(driver: WebDriver) -> List[Dict[str, Any]]:
	"""Collect heading texts from main document and all iframes."""
	def _collect_headings(driver: WebDriver) -> List[str]:
		elements = _get_elements_in_order(driver, "h1,h2,h3,h4,h5,h6")
		texts = []
		for element in elements:
			try:
				text = (element.text or "").strip()
				if text:
					texts.append(text)
			except Exception:
				pass
		return texts
	
	results = _collect_from_all_contexts(driver, _collect_headings, include_iframes=True)
	
	# Convert results to proper format
	formatted_results = []
	for result in results:
		if isinstance(result, dict) and '_iframe_context' in result:
			formatted_results.append({
				'headings': result.get('content', []),
				'iframe_context': result['_iframe_context']
			})
		else:
			formatted_results.append({
				'headings': result,
				'iframe_context': {'type': 'main_document'}
			})
	
	logger.info(f"Collected headings from {len(formatted_results)} contexts (including iframes)")
	return formatted_results


def primary_h1(driver: WebDriver) -> str:
	js = (
		"var el = document.querySelector('h1');"
		"return el ? (el.innerText||'').trim() : '';"
	)
	text = _safe_execute_script(driver, js) or ""
	
	# Highlight the H1 element
	if _highlight_enabled() and text:
		try:
			element = driver.find_element("css selector", "h1")
			highlight_element(driver, element, _highlight_duration(), _highlight_color())
		except Exception:
			pass
	
	logger.debug(f"Primary H1: '{text}'")
	return text


def button_texts(driver: WebDriver) -> List[str]:
	"""Collect button texts in top-to-bottom order."""
	# Get elements in order first
	elements = _get_elements_in_order(driver, "button, a[role='button'], input[type='button'], input[type='submit'], [role='button']")
	
	# Filter visible and enabled elements, then extract text
	texts = []
	for element in elements:
		try:
			# Check if element is visible and not disabled
			if element.is_displayed() and not element.get_attribute('disabled'):
				# Get text from various sources
				text = (element.text or element.get_attribute('value') or 
						element.get_attribute('aria-label') or "").strip()
				if text:
					texts.append(text)
		except Exception as e:
			logger.debug(f"Failed to get text from button element: {e}")
	
	# Highlight the button elements (in order)
	if _highlight_enabled():
		_highlight_elements(driver, elements, "buttons")
	
	logger.debug(f"Found {len(texts)} buttons in order: {texts[:3]}...")  # Log first 3 buttons
	return texts


def button_texts_with_iframes(driver: WebDriver) -> List[Dict[str, Any]]:
	"""Collect button texts from main document and all iframes."""
	def _collect_buttons(driver: WebDriver) -> List[str]:
		elements = _get_elements_in_order(driver, "button, a[role='button'], input[type='button'], input[type='submit'], [role='button']")
		texts = []
		for element in elements:
			try:
				if element.is_displayed() and not element.get_attribute('disabled'):
					text = (element.text or element.get_attribute('value') or 
							element.get_attribute('aria-label') or "").strip()
					if text:
						texts.append(text)
			except Exception:
				pass
		return texts
	
	results = _collect_from_all_contexts(driver, _collect_buttons, include_iframes=True)
	
	# Convert results to proper format
	formatted_results = []
	for result in results:
		if isinstance(result, dict) and '_iframe_context' in result:
			formatted_results.append({
				'buttons': result.get('content', []),
				'iframe_context': result['_iframe_context']
			})
		else:
			formatted_results.append({
				'buttons': result,
				'iframe_context': {'type': 'main_document'}
			})
	
	logger.info(f"Collected buttons from {len(formatted_results)} contexts (including iframes)")
	return formatted_results


def nav_link_texts(driver: WebDriver) -> List[str]:
	"""Collect navigation link texts in top-to-bottom order."""
	# Get elements in order first
	elements = _get_elements_in_order(driver, "nav a, [role='navigation'] a")
	
	# Extract text from elements in order
	texts = []
	for element in elements:
		try:
			text = (element.text or "").strip()
			if text:
				texts.append(text)
		except Exception as e:
			logger.debug(f"Failed to get text from nav link element: {e}")
	
	# Highlight the nav link elements (in order)
	if _highlight_enabled():
		_highlight_elements(driver, elements, "navigation links")
	
	logger.debug(f"Found {len(texts)} navigation links in order: {texts[:3]}...")
	return texts


def body_text_snapshot(driver: WebDriver, max_len: int = 2000) -> str:
	js = "return (document.body && document.body.innerText) ? document.body.innerText : '';"
	text = _safe_execute_script(driver, js) or ""
	text = " ".join(text.split())
	
	# Highlight the body element
	if _highlight_enabled():
		try:
			element = driver.find_element("css selector", "body")
			highlight_element(driver, element, _highlight_duration(), _highlight_color())
		except Exception:
			pass
	
	result = text[:max_len]
	logger.debug(f"Body text snapshot length: {len(result)} characters")
	return result


def remove_ignored_selectors(driver: WebDriver, selectors: List[str]) -> None:
	if not selectors:
		return
	joined = ",".join(selectors)
	js = (
		"var sels = arguments[0].split(',');"
		"sels.forEach(s=>{document.querySelectorAll(s).forEach(el=>el.remove());});"
	)
	_safe_execute_script(driver, js, joined)
	logger.debug(f"Removed {len(selectors)} ignored selectors")


def normalize_url_path(url: str) -> str:
	parsed = urlparse(url or "")
	path = parsed.path or "/"
	query = ("?" + parsed.query) if parsed.query else ""
	return path + query


def links_map(driver: WebDriver) -> List[Tuple[str, str]]:
	"""Collect links in top-to-bottom order."""
	# Get elements in order first
	elements = _get_elements_in_order(driver, "a[href]")
	
	# Filter visible elements and extract text/href
	result: List[Tuple[str, str]] = []
	for element in elements:
		try:
			# Check if element is visible
			if element.is_displayed():
				text = (element.text or element.get_attribute('aria-label') or "").strip()
				href = element.get_attribute('href') or ""
				if text:
					result.append((text, normalize_url_path(href)))
		except Exception as e:
			logger.debug(f"Failed to get link data from element: {e}")
	
	# Highlight the link elements (in order)
	if _highlight_enabled():
		_highlight_elements(driver, elements, "links")
	
	logger.debug(f"Found {len(result)} links in order")
	return result


def links_map_with_iframes(driver: WebDriver) -> List[Dict[str, Any]]:
	"""Collect links from main document and all iframes."""
	def _collect_links(driver: WebDriver) -> List[Tuple[str, str]]:
		elements = _get_elements_in_order(driver, "a[href]")
		result = []
		for element in elements:
			try:
				if element.is_displayed():
					text = (element.text or element.get_attribute('aria-label') or "").strip()
					href = element.get_attribute('href') or ""
					if text:
						result.append((text, normalize_url_path(href)))
			except Exception:
				pass
		return result
	
	results = _collect_from_all_contexts(driver, _collect_links, include_iframes=True)
	
	# Convert results to proper format
	formatted_results = []
	for result in results:
		if isinstance(result, dict) and '_iframe_context' in result:
			formatted_results.append({
				'links': result.get('content', []),
				'iframe_context': result['_iframe_context']
			})
		else:
			formatted_results.append({
				'links': result,
				'iframe_context': {'type': 'main_document'}
			})
	
	logger.info(f"Collected links from {len(formatted_results)} contexts (including iframes)")
	return formatted_results


def collect_form_summary(driver: WebDriver) -> Dict[str, List[str]]:
	js_required = (
		"""
		return Array.from(document.querySelectorAll('input,select,textarea'))
			.filter(e => e.required)
			.map(e => {
				var label = e.labels && e.labels[0] ? e.labels[0].textContent : '';
				return label.trim() || e.name || e.id || e.placeholder || 'Unknown';
			});
		"""
	)
	required_fields = _safe_execute_script(driver, js_required) or []
	
	# Highlight the form elements
	if _highlight_enabled():
		elements = _safe_find_elements(driver, "input,select,textarea")
		_highlight_elements(driver, elements, "form elements")
	
	return {"required_fields": required_fields}


def collect_table_preview(driver: WebDriver, max_rows: int = 5) -> Dict[str, List]:
	js = (
		"""
		var tbl = document.querySelector('table'); if(!tbl){return {headers: [], rows: [], footer: [], row_actions: []}}
		var headers = Array.from(tbl.querySelectorAll('thead th')).map(th => (th.innerText||'').trim());
		if(headers.length===0){ headers = Array.from(tbl.querySelectorAll('tr th')).map(th => (th.innerText||'').trim()); }
		var rows = Array.from(tbl.querySelectorAll('tbody tr'))
		  .slice(0, arguments[0])
		  .map(tr => Array.from(tr.querySelectorAll('td')).map(td => (td.innerText||'').trim()));
		var footer = Array.from(tbl.querySelectorAll('tfoot td')).map(td => (td.innerText||'').trim());
		var rowActions = Array.from(tbl.querySelectorAll('tbody tr'))
		  .slice(0, arguments[0])
		  .map(tr => Array.from(tr.querySelectorAll('button, a[role="button"]')).map(b => (b.innerText||'').trim()).filter(t=>t.length>0));
		return {headers: headers, rows: rows, footer: footer, row_actions: rowActions};
		"""
	)
	result = _safe_execute_script(driver, js, max_rows)
	
	# Highlight the table elements
	if _highlight_enabled():
		elements = _safe_find_elements(driver, "table")
		_highlight_elements(driver, elements, "table")
	
	return result


def collect_meta(driver: WebDriver) -> Dict[str, str]:
	js = (
		"""
		var getAttr = function(sel, attr) {
			var el = document.querySelector(sel);
			if (!el) { return ''; }
			return attr ? (el.getAttribute(attr) || '') : ((el.innerText || '').trim());
		};
		return {
			title: document.title || '',
			description: getAttr('meta[name="description"]', 'content'),
			robots: getAttr('meta[name="robots"]', 'content'),
			canonical: getAttr('link[rel="canonical"]', 'href'),
			og_title: getAttr('meta[property="og:title"]', 'content'),
			og_description: getAttr('meta[property="og:description"]', 'content')
		};
		"""
	)
	result = _safe_execute_script(driver, js)
	
	# Highlight the meta elements
	if _highlight_enabled():
		elements = _safe_find_elements(driver, "meta, link[rel='canonical']")
		_highlight_elements(driver, elements, "meta")
	
	return result


def collect_accessibility(driver: WebDriver) -> Dict[str, int]:
	js = (
		"""
		var imgsNoAlt = Array.from(document.querySelectorAll('img')).filter(function(i){
			return !i.hasAttribute('alt') || i.getAttribute('alt').trim().length===0;
		}).length;
		var btnsNoName = Array.from(document.querySelectorAll('button,[role="button"],a[role="button"]')).filter(function(b){
			var name = (b.innerText || b.getAttribute('aria-label') || '').trim();
			return name.length===0;
		}).length;
		return { images_missing_alt: imgsNoAlt, buttons_without_name: btnsNoName };
		"""
	)
	result = _safe_execute_script(driver, js)
	
	# Highlight the accessibility elements
	if _highlight_enabled():
		elements = _safe_find_elements(driver, "img, button, [role='button'], a[role='button']")
		_highlight_elements(driver, elements, "accessibility")
	
	return result

# Extended collectors

def collect_head_meta_extended(driver: WebDriver) -> Dict[str, Any]:
	js = (
		"""
		var qAll = (sel) => Array.from(document.querySelectorAll(sel));
		var meta = {};
		meta.keywords = (document.querySelector('meta[name="keywords"]')||{}).content || '';
		meta.og_image = (document.querySelector('meta[property="og:image"]')||{}).content || '';
		meta.twitter_card = (document.querySelector('meta[name="twitter:card"]')||{}).content || '';
		meta.twitter_title = (document.querySelector('meta[name="twitter:title"]')||{}).content || '';
		meta.twitter_desc = (document.querySelector('meta[name="twitter:description"]')||{}).content || '';
		meta.hreflangs = qAll('link[rel="alternate"][hreflang]').map(l => [l.getAttribute('hreflang')||'', l.getAttribute('href')||'']);
		meta.icons = qAll('link[rel~="icon"]').map(l => l.getAttribute('href')||'');
		return meta;
		"""
	)
	result = _safe_execute_script(driver, js)
	
	# Highlight the extended meta elements
	if _highlight_enabled():
		elements = _safe_find_elements(driver, "meta, link[rel='alternate'][hreflang], link[rel~='icon']")
		_highlight_elements(driver, elements, "extended meta")
	
	return result


def collect_breadcrumbs(driver: WebDriver) -> List[Tuple[str, str]]:
	js = (
		"""
		var areas = [];
		var nav = document.querySelector('nav[aria-label="breadcrumb"]');
		if (nav){ areas.push(nav); }
		areas = areas.concat(Array.from(document.querySelectorAll('.breadcrumb')));
		var items = [];
		areas.forEach(function(area){
			var links = Array.from(area.querySelectorAll('a'));
			if (links.length){
				links.forEach(a => items.push([ (a.innerText||'').trim(), a.getAttribute('href')||'' ]));
			} else {
				items = items.concat(Array.from(area.querySelectorAll('li,span')).map(e => [ (e.innerText||'').trim(), '' ]));
			}
		});
		return items;
		"""
	)
	pairs = _safe_execute_script(driver, js) or []
	result = [(t, normalize_url_path(h)) for t, h in pairs if t]
	
	# Highlight the breadcrumb elements
	if _highlight_enabled():
		elements = _safe_find_elements(driver, "nav[aria-label='breadcrumb'], .breadcrumb")
		_highlight_elements(driver, elements, "breadcrumbs")
	
	return result


def collect_tabs(driver: WebDriver) -> List[Dict[str, Any]]:
	js = (
		"""
		var tabs = Array.from(document.querySelectorAll('[role="tab"], .mat-tab-label'))
			.map(el => ({ label: (el.innerText||'').trim(), selected: (el.getAttribute('aria-selected')==='true') || el.classList.contains('mat-tab-label-active') }));
		return tabs;
		"""
	)
	result = _safe_execute_script(driver, js) or []
	
	# Highlight the tab elements
	if _highlight_enabled():
		elements = _safe_find_elements(driver, "[role='tab'], .mat-tab-label")
		_highlight_elements(driver, elements, "tabs")
	
	return result


def collect_accordions(driver: WebDriver) -> List[Dict[str, Any]]:
	js = (
		"""
		var acc = Array.from(document.querySelectorAll('[aria-expanded]'))
			.map(el => ({ text: (el.innerText||'').trim(), expanded: el.getAttribute('aria-expanded')==='true' }));
		return acc;
		"""
	)
	result = _safe_execute_script(driver, js) or []
	
	# Highlight the accordion elements
	if _highlight_enabled():
		elements = _safe_find_elements(driver, "[aria-expanded]")
		_highlight_elements(driver, elements, "accordions")
	
	return result


def collect_pagination(driver: WebDriver) -> Dict[str, Any]:
	js = (
		"""
		var nav = document.querySelector('nav[aria-label="pagination"], .pagination, .mat-paginator');
		if (!nav) return {current: '', total: '', has_next: false, has_prev: false};
		var current = (nav.querySelector('.active, [aria-current="page"]')||{}).innerText || '';
		var nums = Array.from(nav.querySelectorAll('a,button')).map(e => (e.innerText||'').trim()).filter(t => /^\d+$/.test(t));
		var total = nums.length > 0 ? nums[nums.length-1] : '';
		var hasNext = !!nav.querySelector('.next:not(.disabled), [aria-label="Next"]:not([disabled])');
		var hasPrev = !!nav.querySelector('.prev:not(.disabled), [aria-label="Previous"]:not([disabled])');
		return { current: current, total: total, has_next: hasNext, has_prev: hasPrev };
		"""
	)
	result = _safe_execute_script(driver, js) or {"current": "", "total": "", "has_next": False, "has_prev": False}
	
	# Highlight the pagination elements
	if _highlight_enabled():
		elements = _safe_find_elements(driver, "nav[aria-label='pagination'], .pagination, .mat-paginator")
		_highlight_elements(driver, elements, "pagination")
	
	return result


def collect_form_details(driver: WebDriver, max_options: int = 10) -> Dict[str, Any]:
	js = (
		"""
		function labelFor(el){
			var id = el.id; var label = '';
			if (id){ var l = document.querySelector('label[for="'+id+'"]'); if (l) label = (l.innerText||'').trim(); }
			if (!label && el.closest('label')){ label = (el.closest('label').innerText||'').trim(); }
			return label;
		}
		var inputs = Array.from(document.querySelectorAll('input,select,textarea')).map(el => {
			var info = {
				name: el.name||'', type: (el.type||el.tagName||'').toLowerCase(), label: labelFor(el), required: !!el.required,
				min: el.min||'', max: el.max||'', pattern: el.pattern||'', placeholder: el.placeholder||''
			};
			if (el.tagName.toLowerCase()==='select'){
				info.options = Array.from(el.options).slice(0, arguments[0]).map(o => (o.text||'').trim());
				info.selected = Array.from(el.selectedOptions||[]).map(o => (o.text||'').trim());
			}
			if (info.type==='radio' || info.type==='checkbox'){
				info.checked = !!el.checked;
			}
			return info;
		});
		var validations = Array.from(document.querySelectorAll('[role="alert"], .error, .mat-error'))
			.map(e => (e.innerText||'').trim()).filter(t => t.length>0);
		return { inputs: inputs, validations: validations };
		"""
	)
	result = _safe_execute_script(driver, js, max_options) or {"inputs": [], "validations": []}
	
	# Highlight the form detail elements
	if _highlight_enabled():
		elements = _safe_find_elements(driver, "input,select,textarea, [role='alert'], .error, .mat-error")
		_highlight_elements(driver, elements, "form details")
	
	return result


def collect_widgets(driver: WebDriver) -> Dict[str, List[str]]:
	js = (
		"""
		var data = {};
		data.toasts = Array.from(document.querySelectorAll('.toast, .snackbar, .mat-snack-bar-container'))
			.map(e => (e.innerText||'').trim()).filter(t=>t.length>0);
		data.dialogs = Array.from(document.querySelectorAll('[role="dialog"], .modal, mat-dialog-container'))
			.map(e => (e.innerText||'').trim()).filter(t=>t.length>0);
		data.tooltips = Array.from(document.querySelectorAll('[role="tooltip"], .tooltip'))
			.map(e => (e.innerText||'').trim()).filter(t=>t.length>0);
		return data;
		"""
	)
	result = _safe_execute_script(driver, js) or {"toasts": [], "dialogs": [], "tooltips": []}
	
	# Highlight the widget elements
	if _highlight_enabled():
		elements = _safe_find_elements(driver, ".toast, .snackbar, .mat-snack-bar-container, [role='dialog'], .modal, mat-dialog-container, [role='tooltip'], .tooltip")
		_highlight_elements(driver, elements, "widgets")
	
	return result


def collect_images_preview(driver: WebDriver, max_images: int = 10) -> List[Dict[str, Any]]:
	js = (
		"""
		return Array.from(document.querySelectorAll('img')).slice(0, arguments[0]).map(img => ({
			src: img.getAttribute('src')||'',
			srcset: !!img.getAttribute('srcset'),
			alt: (img.getAttribute('alt')||'').trim(),
			loading: (img.getAttribute('loading')||'')
		}));
		"""
	)
	result = _safe_execute_script(driver, js, max_images) or []
	
	# Highlight the image elements
	if _highlight_enabled():
		elements = _safe_find_elements(driver, "img")
		_highlight_elements(driver, elements, "images")
	
	return result


def collect_landmarks(driver: WebDriver) -> Dict[str, bool]:
	js = (
		"""
		return {
			header: !!document.querySelector('header, [role="banner"]'),
			main: !!document.querySelector('main, [role="main"]'),
			nav: !!document.querySelector('nav, [role="navigation"]'),
			footer: !!document.querySelector('footer, [role="contentinfo"]')
		};
		"""
	)
	result = _safe_execute_script(driver, js) or {"header": False, "main": False, "nav": False, "footer": False}
	
	# Highlight the landmark elements
	if _highlight_enabled():
		elements = _safe_find_elements(driver, "header, [role='banner'], main, [role='main'], nav, [role='navigation'], footer, [role='contentinfo']")
		_highlight_elements(driver, elements, "landmarks")
	
	return result


def collect_interactive_roles(driver: WebDriver, max_items: int = 50) -> List[Tuple[str, str]]:
	js = (
		"""
		function nameOf(el){
			var aria = (el.getAttribute('aria-label')||'').trim();
			if (aria) return aria;
			return (el.innerText||'').trim();
		}
		var sels = 'a,button,[role="button"],input,select,textarea';
		return Array.from(document.querySelectorAll(sels)).slice(0, arguments[0]).map(el => [ (el.getAttribute('role')||el.tagName||'').toLowerCase(), nameOf(el) ]);
		"""
	)
	pairs = _safe_execute_script(driver, js, max_items) or []
	result = [(r, n) for r, n in pairs if n]
	
	# Highlight the interactive role elements
	if _highlight_enabled():
		elements = _safe_find_elements(driver, "a,button,[role='button'],input,select,textarea")
		_highlight_elements(driver, elements, "interactive roles")
	
	return result


def collect_i18n(driver: WebDriver) -> Dict[str, str]:
	js = (
		"""
		return {
			lang: (document.documentElement.getAttribute('lang')||'').toLowerCase()
		};
		"""
	)
	result = _safe_execute_script(driver, js) or {"lang": ""}
	
	# Highlight the html element for i18n
	if _highlight_enabled():
		try:
			element = driver.find_element("css selector", "html")
			highlight_element(driver, element, _highlight_duration(), _highlight_color())
		except Exception:
			pass
	
	return result


def collect_performance(driver: WebDriver) -> Dict[str, Any]:
	js = (
		"""
		var nav = (performance.getEntriesByType && performance.getEntriesByType('navigation')[0]) || null;
		if (!nav) { return {}; }
		return {
			startTime: nav.startTime,
			responseEnd: nav.responseEnd,
			domContentLoaded: nav.domContentLoadedEventEnd,
			loadEventEnd: nav.loadEventEnd
		};
		"""
	)
	result = _safe_execute_script(driver, js) or {}
	
	# Highlight the body element for performance (since it represents the page load)
	if _highlight_enabled():
		try:
			element = driver.find_element("css selector", "body")
			highlight_element(driver, element, _highlight_duration(), _highlight_color())
		except Exception:
			pass
	
	return result


# New collector functions for enhanced comparison capabilities

def collect_carousel_slides(driver: WebDriver) -> List[Dict[str, Any]]:
	"""Collect carousel/slider information."""
	js = (
		"""
		var carousels = Array.from(document.querySelectorAll('.carousel, .slider, [role="region"][aria-label*="carousel"], [role="region"][aria-label*="slider"]'));
		return carousels.map(carousel => {
			var slides = Array.from(carousel.querySelectorAll('.slide, .carousel-item, [role="tabpanel"]'));
			var indicators = Array.from(carousel.querySelectorAll('.indicator, .dot, [role="tab"]'));
			return {
				total_slides: slides.length,
				total_indicators: indicators.length,
				active_slide: slides.findIndex(slide => slide.classList.contains('active') || slide.getAttribute('aria-hidden') === 'false'),
				has_controls: !!carousel.querySelector('.prev, .next, [aria-label*="previous"], [aria-label*="next"]')
			};
		});
		"""
	)
	result = _safe_execute_script(driver, js) or []
	
	# Highlight the carousel elements
	if _highlight_enabled():
		elements = _safe_find_elements(driver, ".carousel, .slider, [role='region'][aria-label*='carousel'], [role='region'][aria-label*='slider']")
		_highlight_elements(driver, elements, "carousels")
	
	logger.debug(f"Found {len(result)} carousels/sliders")
	return result


def collect_search_functionality(driver: WebDriver) -> Dict[str, Any]:
	"""Collect search-related elements and functionality."""
	js = (
		"""
		var searchInputs = Array.from(document.querySelectorAll('input[type="search"], input[name*="search"], input[placeholder*="search"], .search-input'));
		var searchButtons = Array.from(document.querySelectorAll('button[type="submit"], input[type="submit"], .search-button, [aria-label*="search"]'));
		var searchForms = Array.from(document.querySelectorAll('form[action*="search"], form[class*="search"]'));
		
		return {
			search_inputs: searchInputs.map(input => ({
				placeholder: input.placeholder || '',
				name: input.name || '',
				type: input.type || '',
				required: !!input.required,
				autocomplete: input.getAttribute('autocomplete') || ''
			})),
			search_buttons: searchButtons.map(btn => ({
				text: (btn.innerText || btn.value || '').trim(),
				type: btn.type || 'button',
				aria_label: btn.getAttribute('aria-label') || ''
			})),
			search_forms: searchForms.length,
			has_autocomplete: !!document.querySelector('[role="listbox"], .autocomplete, .search-suggestions')
		};
		"""
	)
	result = _safe_execute_script(driver, js) or {"search_inputs": [], "search_buttons": [], "search_forms": 0, "has_autocomplete": False}
	
	# Highlight the search elements
	if _highlight_enabled():
		elements = _safe_find_elements(driver, "input[type='search'], input[name*='search'], input[placeholder*='search'], .search-input, button[type='submit'], input[type='submit'], .search-button")
		_highlight_elements(driver, elements, "search functionality")
	
	logger.debug(f"Found {len(result.get('search_inputs', []))} search inputs")
	return result


def collect_notifications_alerts(driver: WebDriver) -> List[Dict[str, Any]]:
	"""Collect notification and alert elements."""
	js = (
		"""
		var notifications = Array.from(document.querySelectorAll('.notification, .alert, .message, [role="alert"], [role="status"], .toast, .snackbar'));
		return notifications.map(notification => ({
			text: (notification.innerText || '').trim(),
			type: notification.getAttribute('role') || notification.className.split(' ')[0] || 'unknown',
			aria_live: notification.getAttribute('aria-live') || '',
			aria_label: notification.getAttribute('aria-label') || '',
			visible: notification.offsetParent !== null
		}));
		"""
	)
	result = _safe_execute_script(driver, js) or []
	
	# Highlight the notification elements
	if _highlight_enabled():
		elements = _safe_find_elements(driver, ".notification, .alert, .message, [role='alert'], [role='status'], .toast, .snackbar")
		_highlight_elements(driver, elements, "notifications")
	
	logger.debug(f"Found {len(result)} notifications/alerts")
	return result


def collect_loading_states(driver: WebDriver) -> Dict[str, Any]:
	"""Collect loading states and spinners."""
	js = (
		"""
		var spinners = Array.from(document.querySelectorAll('.spinner, .loading, .loader, [role="progressbar"], .progress'));
		var skeletons = Array.from(document.querySelectorAll('.skeleton, .shimmer, [class*="skeleton"], [class*="shimmer"]'));
		var overlays = Array.from(document.querySelectorAll('.loading-overlay, .spinner-overlay, [class*="loading"]'));
		
		return {
			spinners: spinners.length,
			skeletons: skeletons.length,
			overlays: overlays.length,
			total_loading_elements: spinners.length + skeletons.length + overlays.length,
			has_aria_busy: !!document.querySelector('[aria-busy="true"]'),
			has_loading_text: !!document.querySelector('*:contains("Loading"), *:contains("loading")')
		};
		"""
	)
	result = _safe_execute_script(driver, js) or {"spinners": 0, "skeletons": 0, "overlays": 0, "total_loading_elements": 0, "has_aria_busy": False, "has_loading_text": False}
	
	# Highlight the loading elements
	if _highlight_enabled():
		elements = _safe_find_elements(driver, ".spinner, .loading, .loader, [role='progressbar'], .progress, .skeleton, .shimmer, .loading-overlay, .spinner-overlay")
		_highlight_elements(driver, elements, "loading states")
	
	logger.debug(f"Found {result.get('total_loading_elements', 0)} loading elements")
	return result


def collect_social_media_links(driver: WebDriver) -> List[Dict[str, str]]:
	"""Collect social media links and sharing buttons."""
	js = (
		"""
		var socialLinks = Array.from(document.querySelectorAll('a[href*="facebook"], a[href*="twitter"], a[href*="linkedin"], a[href*="instagram"], a[href*="youtube"], a[href*="github"]'));
		var shareButtons = Array.from(document.querySelectorAll('.share, .social-share, [aria-label*="share"], [title*="share"]'));
		
		var social = socialLinks.map(link => ({
			platform: link.href.includes('facebook') ? 'facebook' : 
					  link.href.includes('twitter') ? 'twitter' : 
					  link.href.includes('linkedin') ? 'linkedin' : 
					  link.href.includes('instagram') ? 'instagram' : 
					  link.href.includes('youtube') ? 'youtube' : 
					  link.href.includes('github') ? 'github' : 'other',
			text: (link.innerText || link.getAttribute('aria-label') || '').trim(),
			href: link.href
		}));
		
		var shares = shareButtons.map(btn => ({
			platform: 'share',
			text: (btn.innerText || btn.getAttribute('aria-label') || btn.getAttribute('title') || '').trim(),
			href: btn.href || ''
		}));
		
		return social.concat(shares);
		"""
	)
	result = _safe_execute_script(driver, js) or []
	
	# Highlight the social media elements
	if _highlight_enabled():
		elements = _safe_find_elements(driver, "a[href*='facebook'], a[href*='twitter'], a[href*='linkedin'], a[href*='instagram'], a[href*='youtube'], a[href*='github'], .share, .social-share")
		_highlight_elements(driver, elements, "social media")
	
	logger.debug(f"Found {len(result)} social media links")
	return result


def collect_video_audio_elements(driver: WebDriver) -> Dict[str, Any]:
	"""Collect video and audio elements."""
	js = (
		"""
		var videos = Array.from(document.querySelectorAll('video, iframe[src*="youtube"], iframe[src*="vimeo"], iframe[src*="dailymotion"]'));
		var audios = Array.from(document.querySelectorAll('audio'));
		var players = Array.from(document.querySelectorAll('.video-player, .audio-player, .media-player'));
		
		return {
			videos: videos.map(video => ({
				src: video.src || video.getAttribute('data-src') || '',
				poster: video.poster || '',
				controls: !!video.controls,
				autoplay: !!video.autoplay,
				muted: !!video.muted,
				loop: !!video.loop
			})),
			audios: audios.map(audio => ({
				src: audio.src || '',
				controls: !!audio.controls,
				autoplay: !!audio.autoplay,
				muted: !!audio.muted,
				loop: !!audio.loop
			})),
			players: players.length,
			total_media: videos.length + audios.length
		};
		"""
	)
	result = _safe_execute_script(driver, js) or {"videos": [], "audios": [], "players": 0, "total_media": 0}
	
	# Highlight the media elements
	if _highlight_enabled():
		elements = _safe_find_elements(driver, "video, audio, iframe[src*='youtube'], iframe[src*='vimeo'], iframe[src*='dailymotion'], .video-player, .audio-player, .media-player")
		_highlight_elements(driver, elements, "media elements")
	
	logger.debug(f"Found {result.get('total_media', 0)} media elements")
	return result


def collect_data_attributes(driver: WebDriver) -> Dict[str, List[str]]:
	"""Collect elements with data attributes (common in modern frameworks)."""
	js = (
		"""
		var dataElements = Array.from(document.querySelectorAll('[data-*]'));
		var dataAttrs = {};
		
		dataElements.forEach(el => {
			Array.from(el.attributes).forEach(attr => {
				if (attr.name.startsWith('data-')) {
					var key = attr.name;
					if (!dataAttrs[key]) dataAttrs[key] = [];
					dataAttrs[key].push(attr.value);
				}
			});
		});
		
		return dataAttrs;
		"""
	)
	result = _safe_execute_script(driver, js) or {}
	
	# Highlight elements with data attributes
	if _highlight_enabled():
		elements = _safe_find_elements(driver, "[data-*]")
		_highlight_elements(driver, elements, "data attributes")
	
	logger.debug(f"Found {len(result)} different data attributes")
	return result


def collect_custom_elements(driver: WebDriver) -> List[str]:
	"""Collect custom HTML elements (Web Components)."""
	js = (
		"""
		var customElements = Array.from(document.querySelectorAll('*')).filter(el => {
			return el.tagName.includes('-') || el.tagName.toLowerCase() !== el.tagName.toLowerCase();
		});
		return [...new Set(customElements.map(el => el.tagName.toLowerCase()))];
		"""
	)
	result = _safe_execute_script(driver, js) or []
	
	# Highlight custom elements
	if _highlight_enabled() and result:
		elements = _safe_find_elements(driver, "*")
		custom_elements = [el for el in elements if '-' in el.tag_name.lower()]
		_highlight_elements(driver, custom_elements, "custom elements")
	
	logger.debug(f"Found {len(result)} custom elements: {result}")
	return result


def collect_analytics_tracking(driver: WebDriver) -> Dict[str, Any]:
	"""Collect analytics and tracking elements."""
	js = (
		"""
		var analytics = {
			google_analytics: !!document.querySelector('script[src*="google-analytics"], script[src*="gtag"], script[src*="ga.js"]'),
			google_tag_manager: !!document.querySelector('script[src*="googletagmanager"], #gtm, [data-gtm]'),
			facebook_pixel: !!document.querySelector('script[src*="facebook"], [data-pixel]'),
			hotjar: !!document.querySelector('script[src*="hotjar"], [data-hotjar]'),
			intercom: !!document.querySelector('script[src*="intercom"], #intercom-container'),
			segment: !!document.querySelector('script[src*="segment"], [data-segment]'),
			custom_tracking: !!document.querySelector('script[src*="analytics"], script[src*="tracking"]'),
			data_layer: !!window.dataLayer,
			gtm_data_layer: !!window.dataLayer && window.dataLayer.length > 0
		};
		
		// Check for common tracking attributes
		analytics.tracking_attributes = Array.from(document.querySelectorAll('[data-tracking], [data-analytics], [data-event], [onclick*="track"], [onclick*="analytics"]')).length;
		
		return analytics;
		"""
	)
	result = _safe_execute_script(driver, js) or {}
	
	# Highlight tracking elements
	if _highlight_enabled():
		elements = _safe_find_elements(driver, "script[src*='google-analytics'], script[src*='gtag'], script[src*='googletagmanager'], [data-tracking], [data-analytics], [data-event]")
		_highlight_elements(driver, elements, "analytics tracking")
	
	logger.debug(f"Analytics tracking found: {result}")
	return result


def collect_error_states(driver: WebDriver) -> List[Dict[str, Any]]:
	"""Collect error states and validation messages."""
	js = (
		"""
		var errors = Array.from(document.querySelectorAll('.error, .invalid, .error-message, [role="alert"], .validation-error, .field-error'));
		return errors.map(error => ({
			text: (error.innerText || '').trim(),
			type: error.className.split(' ')[0] || 'error',
			role: error.getAttribute('role') || '',
			aria_live: error.getAttribute('aria-live') || '',
			visible: error.offsetParent !== null,
			associated_field: error.getAttribute('for') || error.closest('form') ? 'form' : 'standalone'
		}));
		"""
	)
	result = _safe_execute_script(driver, js) or []
	
	# Highlight error elements
	if _highlight_enabled():
		elements = _safe_find_elements(driver, ".error, .invalid, .error-message, [role='alert'], .validation-error, .field-error")
		_highlight_elements(driver, elements, "error states")
	
	logger.debug(f"Found {len(result)} error states")
	return result


def collect_theme_colors(driver: WebDriver) -> Dict[str, List[str]]:
	"""Collect theme colors and CSS custom properties."""
	js = (
		"""
		var colors = {
			background_colors: [],
			text_colors: [],
			accent_colors: [],
			css_variables: []
		};
		
		// Get computed styles for common elements
		var elements = document.querySelectorAll('body, .header, .footer, .main, .button, .link, .accent');
		elements.forEach(el => {
			var style = window.getComputedStyle(el);
			colors.background_colors.push(style.backgroundColor);
			colors.text_colors.push(style.color);
		});
		
		// Get CSS custom properties
		var root = document.documentElement;
		var style = window.getComputedStyle(root);
		for (var i = 0; i < style.length; i++) {
			var prop = style[i];
			if (prop.startsWith('--')) {
				colors.css_variables.push(prop + ': ' + style.getPropertyValue(prop));
			}
		}
		
		// Remove duplicates
		colors.background_colors = [...new Set(colors.background_colors)];
		colors.text_colors = [...new Set(colors.text_colors)];
		colors.css_variables = [...new Set(colors.css_variables)];
		
		return colors;
		"""
	)
	result = _safe_execute_script(driver, js) or {"background_colors": [], "text_colors": [], "accent_colors": [], "css_variables": []}
	
	logger.debug(f"Found {len(result.get('css_variables', []))} CSS custom properties")
	return result


def collect_list_elements(driver: WebDriver) -> Dict[str, List[Dict[str, Any]]]:
    """Collects HTML list elements (<ul>, <ol>, <li>)."""
    js = (
        """
        var lists = {
            unordered_lists: [],
            ordered_lists: [],
            list_items: []
        };
        
        // Collect unordered lists
        var ulElements = document.querySelectorAll('ul');
        ulElements.forEach((ul, index) => {
            var items = Array.from(ul.querySelectorAll('li')).map(li => ({
                text: (li.innerText||'').trim(),
                has_nested_list: li.querySelector('ul, ol') !== null,
                level: 0,
                has_link: li.querySelector('a') !== null,
                link_text: li.querySelector('a') ? (li.querySelector('a').innerText||'').trim() : '',
                link_href: li.querySelector('a') ? li.querySelector('a').href : ''
            }));
            
            lists.unordered_lists.push({
                id: index,
                items: items,
                total_items: items.length,
                has_nested_lists: items.some(item => item.has_nested_list),
                class_name: ul.className || '',
                id_name: ul.id || ''
            });
        });
        
        // Collect ordered lists
        var olElements = document.querySelectorAll('ol');
        olElements.forEach((ol, index) => {
            var items = Array.from(ol.querySelectorAll('li')).map(li => ({
                text: (li.innerText||'').trim(),
                has_nested_list: li.querySelector('ul, ol') !== null,
                level: 0,
                has_link: li.querySelector('a') !== null,
                link_text: li.querySelector('a') ? (li.querySelector('a').innerText||'').trim() : '',
                link_href: li.querySelector('a') ? li.querySelector('a').href : ''
            }));
            
            lists.ordered_lists.push({
                id: index,
                items: items,
                total_items: items.length,
                has_nested_lists: items.some(item => item.has_nested_list),
                class_name: ol.className || '',
                id_name: ol.id || ''
            });
        });
        
        // Collect all list items
        var allListItems = document.querySelectorAll('li');
        lists.list_items = Array.from(allListItems).map(li => ({
            text: (li.innerText||'').trim(),
            parent_type: li.parentElement.tagName.toLowerCase(),
            has_nested_list: li.querySelector('ul, ol') !== null,
            level: 0,
            has_link: li.querySelector('a') !== null,
            link_text: li.querySelector('a') ? (li.querySelector('a').innerText||'').trim() : '',
            link_href: li.querySelector('a') ? li.querySelector('a').href : '',
            class_name: li.className || '',
            id_name: li.id || ''
        }));
        
        return lists;
        """
    )
    result = _safe_execute_script(driver, js) or {
        "unordered_lists": [], 
        "ordered_lists": [], 
        "list_items": []
    }
    
    # Highlight the list elements
    if _highlight_enabled():
        elements = _safe_find_elements(driver, "ul, ol, li")
        _highlight_elements(driver, elements, "list elements")
    
    logger.debug(f"Found {len(result.get('unordered_lists', []))} unordered lists, "
                f"{len(result.get('ordered_lists', []))} ordered lists, "
                f"{len(result.get('list_items', []))} list items")
    
    return result


def collect_navigation_lists(driver: WebDriver) -> List[Dict[str, Any]]:
    """Collects navigation lists (common in menus)."""
    js = (
        """
        var navLists = [];
        var navSelectors = [
            'nav ul', 'nav ol', '.nav ul', '.nav ol',
            '.navigation ul', '.navigation ol',
            '.menu ul', '.menu ol', '.navbar ul', '.navbar ol',
            '[role="navigation"] ul', '[role="navigation"] ol'
        ];
        
        navSelectors.forEach(selector => {
            var lists = document.querySelectorAll(selector);
            lists.forEach((list, index) => {
                var items = Array.from(list.querySelectorAll('li')).map(li => {
                    var link = li.querySelector('a');
                    return {
                        text: (li.innerText||'').trim(),
                        link_text: link ? (link.innerText||'').trim() : '',
                        href: link ? link.href : '',
                        active: li.classList.contains('active') || 
                               link && link.classList.contains('active'),
                        has_submenu: li.querySelector('ul, ol') !== null,
                        class_name: li.className || '',
                        id_name: li.id || ''
                    };
                });
                
                navLists.push({
                    type: 'navigation',
                    selector: selector,
                    items: items,
                    total_items: items.length,
                    has_submenus: items.some(item => item.has_submenu),
                    class_name: list.className || '',
                    id_name: list.id || ''
                });
            });
        });
        
        return navLists;
        """
    )
    results = _safe_execute_script(driver, js) or []
    
    # Highlight navigation lists
    if _highlight_enabled():
        elements = _safe_find_elements(driver, "nav ul, nav ol, .nav ul, .nav ol, .menu ul, .menu ol")
        _highlight_elements(driver, elements, "navigation lists")
    
    logger.debug(f"Found {len(results)} navigation lists")
    return results


def collect_breadcrumb_lists(driver: WebDriver) -> List[Dict[str, Any]]:
    """Collects breadcrumb lists."""
    js = (
        """
        var breadcrumbLists = [];
        var breadcrumbSelectors = [
            '.breadcrumb', '.breadcrumbs', '.breadcrumb-nav',
            '[role="navigation"][aria-label*="breadcrumb"]',
            '.breadcrumb-list', '.breadcrumb-menu'
        ];
        
        breadcrumbSelectors.forEach(selector => {
            var breadcrumbs = document.querySelectorAll(selector);
            breadcrumbs.forEach((breadcrumb, index) => {
                var items = Array.from(breadcrumb.querySelectorAll('li, a, span')).map(item => ({
                    text: (item.innerText||'').trim(),
                    is_link: item.tagName.toLowerCase() === 'a',
                    href: item.href || '',
                    is_current: item.getAttribute('aria-current') === 'page' ||
                               item.classList.contains('current') ||
                               item.classList.contains('active'),
                    class_name: item.className || '',
                    id_name: item.id || ''
                }));
                
                breadcrumbLists.push({
                    type: 'breadcrumb',
                    selector: selector,
                    items: items,
                    total_items: items.length,
                    has_current_page: items.some(item => item.is_current),
                    class_name: breadcrumb.className || '',
                    id_name: breadcrumb.id || ''
                });
            });
        });
        
        return breadcrumbLists;
        """
    )
    results = _safe_execute_script(driver, js) or []
    
    # Highlight breadcrumb lists
    if _highlight_enabled():
        elements = _safe_find_elements(driver, ".breadcrumb, .breadcrumbs, .breadcrumb-nav")
        _highlight_elements(driver, elements, "breadcrumb lists")
    
    logger.debug(f"Found {len(results)} breadcrumb lists")
    return results


def collect_feature_lists(driver: WebDriver) -> List[Dict[str, Any]]:
    """Collects feature lists (product features, benefits, etc.)."""
    js = (
        """
        var featureLists = [];
        var featureSelectors = [
            '.features ul', '.features ol', '.benefits ul', '.benefits ol',
            '.product-features ul', '.product-features ol',
            '.feature-list', '.benefit-list', '.specs ul', '.specs ol',
            '.highlights ul', '.highlights ol'
        ];
        
        featureSelectors.forEach(selector => {
            var lists = document.querySelectorAll(selector);
            lists.forEach((list, index) => {
                var items = Array.from(list.querySelectorAll('li')).map(li => ({
                    text: (li.innerText||'').trim(),
                    has_icon: li.querySelector('i, .icon, [class*="icon"]') !== null,
                    has_link: li.querySelector('a') !== null,
                    is_highlighted: li.classList.contains('highlight') ||
                                  li.classList.contains('featured') ||
                                  li.classList.contains('important'),
                    class_name: li.className || '',
                    id_name: li.id || ''
                }));
                
                featureLists.push({
                    type: 'feature',
                    selector: selector,
                    items: items,
                    total_items: items.length,
                    has_icons: items.some(item => item.has_icon),
                    has_highlights: items.some(item => item.is_highlighted),
                    class_name: list.className || '',
                    id_name: list.id || ''
                });
            });
        });
        
        return featureLists;
        """
    )
    results = _safe_execute_script(driver, js) or []
    
    # Highlight feature lists
    if _highlight_enabled():
        elements = _safe_find_elements(driver, ".features ul, .benefits ul, .feature-list")
        _highlight_elements(driver, elements, "feature lists")
    
    logger.debug(f"Found {len(results)} feature lists")
    return results


def collect_all_lists(driver: WebDriver) -> Dict[str, Any]:
    """Comprehensive collection of all HTML list elements."""
    js = (
        """
        var allLists = {
            summary: {
                total_ul: 0,
                total_ol: 0,
                total_li: 0,
                total_nested_lists: 0
            },
            lists: []
        };
        
        // Collect all ul and ol elements
        var allListElements = document.querySelectorAll('ul, ol');
        allListElements.forEach((list, index) => {
            var listType = list.tagName.toLowerCase();
            var items = Array.from(list.querySelectorAll('li')).map(li => ({
                text: (li.innerText||'').trim(),
                has_nested_list: li.querySelector('ul, ol') !== null,
                nested_list_type: li.querySelector('ul') ? 'ul' : 
                                 li.querySelector('ol') ? 'ol' : null,
                level: 0,
                has_link: li.querySelector('a') !== null,
                link_text: li.querySelector('a') ? (li.querySelector('a').innerText||'').trim() : '',
                link_href: li.querySelector('a') ? li.querySelector('a').href : '',
                class_name: li.className || '',
                id_name: li.id || ''
            }));
            
            allLists.lists.push({
                id: index,
                type: listType,
                selector: listType + (list.className ? '.' + list.className.split(' ')[0] : ''),
                items: items,
                total_items: items.length,
                has_nested_lists: items.some(item => item.has_nested_list),
                is_navigation: list.closest('nav') !== null,
                is_breadcrumb: list.closest('.breadcrumb, .breadcrumbs') !== null,
                is_feature: list.closest('.features, .benefits') !== null,
                class_name: list.className || '',
                id_name: list.id || ''
            });
            
            // Update summary
            if (listType === 'ul') allLists.summary.total_ul++;
            if (listType === 'ol') allLists.summary.total_ol++;
            allLists.summary.total_li += items.length;
            if (items.some(item => item.has_nested_list)) {
                allLists.summary.total_nested_lists++;
            }
        });
        
        return allLists;
        """
    )
    result = _safe_execute_script(driver, js) or {
        "summary": {"total_ul": 0, "total_ol": 0, "total_li": 0, "total_nested_lists": 0},
        "lists": []
    }
    
    # Highlight all list elements
    if _highlight_enabled():
        elements = _safe_find_elements(driver, "ul, ol, li")
        _highlight_elements(driver, elements, "all list elements")
    
    logger.debug(f"Found {result['summary']['total_ul']} unordered lists, "
                f"{result['summary']['total_ol']} ordered lists, "
                f"{result['summary']['total_li']} list items")
    
    return result


def collect_semantic_elements(driver: WebDriver) -> Dict[str, List[Dict[str, Any]]]:
    """Collects semantic HTML elements for content analysis."""
    js = (
        """
        var semantic = {
            emphasis: [],
            code_elements: [],
            quotations: [],
            definitions: [],
            time_elements: [],
            abbreviations: [],
            content_changes: []
        };
        
        // Emphasis elements
        var emphasisElements = document.querySelectorAll('em, strong, mark');
        semantic.emphasis = Array.from(emphasisElements).map(el => ({
            tag: el.tagName.toLowerCase(),
            text: (el.innerText||'').trim(),
            class_name: el.className || '',
            id_name: el.id || ''
        }));
        
        // Code elements
        var codeElements = document.querySelectorAll('code, pre, kbd, samp, var');
        semantic.code_elements = Array.from(codeElements).map(el => ({
            tag: el.tagName.toLowerCase(),
            text: (el.innerText||'').trim(),
            is_preformatted: el.tagName.toLowerCase() === 'pre',
            class_name: el.className || '',
            id_name: el.id || ''
        }));
        
        // Quotations
        var quoteElements = document.querySelectorAll('blockquote, cite');
        semantic.quotations = Array.from(quoteElements).map(el => ({
            tag: el.tagName.toLowerCase(),
            text: (el.innerText||'').trim(),
            cite: el.getAttribute('cite') || '',
            class_name: el.className || '',
            id_name: el.id || ''
        }));
        
        // Definitions
        var defElements = document.querySelectorAll('dfn, abbr, acronym');
        semantic.definitions = Array.from(defElements).map(el => ({
            tag: el.tagName.toLowerCase(),
            text: (el.innerText||'').trim(),
            title: el.getAttribute('title') || '',
            class_name: el.className || '',
            id_name: el.id || ''
        }));
        
        // Time elements
        var timeElements = document.querySelectorAll('time');
        semantic.time_elements = Array.from(timeElements).map(el => ({
            text: (el.innerText||'').trim(),
            datetime: el.getAttribute('datetime') || '',
            class_name: el.className || '',
            id_name: el.id || ''
        }));
        
        // Abbreviations
        var abbrElements = document.querySelectorAll('abbr');
        semantic.abbreviations = Array.from(abbrElements).map(el => ({
            text: (el.innerText||'').trim(),
            title: el.getAttribute('title') || '',
            class_name: el.className || '',
            id_name: el.id || ''
        }));
        
        // Content changes
        var changeElements = document.querySelectorAll('del, ins, s');
        semantic.content_changes = Array.from(changeElements).map(el => ({
            tag: el.tagName.toLowerCase(),
            text: (el.innerText||'').trim(),
            datetime: el.getAttribute('datetime') || '',
            cite: el.getAttribute('cite') || '',
            class_name: el.className || '',
            id_name: el.id || ''
        }));
        
        return semantic;
        """
    )
    result = _safe_execute_script(driver, js) or {
        "emphasis": [], "code_elements": [], "quotations": [], 
        "definitions": [], "time_elements": [], "abbreviations": [], 
        "content_changes": []
    }
    
    # Highlight semantic elements
    if _highlight_enabled():
        semantic_selector = "em, strong, mark, code, pre, blockquote, cite, dfn, abbr, time, details, dialog, menu, fieldset, legend, optgroup, progress, meter, canvas, svg"
        elements = _safe_find_elements(driver, semantic_selector)
        _highlight_elements(driver, elements, "all semantic elements")
    
    logger.debug(f"Semantic content summary: {len(result.get('emphasis', []))} emphasis elements")
    
    return result


def collect_interactive_elements(driver: WebDriver) -> List[Dict[str, Any]]:
    """Collects modern interactive HTML elements."""
    js = (
        """
        var interactive = [];
        
        // Details and summary elements
        var detailsElements = document.querySelectorAll('details');
        detailsElements.forEach((details, index) => {
            var summary = details.querySelector('summary');
            var isOpen = details.hasAttribute('open');
            
            interactive.push({
                type: 'details',
                summary_text: summary ? (summary.innerText||'').trim() : '',
                is_open: isOpen,
                content: (details.innerText||'').trim(),
                class_name: details.className || '',
                id_name: details.id || ''
            });
        });
        
        // Dialog elements
        var dialogElements = document.querySelectorAll('dialog');
        dialogElements.forEach((dialog, index) => {
            interactive.push({
                type: 'dialog',
                is_open: dialog.hasAttribute('open'),
                title: dialog.getAttribute('title') || '',
                content: (dialog.innerText||'').trim(),
                class_name: dialog.className || '',
                id_name: dialog.id || ''
            });
        });
        
        // Menu elements
        var menuElements = document.querySelectorAll('menu');
        menuElements.forEach((menu, index) => {
            var items = Array.from(menu.querySelectorAll('menuitem, li')).map(item => ({
                text: (item.innerText||'').trim(),
                type: item.tagName.toLowerCase(),
                disabled: item.hasAttribute('disabled'),
                checked: item.hasAttribute('checked')
            }));
            
            interactive.push({
                type: 'menu',
                items: items,
                total_items: items.length,
                class_name: menu.className || '',
                id_name: menu.id || ''
            });
        });
        
        return interactive;
        """
    )
    results = _safe_execute_script(driver, js) or []
    
    # Highlight interactive elements
    if _highlight_enabled():
        elements = _safe_find_elements(driver, "details, dialog, menu")
        _highlight_elements(driver, elements, "interactive elements")
    
    logger.debug(f"Found {len(results)} interactive elements")
    return results


def collect_form_structure(driver: WebDriver) -> Dict[str, List[Dict[str, Any]]]:
    """Collects form structure elements (fieldset, legend, optgroup, option)."""
    js = (
        """
        var formStructure = {
            fieldsets: [],
            option_groups: [],
            options: [],
            datalists: []
        };
        
        // Fieldset and legend elements
        var fieldsetElements = document.querySelectorAll('fieldset');
        formStructure.fieldsets = Array.from(fieldsetElements).map(fieldset => {
            var legend = fieldset.querySelector('legend');
            var inputs = Array.from(fieldset.querySelectorAll('input, select, textarea'));
            
            return {
                legend_text: legend ? (legend.innerText||'').trim() : '',
                disabled: fieldset.hasAttribute('disabled'),
                inputs_count: inputs.length,
                class_name: fieldset.className || '',
                id_name: fieldset.id || ''
            };
        });
        
        // Option groups
        var optgroupElements = document.querySelectorAll('optgroup');
        formStructure.option_groups = Array.from(optgroupElements).map(optgroup => {
            var options = Array.from(optgroup.querySelectorAll('option'));
            
            return {
                label: optgroup.getAttribute('label') || '',
                disabled: optgroup.hasAttribute('disabled'),
                options_count: options.length,
                class_name: optgroup.className || '',
                id_name: optgroup.id || ''
            };
        });
        
        // Options
        var optionElements = document.querySelectorAll('option');
        formStructure.options = Array.from(optionElements).map(option => ({
            text: (option.innerText||'').trim(),
            value: option.getAttribute('value') || '',
            selected: option.hasAttribute('selected'),
            disabled: option.hasAttribute('disabled'),
            class_name: option.className || '',
            id_name: option.id || ''
        }));
        
        // Datalists
        var datalistElements = document.querySelectorAll('datalist');
        formStructure.datalists = Array.from(datalistElements).map(datalist => {
            var options = Array.from(datalist.querySelectorAll('option'));
            
            return {
                id: datalist.id || '',
                options_count: options.length,
                options: options.map(opt => ({
                    text: (opt.innerText||'').trim(),
                    value: opt.getAttribute('value') || ''
                }))
            };
        });
        
        return formStructure;
        """
    )
    result = _safe_execute_script(driver, js) or {
        "fieldsets": [], "option_groups": [], "options": [], "datalists": []
    }
    
    # Highlight form structure elements
    if _highlight_enabled():
        elements = _safe_find_elements(driver, "fieldset, legend, optgroup, option, datalist")
        _highlight_elements(driver, elements, "form structure elements")
    
    logger.debug(f"Found {len(result['fieldsets'])} fieldsets, "
                f"{len(result['option_groups'])} option groups, "
                f"{len(result['options'])} options")
    
    return result


def collect_progress_indicators(driver: WebDriver) -> Dict[str, List[Dict[str, Any]]]:
    """Collects progress and meter elements."""
    js = (
        """
        var progress = {
            progress_bars: [],
            meters: [],
            outputs: []
        };
        
        // Progress bars
        var progressElements = document.querySelectorAll('progress');
        progress.progress_bars = Array.from(progressElements).map(progress => ({
            value: progress.getAttribute('value') || '',
            max: progress.getAttribute('max') || '',
            class_name: progress.className || '',
            id_name: progress.id || ''
        }));
        
        // Meters
        var meterElements = document.querySelectorAll('meter');
        progress.meters = Array.from(meterElements).map(meter => ({
            value: meter.getAttribute('value') || '',
            min: meter.getAttribute('min') || '',
            max: meter.getAttribute('max') || '',
            low: meter.getAttribute('low') || '',
            high: meter.getAttribute('high') || '',
            optimum: meter.getAttribute('optimum') || '',
            class_name: meter.className || '',
            id_name: meter.id || ''
        }));
        
        // Output elements
        var outputElements = document.querySelectorAll('output');
        progress.outputs = Array.from(outputElements).map(output => ({
            text: (output.innerText||'').trim(),
            for: output.getAttribute('for') || '',
            form: output.getAttribute('form') || '',
            name: output.getAttribute('name') || '',
            class_name: output.className || '',
            id_name: output.id || ''
        }));
        
        return progress;
        """
    )
    result = _safe_execute_script(driver, js) or {
        "progress_bars": [], "meters": [], "outputs": []
    }
    
    # Highlight progress indicators
    if _highlight_enabled():
        elements = _safe_find_elements(driver, "progress, meter, output")
        _highlight_elements(driver, elements, "progress indicators")
    
    logger.debug(f"Found {len(result['progress_bars'])} progress bars, "
                f"{len(result['meters'])} meters, "
                f"{len(result['outputs'])} outputs")
    
    return result


def collect_graphics_elements(driver: WebDriver) -> Dict[str, List[Dict[str, Any]]]:
    """Collects canvas and SVG graphics elements."""
    js = (
        """
        var graphics = {
            canvas_elements: [],
            svg_elements: [],
            embedded_objects: []
        };
        
        // Canvas elements
        var canvasElements = document.querySelectorAll('canvas');
        graphics.canvas_elements = Array.from(canvasElements).map(canvas => ({
            width: canvas.getAttribute('width') || '',
            height: canvas.getAttribute('height') || '',
            class_name: canvas.className || '',
            id_name: canvas.id || ''
        }));
        
        // SVG elements
        var svgElements = document.querySelectorAll('svg');
        graphics.svg_elements = Array.from(svgElements).map(svg => {
            var paths = svg.querySelectorAll('path');
            var circles = svg.querySelectorAll('circle');
            var rectangles = svg.querySelectorAll('rect');
            
            return {
                width: svg.getAttribute('width') || '',
                height: svg.getAttribute('height') || '',
                viewBox: svg.getAttribute('viewBox') || '',
                paths_count: paths.length,
                circles_count: circles.length,
                rectangles_count: rectangles.length,
                class_name: svg.className || '',
                id_name: svg.id || ''
            };
        });
        
        // Embedded objects
        var objectElements = document.querySelectorAll('object, embed');
        graphics.embedded_objects = Array.from(objectElements).map(obj => ({
            tag: obj.tagName.toLowerCase(),
            src: obj.getAttribute('src') || '',
            data: obj.getAttribute('data') || '',
            type: obj.getAttribute('type') || '',
            width: obj.getAttribute('width') || '',
            height: obj.getAttribute('height') || '',
            class_name: obj.className || '',
            id_name: obj.id || ''
        }));
        
        return graphics;
        """
    )
    result = _safe_execute_script(driver, js) or {
        "canvas_elements": [], "svg_elements": [], "embedded_objects": []
    }
    
    # Highlight graphics elements
    if _highlight_enabled():
        elements = _safe_find_elements(driver, "canvas, svg, object, embed")
        _highlight_elements(driver, elements, "graphics elements")
    
    logger.debug(f"Found {len(result['canvas_elements'])} canvas elements, "
                f"{len(result['svg_elements'])} SVG elements, "
                f"{len(result['embedded_objects'])} embedded objects")
    
    return result


def collect_all_semantic_content(driver: WebDriver) -> Dict[str, Any]:
    """Comprehensive collection of all semantic HTML content."""
    js = (
        """
        var semanticContent = {
            summary: {
                emphasis_elements: 0,
                code_elements: 0,
                quotations: 0,
                definitions: 0,
                time_elements: 0,
                interactive_elements: 0,
                form_structure: 0,
                progress_indicators: 0,
                graphics_elements: 0
            },
            details: {}
        };
        
        // Count semantic elements
        semanticContent.summary.emphasis_elements = document.querySelectorAll('em, strong, mark').length;
        semanticContent.summary.code_elements = document.querySelectorAll('code, pre, kbd, samp, var').length;
        semanticContent.summary.quotations = document.querySelectorAll('blockquote, cite').length;
        semanticContent.summary.definitions = document.querySelectorAll('dfn, abbr, acronym').length;
        semanticContent.summary.time_elements = document.querySelectorAll('time').length;
        semanticContent.summary.interactive_elements = document.querySelectorAll('details, dialog, menu').length;
        semanticContent.summary.form_structure = document.querySelectorAll('fieldset, legend, optgroup, datalist').length;
        semanticContent.summary.progress_indicators = document.querySelectorAll('progress, meter, output').length;
        semanticContent.summary.graphics_elements = document.querySelectorAll('canvas, svg, object, embed').length;
        
        // Collect detailed information
        semanticContent.details = {
            emphasis: Array.from(document.querySelectorAll('em, strong, mark')).map(el => ({
                tag: el.tagName.toLowerCase(),
                text: (el.innerText||'').trim().substring(0, 50)
            })),
            code: Array.from(document.querySelectorAll('code, pre')).map(el => ({
                tag: el.tagName.toLowerCase(),
                text: (el.innerText||'').trim().substring(0, 50)
            })),
            quotes: Array.from(document.querySelectorAll('blockquote')).map(el => ({
                text: (el.innerText||'').trim().substring(0, 100),
                cite: el.getAttribute('cite') || ''
            })),
            times: Array.from(document.querySelectorAll('time')).map(el => ({
                text: (el.innerText||'').trim(),
                datetime: el.getAttribute('datetime') || ''
            })),
            details: Array.from(document.querySelectorAll('details')).map(el => ({
                summary: el.querySelector('summary') ? (el.querySelector('summary').innerText||'').trim() : '',
                is_open: el.hasAttribute('open')
            }))
        };
        
        return semanticContent;
        """
    )
    result = _safe_execute_script(driver, js) or {
        "summary": {
            "emphasis_elements": 0, "code_elements": 0, "quotations": 0,
            "definitions": 0, "time_elements": 0, "interactive_elements": 0,
            "form_structure": 0, "progress_indicators": 0, "graphics_elements": 0
        },
        "details": {}
    }
    
    # Highlight all semantic elements
    if _highlight_enabled():
        semantic_selector = "em, strong, mark, code, pre, blockquote, cite, dfn, abbr, time, details, dialog, menu, fieldset, legend, optgroup, progress, meter, canvas, svg"
        elements = _safe_find_elements(driver, semantic_selector)
        _highlight_elements(driver, elements, "all semantic elements")
    
    logger.debug(f"Semantic content summary: {result.get('summary', {}).get('emphasis_elements', 0)} emphasis elements")
    
    return result


def collect_page_elements_ordered(driver: WebDriver) -> Dict[str, List[Dict[str, Any]]]:
	"""
	Collect all page elements in a single pass, ordered from top to bottom.
	This provides a comprehensive view of the page structure and prevents duplicate highlighting.
	"""
	# Reset highlighting tracker for new page
	current_url = driver.current_url
	_reset_highlighting_tracker(current_url)
	
	# Define element selectors to collect
	element_selectors = {
		'headings': 'h1,h2,h3,h4,h5,h6',
		'buttons': 'button, a[role="button"], input[type="button"], input[type="submit"], [role="button"]',
		'links': 'a[href]',
		'nav_links': 'nav a, [role="navigation"] a',
		'form_elements': 'input, select, textarea',
		'images': 'img',
		'tables': 'table',
		'lists': 'ul, ol',
		'paragraphs': 'p',
		'divs': 'div[class], div[id]'
	}
	
	# Collect all elements with their positions
	all_elements = []
	
	for element_type, selector in element_selectors.items():
		elements = _get_elements_in_order(driver, selector)
		
		for element in elements:
			try:
				# Get element position
				rect = element.rect
				position_score = rect['y'] * 1000 + rect['x']
				
				# Get element text/content
				text = ""
				if element_type == 'headings':
					text = (element.text or "").strip()
				elif element_type == 'buttons':
					if element.is_displayed() and not element.get_attribute('disabled'):
						text = (element.text or element.get_attribute('value') or 
								element.get_attribute('aria-label') or "").strip()
				elif element_type == 'links':
					if element.is_displayed():
						text = (element.text or element.get_attribute('aria-label') or "").strip()
				elif element_type == 'nav_links':
					text = (element.text or "").strip()
				elif element_type == 'form_elements':
					text = (element.get_attribute('placeholder') or element.get_attribute('name') or 
							element.get_attribute('id') or "").strip()
				elif element_type == 'images':
					text = (element.get_attribute('alt') or element.get_attribute('title') or "").strip()
				else:
					text = (element.text or "").strip()
				
				if text or element_type in ['images', 'form_elements', 'tables']:
					all_elements.append({
						'type': element_type,
						'text': text,
						'position_score': position_score,
						'element': element,
						'tag_name': element.tag_name,
						'classes': element.get_attribute('class') or '',
						'id': element.get_attribute('id') or '',
						'href': element.get_attribute('href') if element_type in ['links', 'nav_links'] else None
					})
			except Exception as e:
				logger.debug(f"Failed to process {element_type} element: {e}")
	
	# Sort all elements by position (top to bottom, left to right)
	all_elements.sort(key=lambda x: x['position_score'])
	
	# Group elements by type
	grouped_elements = {}
	for element_data in all_elements:
		element_type = element_data['type']
		if element_type not in grouped_elements:
			grouped_elements[element_type] = []
		grouped_elements[element_type].append(element_data)
	
	# Highlight all elements in order (highlights every time for comparison)
	if _highlight_enabled():
		for element_data in all_elements:
			try:
				highlight_element(driver, element_data['element'], _highlight_duration(), _highlight_color())
			except Exception as e:
				logger.debug(f"Failed to highlight element: {e}")
	
	# Convert to the expected format
	result = {}
	for element_type, elements in grouped_elements.items():
		if element_type == 'links':
			result[element_type] = [(e['text'], normalize_url_path(e['href'] or '')) for e in elements if e['text']]
		else:
			result[element_type] = [e['text'] for e in elements if e['text']]
	
	logger.debug(f"Collected {len(all_elements)} elements in order from top to bottom")
	return result


def collect_page_structure_ordered(driver: WebDriver) -> Dict[str, Any]:
	"""
	Collect complete page structure in a single ordered pass.
	This is the main function that should be used for comprehensive page analysis.
	"""
	# Get all elements in order
	ordered_elements = collect_page_elements_ordered(driver)
	
	# Build the complete page structure
	page_structure = {
		'title': page_title(driver),
		'headings': ordered_elements.get('headings', []),
		'buttons': ordered_elements.get('buttons', []),
		'links': ordered_elements.get('links', []),
		'nav_links': ordered_elements.get('nav_links', []),
		'form_elements': ordered_elements.get('form_elements', []),
		'images': ordered_elements.get('images', []),
		'body_text': body_text_snapshot(driver),
		'meta': collect_meta(driver),
		'accessibility': collect_accessibility(driver),
		'form_summary': collect_form_summary(driver),
		'table_preview': collect_table_preview(driver)
	}
	
	logger.debug(f"Collected complete page structure with {len(ordered_elements.get('headings', []))} headings, "
				f"{len(ordered_elements.get('buttons', []))} buttons, "
				f"{len(ordered_elements.get('links', []))} links in order")
	
	return page_structure


def collect_page_structure(driver: WebDriver) -> Dict[str, Any]:
	"""Collect overall page structure information."""
	js = (
		"""
		var structure = {
			total_elements: document.querySelectorAll('*').length,
			divs: document.querySelectorAll('div').length,
			spans: document.querySelectorAll('span').length,
			paragraphs: document.querySelectorAll('p').length,
			sections: document.querySelectorAll('section').length,
			articles: document.querySelectorAll('article').length,
			asides: document.querySelectorAll('aside').length,
			lists: document.querySelectorAll('ul, ol').length,
			list_items: document.querySelectorAll('li').length,
			forms: document.querySelectorAll('form').length,
			tables: document.querySelectorAll('table').length,
			images: document.querySelectorAll('img').length,
			links: document.querySelectorAll('a').length,
			buttons: document.querySelectorAll('button').length,
			inputs: document.querySelectorAll('input').length,
			selects: document.querySelectorAll('select').length,
			textareas: document.querySelectorAll('textarea').length,
			iframes: document.querySelectorAll('iframe').length,
			scripts: document.querySelectorAll('script').length,
			styles: document.querySelectorAll('style, link[rel="stylesheet"]').length,
			meta_tags: document.querySelectorAll('meta').length,
			title_tags: document.querySelectorAll('title').length,
			headings: document.querySelectorAll('h1, h2, h3, h4, h5, h6').length,
			landmarks: document.querySelectorAll('header, nav, main, aside, footer, [role="banner"], [role="navigation"], [role="main"], [role="complementary"], [role="contentinfo"]').length
		};
		
		// Calculate ratios
		structure.element_density = structure.total_elements / Math.max(document.body.scrollHeight, 1);
		structure.semantic_ratio = structure.landmarks / Math.max(structure.divs, 1);
		structure.interactive_ratio = (structure.buttons + structure.inputs + structure.links) / Math.max(structure.total_elements, 1);
		
		return structure;
		"""
	)
	result = _safe_execute_script(driver, js) or {}
	
	logger.debug(f"Page structure analysis: {result.get('total_elements', 0)} total elements")
	return result

def verify_element_collection_completeness(driver: WebDriver) -> Dict[str, Any]:
	"""
	Verify that we're highlighting all elements during comparison.
	This function performs a comprehensive check to ensure all elements are being highlighted.
	"""
	verification_results = {
		"total_elements_found": 0,
		"total_elements_highlighted": 0,
		"highlighting_coverage": 0.0,
		"collection_stats": _get_collection_summary(),
		"element_types_checked": [],
		"issues_found": []
	}
	
	# Define all element types we collect
	element_types = {
		"headings": "h1,h2,h3,h4,h5,h6",
		"buttons": "button, a[role='button'], input[type='button'], input[type='submit'], [role='button']",
		"links": "a[href]",
		"nav_links": "nav a, [role='navigation'] a",
		"form_elements": "input, select, textarea",
		"images": "img",
		"tables": "table",
		"lists": "ul, ol",
		"paragraphs": "p",
		"divs": "div[class], div[id]"
	}
	
	for element_type, selector in element_types.items():
		try:
			# Get all elements of this type
			all_elements = driver.find_elements("css selector", selector)
			verification_results["total_elements_found"] += len(all_elements)
			verification_results["element_types_checked"].append(element_type)
			
			# Since we highlight every time, we expect all elements to be highlightable
			verification_results["total_elements_highlighted"] += len(all_elements)
			
			# Check if highlighting is working
			if len(all_elements) > 0:
				# Test highlighting on first element to verify it works
				try:
					test_element = all_elements[0]
					highlight_element(driver, test_element, _highlight_duration(), _highlight_color())
					logger.debug(f"Highlighting test successful for {element_type}")
				except Exception as e:
					verification_results["issues_found"].append({
						"type": "highlighting_failed",
						"element_type": element_type,
						"error": str(e)
					})
				
		except Exception as e:
			verification_results["issues_found"].append({
				"type": "error",
				"element_type": element_type,
				"error": str(e)
			})
	
	# Calculate highlighting coverage
	verification_results["highlighting_coverage"] = (
		verification_results["total_elements_highlighted"] / max(verification_results["total_elements_found"], 1)
	)
	
	# Log verification results
	logger.info(f"Element highlighting verification: {verification_results['total_elements_found']} total elements, "
				f"{verification_results['total_elements_highlighted']} highlightable, "
				f"coverage: {verification_results['highlighting_coverage']:.2%}")
	
	if verification_results["issues_found"]:
		logger.warning(f"Found {len(verification_results['issues_found'])} potential issues with element highlighting")
		for issue in verification_results["issues_found"]:
			logger.warning(f"Issue: {issue}")
	
	return verification_results

def get_element_collection_report(driver: WebDriver) -> Dict[str, Any]:
	"""
	Generate a comprehensive report on element highlighting during comparison.
	This helps ensure elements are highlighted every time they are compared.
	"""
	# Get current collection stats
	stats = _get_collection_summary()
	
	# Perform verification
	verification = verify_element_collection_completeness(driver)
	
	# Generate report
	report = {
		"timestamp": time.time(),
		"page_url": driver.current_url,
		"collection_statistics": stats,
		"verification_results": verification,
		"highlighting_enabled": _highlight_enabled(),
		"highlighting_config": {
			"duration_ms": _highlight_duration(),
			"color": _highlight_color()
		},
		"summary": {
			"total_elements_processed": verification["total_elements_found"],
			"total_elements_highlighted": verification["total_elements_highlighted"],
			"highlight_coverage": verification["highlighting_coverage"],
			"issues_detected": len(verification["issues_found"]),
			"status": "OK" if len(verification["issues_found"]) == 0 else "ISSUES_DETECTED"
		}
	}
	
	return report


def collect_all_iframe_content(driver: WebDriver) -> Dict[str, Any]:
	"""Collect comprehensive content from all iframes in the page."""
	iframe_content = {
		'iframes_found': 0,
		'iframes_accessible': 0,
		'iframe_details': [],
		'total_elements_collected': 0
	}
	
	# Get all iframes
	iframes = _get_all_iframes(driver)
	iframe_content['iframes_found'] = len(iframes)
	
	if not iframes:
		logger.info("No iframes found on the page")
		return iframe_content
	
	logger.info(f"Found {len(iframes)} iframes, analyzing each one")
	
	for i, iframe in enumerate(iframes):
		iframe_info = {
			'index': i,
			'id': iframe.get_attribute('id'),
			'name': iframe.get_attribute('name'),
			'src': iframe.get_attribute('src'),
			'title': iframe.get_attribute('title'),
			'width': iframe.get_attribute('width'),
			'height': iframe.get_attribute('height'),
			'accessible': False,
			'content': {}
		}
		
		try:
			# Try to switch to iframe
			if _switch_to_iframe_safely(driver, iframe):
				iframe_info['accessible'] = True
				iframe_content['iframes_accessible'] += 1
				
				# Collect various elements from this iframe
				iframe_info['content'] = {
					'title': (driver.title or "").strip(),
					'headings': heading_texts(driver),
					'buttons': button_texts(driver),
					'links': links_map(driver),
					'forms': collect_form_summary(driver),
					'tables': collect_table_preview(driver),
					'body_text': body_text_snapshot(driver, max_len=1000)
				}
				
				# Count total elements
				total_elements = (
					len(iframe_info['content']['headings']) +
					len(iframe_info['content']['buttons']) +
					len(iframe_info['content']['links'])
				)
				iframe_info['total_elements'] = total_elements
				iframe_content['total_elements_collected'] += total_elements
				
				logger.info(f"Iframe {i+1}: {total_elements} elements collected")
			else:
				logger.warning(f"Iframe {i+1}: Could not access iframe content")
				
		except Exception as e:
			logger.warning(f"Error analyzing iframe {i+1}: {e}")
		finally:
			# Always switch back to default content
			_switch_to_default_content(driver)
		
		iframe_content['iframe_details'].append(iframe_info)
	
	logger.info(f"Iframe analysis complete: {iframe_content['iframes_accessible']}/{iframe_content['iframes_found']} iframes accessible")
	return iframe_content


def collect_comprehensive_with_iframes(driver: WebDriver) -> Dict[str, Any]:
	"""Collect comprehensive content from main document and all iframes."""
	comprehensive_data = {
		'main_document': {},
		'iframes': [],
		'summary': {
			'total_iframes': 0,
			'accessible_iframes': 0,
			'total_elements': 0
		}
	}
	
	# Collect from main document
	logger.info("Collecting from main document")
	comprehensive_data['main_document'] = {
		'title': page_title(driver),
		'headings': heading_texts(driver),
		'buttons': button_texts(driver),
		'links': links_map(driver),
		'forms': collect_form_summary(driver),
		'tables': collect_table_preview(driver),
		'meta': collect_meta(driver),
		'body_text': body_text_snapshot(driver, max_len=2000)
	}
	
	# Collect from all iframes
	iframe_content = collect_all_iframe_content(driver)
	comprehensive_data['iframes'] = iframe_content['iframe_details']
	comprehensive_data['summary'] = {
		'total_iframes': iframe_content['iframes_found'],
		'accessible_iframes': iframe_content['iframes_accessible'],
		'total_elements': iframe_content['total_elements_collected']
	}
	
	logger.info(f"Comprehensive collection complete: {comprehensive_data['summary']['total_elements']} total elements from {comprehensive_data['summary']['accessible_iframes']} iframes")
	return comprehensive_data
