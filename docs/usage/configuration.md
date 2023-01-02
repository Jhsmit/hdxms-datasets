# Configuration

Default values for HDXMS Datasets configuration are stored as a .yaml file in `~/.hdxms_datasets/config.yaml`. 
The values there can be modified to update default settings.

The default configuration is as follows:

```yaml
database_dir: $home/.hdxms_datasets/datasets
database_url: https://raw.githubusercontent.com/Jhsmit/HDX-MS-datasets/master/datasets/
time_unit: s

dynamx:
  time_unit: min

```

Here `time_unit` defines the time unit in returned datasets. The `time_unit` in the `dynamx` section sets the time unit 
of the source datasets in the DynamX format.

Configuration settings can also be changed from within python:

```python
from hdxms_datasets import cfg

cfg.time_unit = 'min'

```

This will change the time unit to minutes for all datasets loaded from then on.