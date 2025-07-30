from __future__ import annotations

import shutil
import urllib.error
import urllib.parse
from pathlib import Path
from typing import Union

import requests
import yaml

from hdxms_datasets.backend import BACKEND
from hdxms_datasets.datasets import DataSet
import narwhals as nw

DATABASE_URL = "https://raw.githubusercontent.com/Jhsmit/HDX-MS-datasets/master/datasets/"


class DataVault:
    def __init__(self, cache_dir: Union[Path, str]):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True, parents=True)

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

    def clear_cache(self) -> None:
        for dir in self.cache_dir.iterdir():
            shutil.rmtree(dir)

    def get_metadata(self, data_id: str) -> dict:
        return yaml.safe_load((self.cache_dir / data_id / "metadata.yaml").read_text())

    def load_dataset(self, data_id: str) -> DataSet:
        hdx_spec = yaml.safe_load((self.cache_dir / data_id / "hdx_spec.yaml").read_text())
        dataset_metadata = self.get_metadata(data_id)

        return DataSet.from_spec(
            hdx_spec=hdx_spec,
            data_dir=self.cache_dir / data_id,
            data_id=data_id,
            metadata=dataset_metadata,
        )


class RemoteDataVault(DataVault):
    """
    A vault for HDX-MS datasets, with the ability to fetch datasets from a remote repository.

    Args:
        cache_dir: Directory to store downloaded datasets.
        remote_url: URL of the remote repository (default: DATABASE_URL).
    """

    def __init__(self, cache_dir: Union[Path, str], remote_url: str = DATABASE_URL):
        super().__init__(cache_dir)
        self.remote_url = remote_url

    def get_index(self) -> nw.DataFrame:
        """Retrieves the index of available datasets

        on success, returns the index dataframe and
        stores as `remote_index` attribute.

        """

        url = urllib.parse.urljoin(self.remote_url, "index.csv")
        response = requests.get(url)

        if response.ok:
            (self.cache_dir / "index.csv").write_bytes(response.content)
            return nw.read_csv(str(self.cache_dir / "index.csv"), backend=BACKEND)
        else:
            raise urllib.error.HTTPError(
                url,
                response.status_code,
                "Error downloading database index",
                response.headers,  # type: ignore
                None,
            )

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
        hdx_spec = None
        for f in files + optional_files:
            url = urllib.parse.urljoin(dataset_url, f)
            response = requests.get(url)

            if response.ok:
                (output_pth / f).write_bytes(response.content)

            elif f in files:
                raise urllib.error.HTTPError(
                    url,
                    response.status_code,
                    f"Error for file {f!r}",
                    response.headers,  # type: ignore
                    None,
                )

            if f == "hdx_spec.yaml":
                hdx_spec = yaml.safe_load(response.text)

        if hdx_spec is None:
            raise ValueError(f"Could not find HDX spec for data_id {data_id!r}")

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
                    response.headers,  # type: ignore
                    None,
                )

        return True
