from pathlib import Path

import urllib
import uuid

import requests
from hdxms_datasets.loader import BACKEND
from hdxms_datasets.models import HDXDataSet
import shutil
import narwhals as nw
import hashlib
import pydantic_core

from hdxms_datasets.utils import records_to_dict
from hdxms_datasets.verification import verify_dataset


def load_dataset(pth: Path) -> HDXDataSet:
    """
    Load a dataset from a JSON file or directory.
    """

    if pth.is_file():
        dataset_root = pth.parent
        json_pth = pth
    else:
        dataset_root = pth
        json_pth = dataset_root / "dataset.json"
    dataset = HDXDataSet.model_validate_json(
        json_pth.read_text(), context={"dataset_root": dataset_root}
    )
    return dataset


def mint_new_dataset_id(current_ids: set[str]) -> str:
    """
    Mint a new dataset ID that does not conflict with existing IDs in the database directory.
    """
    while True:
        new_id = f"HDX_{uuid.uuid4().hex[:8].upper()}"
        if new_id not in current_ids:
            return new_id


def valid_id(dataset_id: str) -> bool:
    """
    Check if the dataset ID is valid.
    A valid ID starts with 'HDX_' followed by 8 uppercase alphanumeric characters.
    """
    return (
        bool(dataset_id)
        and dataset_id.startswith("HDX_")
        and len(dataset_id) == 12
        and dataset_id[4:].isalnum()
    )


def list_datasets(database_dir: Path) -> list[str]:
    """
    List all valid dataset IDs in the database directory.
    """

    return [p.stem for p in database_dir.iterdir() if valid_id(p.stem)]


def export_dataset(dataset: HDXDataSet, tgt_dir: Path) -> None:
    """
    Store a dataset to a target directory.
    This will copy the data files to a 'data' subdirectory and write the dataset JSON.
    """

    # copy the dataset to update the paths
    ds_copy = dataset.model_copy(deep=True)

    data_dir = tgt_dir / "data"
    data_dir.mkdir(exist_ok=True, parents=True)

    # copy the sequence file
    shutil.copy(ds_copy.structure.data_file, data_dir / ds_copy.structure.data_file.name)
    # the the path to the copied file relative path
    ds_copy.structure.data_file = Path("data") / ds_copy.structure.data_file.name

    # repeat for the peptides
    for state in ds_copy.states:
        for peptides in state.peptides:
            shutil.copy(peptides.data_file, data_dir / peptides.data_file.name)
            # update the path to the copied file relative path
            peptides.data_file = Path("data") / peptides.data_file.name

    # write the dataset to a JSON file
    s = ds_copy.model_dump_json(indent=2, exclude_none=True)
    Path(tgt_dir / "dataset.json").write_text(s)


def generate_datasets_catalog(database_dir: Path, save_csv: bool = True) -> nw.DataFrame:
    """
    Generate an overview DataFrame of all datasets in the database directory.
    """
    records = []
    for ds_id in list_datasets(database_dir):
        ds_path = database_dir / ds_id / "dataset.json"
        if ds_path.exists():
            dataset = HDXDataSet.model_validate_json(
                ds_path.read_text(), context={"dataset_root": database_dir / ds_id}
            )
            records.append(
                {
                    "id": ds_id,
                    "description": dataset.description,
                    "author": dataset.metadata.authors[0].last_name,
                    "doi": dataset.metadata.publication.doi
                    if dataset.metadata.publication
                    else None,
                    "created_date": dataset.metadata.created_date,
                    "uniprot_accession_number": dataset.protein_identifiers.uniprot_accession_number,
                    "file_hash": dataset.file_hash,
                }
            )

    df = nw.from_dict(records_to_dict(records), backend=BACKEND)
    if save_csv:
        df.write_csv(database_dir / "datasets_catalogue.csv")

    return df


def find_file_hash_matches(dataset: HDXDataSet, database_dir: Path) -> list[str]:
    """
    Check if a new dataset matches an existing dataset in the database directory.
    """
    try:
        catalog = nw.read_csv(str(database_dir / "datasets_catalogue.csv"), backend=BACKEND)
    except FileNotFoundError:
        return []

    assert dataset.file_hash is not None, "Dataset must have a file hash."
    matching_datasets = catalog.filter(nw.col("file_hash") == dataset.file_hash[:16])

    return matching_datasets["id"].to_list()


def submit_dataset(
    dataset: HDXDataSet,
    database_dir: Path,
    dataset_id: str | None = None,
    check_existing: bool = True,
    verify: bool = True,
) -> tuple[bool, str]:
    """
    Submit a dataset to a local HDX-MS database.

    Args:
        dataset: The HDXDataSet to submit.
        database_dir: The directory where the dataset will be stored.
        dataset_id: Optional ID for the dataset. If not provided, a new ID will be minted.
        check_existing: If True, checks if the dataset already exists in the database.
        verify: If True, verifies the dataset before submission.

    Returns:
        A tuple (success: bool, message: str):
        - success: True if the dataset was successfully submitted, False otherwise.
        - message: A message indicating the result of the submission.

    """

    if verify:
        verify_dataset(dataset)

    if not database_dir.is_absolute():
        raise ValueError("Database directory must be an absolute path.")

    # check if the uniprot ID is already there,
    # although there could be multiple states with the same uniprot ID
    # this is a quick check to avoid duplicates
    if check_existing:
        matches = find_file_hash_matches(dataset, database_dir)
        if matches:
            if len(matches) == 1:
                msg = f"Dataset matches an existing dataset in the database: {matches[0]}"
            else:
                msg = f"Dataset matches existing datasets in the database: {', '.join(matches)}"
            return False, msg

    # mint a new ID if not provided
    existing_ids = set(list_datasets(database_dir))
    if dataset_id is None:
        dataset_id = mint_new_dataset_id(existing_ids)
    else:
        if dataset_id in existing_ids:
            return False, f"Dataset ID {dataset_id} already exists in the database."

    if not valid_id(dataset_id):
        raise ValueError(
            f"Invalid dataset ID: {dataset_id}. "
            "A valid ID starts with 'HDX_' followed by 8 uppercase alphanumeric characters."
        )

    # create the target directory
    tgt_dir = database_dir / dataset_id
    export_dataset(dataset, tgt_dir)

    # update the catalogue
    # TODO: update instead of regenerate
    catalog = generate_datasets_catalog(database_dir, save_csv=True)

    return True, dataset_id


class DataBase:
    def __init__(self, database_dir: Path | str):
        self.database_dir = Path(database_dir)
        self.database_dir.mkdir(exist_ok=True, parents=True)

    @property
    def datasets(self) -> list[str]:
        """List of available datasets in the cache dir"""
        return [d.stem for d in self.database_dir.iterdir() if self.is_dataset(d)]

    @staticmethod
    def is_dataset(path: Path) -> bool:
        """
        Checks if the supplied path is a HDX-MS dataset.
        """

        return (path / "dataset.json").exists()

    def clear_cache(self) -> None:
        for dir in self.database_dir.iterdir():
            shutil.rmtree(dir)

    def load_dataset(self, dataset_id: str) -> HDXDataSet:
        dataset_root = self.database_dir / dataset_id
        dataset = HDXDataSet.model_validate_json(
            Path(dataset_root, "dataset.json").read_text(),
            context={"dataset_root": dataset_root},
        )
        return dataset


DATABASE_URL = "https://raw.githubusercontent.com/Jhsmit/HDX-MS-datasets/master/datasets/"


class RemoteDataBase(DataBase):
    """
    A database for HDX-MS datasets, with the ability to fetch datasets from a remote repository.

    Args:
        cache_dir: Directory to store downloaded datasets.
        remote_url: URL of the remote repository (default: DATABASE_URL).
    """

    def __init__(self, database_dir: Path | str, remote_url: str = DATABASE_URL):
        super().__init__(database_dir)
        self.remote_url = remote_url

    def get_index(self) -> nw.DataFrame:
        """Retrieves the index of available datasets

        on success, returns the index dataframe and
        stores as `remote_index` attribute.

        """
        raise NotImplementedError()

    def fetch_dataset(self, data_id: str) -> bool:
        """
        Download a dataset from the online repository to the cache dir

        Args:
            data_id: The ID of the dataset to download.

        Returns:
            `True` if the dataset was downloaded successfully, `False`  otherwise.
        """

        raise NotImplementedError()
        output_pth = self.cache_dir / data_id
        if output_pth.exists():
            return False
        else:
            output_pth.mkdir()

        dataset_url = urllib.parse.urljoin(self.remote_url, data_id + "/")

        files = ["hdx_spec.yaml", "metadata.yaml"]
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
