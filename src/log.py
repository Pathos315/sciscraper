from __future__ import annotations

import json
import logging
import logging.config

from pathlib import Path


logger = logging.getLogger("sciscraper")

logging_configs_path = Path("logging_config.json")
logging_configs = logging_configs_path.resolve()
with open(logging_configs) as f_in:
    log_config = json.load(f_in)
    logging.config.dictConfig(log_config)
