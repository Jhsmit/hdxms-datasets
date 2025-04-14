"""
Run this script to copy the template directory to a create a new dataset
"""

from pathlib import Path
from hdxms_datasets import create_dataset


author_name = "Krishnamurthy"
human_readable_tag = "SecB"  # optional tag

data_id = create_dataset(Path().resolve() / "datasets", author_name, human_readable_tag)
