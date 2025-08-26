from __future__ import annotations

from typing import Optional

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement


HIGHLIGHT_STYLE_ID = "__ui_compare_highlight_style__"
HIGHLIGHT_CLASS = "__ui_compare_highlight__"



def _apply_inline_highlight_js() -> str:
	return (
		"var el=arguments[0], dur=arguments[1], color=arguments[2];"
		"if(!el) return;"
		"try { el.scrollIntoView({behavior: 'instant', block: 'center', inline: 'center'}); } catch(e){}"
		"el.setAttribute('data-ui-prev-outline', el.style.outline || '');"
		"el.setAttribute('data-ui-prev-outlineOffset', el.style.outlineOffset || '');"
		"el.setAttribute('data-ui-prev-boxShadow', el.style.boxShadow || '');"
		"el.setAttribute('data-ui-prev-bg', el.style.backgroundColor || '');"
		"el.setAttribute('data-ui-prev-position', el.style.position || '');"
		"el.setAttribute('data-ui-prev-z', el.style.zIndex || '');"
		"el.style.outline = '4px solid ' + color; el.style.outlineOffset='2px';"
		"el.style.boxShadow = '0 0 0 4px rgba(255,255,0,0.6), 0 0 10px 4px ' + color;"
		"el.style.backgroundColor = 'rgba(255,255,0,0.12)';"
		"if (getComputedStyle(el).position === 'static') { el.style.position = 'relative'; }"
		"el.style.zIndex = '2147483647';"
		"if(dur>0){ setTimeout(function(){"
		"  el.style.outline = el.getAttribute('data-ui-prev-outline');"
		"  el.style.outlineOffset = el.getAttribute('data-ui-prev-outlineOffset');"
		"  el.style.boxShadow = el.getAttribute('data-ui-prev-boxShadow');"
		"  el.style.backgroundColor = el.getAttribute('data-ui-prev-bg');"
		"  el.style.position = el.getAttribute('data-ui-prev-position');"
		"  el.style.zIndex = el.getAttribute('data-ui-prev-z');"
		"}, dur); }"
	)


def highlight_selector(driver: WebDriver, selector: str, duration_ms: int = 400, color: str = "#ff00ff") -> None:
	if not selector:
		return
	# Inline styles to ensure visibility across component styles and frames
	js = (
		"var sel=arguments[0], dur=arguments[1], color=arguments[2];"
		"var apply=function(doc){"
		"  var nodes = Array.from(doc.querySelectorAll(sel));"
		"  nodes.forEach(function(n){"
		+ _apply_inline_highlight_js() +
		"    (n, dur, color);"
		"  });"
		"};"
		"apply(document);"
		"var iframes = Array.from(document.querySelectorAll('iframe'));"
		"iframes.forEach(function(fr){"
		"  try { if (fr.contentDocument) { apply(fr.contentDocument); } } catch(e){}"
		"});"
	)
	driver.execute_script(js, selector, int(duration_ms), color)


def highlight_element(driver: WebDriver, element: WebElement, duration_ms: int = 400, color: str = "#ff00ff") -> None:
	if element is None:
		return
	js = _apply_inline_highlight_js()
	driver.execute_script(js, element, int(duration_ms), color)
