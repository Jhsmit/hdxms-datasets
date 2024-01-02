from __future__ import annotations

import shutil
import urllib.error
import urllib.parse
from functools import cached_property
from pathlib import Path
from typing import Optional, Union

import requests
import yaml

from hdxms_datasets.datasets import HDXDataSet


DATABASE_URL = "https://raw.githubusercontent.com/Jhsmit/HDX-MS-datasets/master/datasets/"


class DataVault(object):
    def __init__(
        self,
        cache_dir: Union[Path, str],
        remote_url: str = DATABASE_URL,
    ):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True, parents=True)

        self.remote_url = remote_url

    def filter(self, *spec: dict):
        # filters list of available datasets
        raise NotImplementedError("Not yet implemented")

    @cached_property
    def remote_index(self) -> list[str]:
        """List of available datasets in the remote database"""

        url = urllib.parse.urljoin(self.remote_url, "index.txt")
        response = requests.get(url)
        if response.ok:
            index = response.text.split("\n")[1:]
            return index
        else:
            return []

    @property
    def datasets(self) -> list[str]:
        """List of available datasets in the cache dir"""
        return [d.stem for d in self.cache_dir.iterdir() if self.is_dataset(d)]

    @staticmethod
    def is_dataset(path: Path) -> bool:
        """
        Checks if the supplied path is a HDX-MS dataset.
        """

        return (path / "hdx_spec.yaml").exists()

    async def fetch_datasets(self, n: Optional[str] = None, data_ids: Optional[list[str]] = None):
        """
        Asynchronously download multiple datasets
        """
        raise NotImplementedError("Not yet implemented")

        if n is None and data_ids is None:
            n = 10

        if data_ids:
            # Download specified datasets to cache_dir
            ...

        elif n:
            # Download n new datasets to cache_dir
            ...

    def fetch_dataset(self, data_id: str) -> bool:
        """
        Download a dataset from the online repository to the cache dir

        Args:
            data_id: The ID of the dataset to download.

        Returns:
            `True` if the dataset was downloaded successfully, `False`  otherwise.
        """

        output_pth = self.cache_dir / data_id
        if output_pth.exists():
            return False
        else:
            output_pth.mkdir()

        dataset_url = urllib.parse.urljoin(self.remote_url, data_id + "/")

        files = ["hdx_spec.yaml", "metadata.yaml"]
        optional_files = ["CITATION.cff"]
        for f in files + optional_files:
            url = urllib.parse.urljoin(dataset_url, f)
            response = requests.get(url)

            if response.ok:
                (output_pth / f).write_bytes(response.content)

            elif f in files:
                raise urllib.error.HTTPError(
                    url, response.status_code, f"Error for file {f!r}", response.headers, None
                )

            if f == "hdx_spec.yaml":
                hdx_spec = yaml.safe_load(response.text)

        data_pth = output_pth / "data"
        data_pth.mkdir()

        for file_spec in hdx_spec["data_files"].values():
            filename = file_spec["filename"]
            f_url = urllib.parse.urljoin(dataset_url, filename)
            response = requests.get(f_url)

            if response.ok:
                (output_pth / filename).write_bytes(response.content)
            else:
                raise urllib.error.HTTPError(
                    f_url,
                    response.status_code,
                    f"Error for data file {filename!r}",
                    response.headers,
                    None,
                )

        return True

    def clear_cache(self) -> None:
        for dir in self.cache_dir.iterdir():
            shutil.rmtree(dir)

    def load_dataset(self, data_id: str) -> HDXDataSet:
        hdx_spec = yaml.safe_load((self.cache_dir / data_id / "hdx_spec.yaml").read_text())
        dataset_metadata = yaml.safe_load((self.cache_dir / data_id / "metadata.yaml").read_text())

        return HDXDataSet.from_spec(
            hdx_spec=hdx_spec,
            data_dir=self.cache_dir / data_id,
            data_id=data_id,
            metadata=dataset_metadata,
        )
