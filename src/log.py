from __future__ import annotations

import json
import logging
import logging.config

from pathlib import Path


logger = logging.getLogger("sciscraper")

logging_configs = Path("logging_config.json").resolve()
with open(logging_configs) as f_in:
    log_config = json.load(f_in)
    logging.config.dictConfig(log_config)
