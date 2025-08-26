import os
from typing import Any, Dict
import yaml


def load_settings(settings_path: str = "config/settings.yaml") -> Dict[str, Any]:
	path = os.path.abspath(settings_path)
	if not os.path.exists(path):
		raise FileNotFoundError(f"Settings file not found: {path}")
	with open(path, "r", encoding="utf-8") as f:
		data = yaml.safe_load(f) or {}

	# Normalize and expand paths
	for key in [
		"screenshot_dir",
	]:
		if key in data and isinstance(data[key], str):
			data[key] = os.path.abspath(os.path.expandvars(os.path.expanduser(data[key])))

	return data
