from pathlib import Path

from urllib.parse import urljoin
from urllib.error import HTTPError
import uuid

import requests
from hdxms_datasets.loader import BACKEND, read_csv
from hdxms_datasets.models import HDXDataSet, extract_values_by_types
import shutil
import narwhals as nw

from hdxms_datasets.utils import records_to_dict
from hdxms_datasets.verification import verify_dataset


CATALOG_FILE = "datasets_catalog.csv"
DATABASE_URL = "https://raw.githubusercontent.com/Jhsmit/HDXMS-database/master/datasets/"
KNOWN_HDX_IDS = set[str]()


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


def mint_new_dataset_id(current_ids: set[str] = KNOWN_HDX_IDS) -> str:
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


def populate_known_ids(database_dir: Path, append=True) -> None:
    """
    Populate the KNOWN_HDX_IDS set with existing dataset IDs from the database directory.
    """
    global KNOWN_HDX_IDS
    if append:
        KNOWN_HDX_IDS.update(list_datasets(database_dir))
    else:
        KNOWN_HDX_IDS = set(list_datasets(database_dir))


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
        df.write_csv(database_dir / "datasets_catalog.csv")

    return df


def find_file_hash_matches(dataset: HDXDataSet, database_dir: Path) -> list[str]:
    """
    Check if a new dataset matches an existing dataset in the database directory.
    """
    try:
        catalog = nw.read_csv(str(database_dir / "datasets_catalog.csv"), backend=BACKEND)
    except FileNotFoundError:
        return []

    assert dataset.file_hash is not None, "Dataset must have a file hash."
    matching_datasets = catalog.filter(nw.col("file_hash") == dataset.file_hash[:16])

    return matching_datasets["id"].to_list()


def submit_dataset(
    dataset: HDXDataSet,
    database_dir: Path,
    allow_mint_new_id: bool = False,
    check_existing: bool = True,
    verify: bool = True,
) -> tuple[bool, str]:
    """
    Submit a dataset to a local HDX-MS database.

    Args:
        dataset: The HDXDataSet to submit.
        database_dir: The directory where the dataset will be stored.
        allow_mint_new_id: If True, allows minting a new dataset ID if it is already present in the database.
        check_existing: If True, checks if the dataset already exists in the database.
        verify: If True, verifies the dataset before submission.

    Returns:
        A tuple (success: bool, message: str):
        - success: True if the dataset was successfully submitted, False otherwise.
        - message: A message indicating the result of the submission.

    """

    dataset_copy = dataset.model_copy(deep=True)

    if verify:
        verify_dataset(dataset_copy)

    if not database_dir.is_absolute():
        raise ValueError("Database directory must be an absolute path.")

    # check if the uniprot ID is already there,
    # although there could be multiple states with the same uniprot ID
    # this is a quick check to avoid duplicates
    if check_existing:
        matches = find_file_hash_matches(dataset_copy, database_dir)
        if matches:
            if len(matches) == 1:
                msg = f"Dataset matches an existing dataset in the database: {matches[0]}"
            else:
                msg = f"Dataset matches existing datasets in the database: {', '.join(matches)}"
            return False, msg

    # mint a new ID if not provided
    existing_ids = set(list_datasets(database_dir))
    if dataset_copy.hdx_id in existing_ids:
        if allow_mint_new_id:
            dataset_id = mint_new_dataset_id(existing_ids)
            dataset_copy.hdx_id = dataset_id
        else:
            return False, f"Dataset ID {dataset_copy.hdx_id} already exists in the database."

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
    export_dataset(dataset_copy, tgt_dir)

    # update the catalogue
    # TODO: update instead of regenerate
    # TODO: lockfile? https://github.com/harlowja/fasteners
    generate_datasets_catalog(database_dir, save_csv=True)

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


class RemoteDataBase(DataBase):
    """
    A database for HDX-MS datasets, with the ability to fetch datasets from a remote repository.

    Args:
        database_dir: Directory to store downloaded datasets.
        remote_url: URL of the remote repository (default: DATABASE_URL).
    """

    def __init__(
        self,
        database_dir: Path | str,
        remote_url: str = DATABASE_URL,
    ):
        super().__init__(database_dir)
        self.remote_url = remote_url

        index_url = urljoin(DATABASE_URL, CATALOG_FILE)
        response = requests.get(index_url)

        # TODO keep catalogs on a per-url basis in a singleton
        if response.ok:
            df = read_csv(response.content)
            self.datasets_catalog = df
        else:
            raise HTTPError(
                index_url,
                response.status_code,
                "Error fetching dataset index",
                response.headers,  # type: ignore
                None,
            )

    @property
    def remote_datasets(self) -> list[str]:
        """List of available datasets in the remote repository"""
        return self.datasets_catalog["id"].to_list()

    @property
    def local_datasets(self) -> list[str]:
        """List of available datasets in the local database directory"""
        return self.datasets

    def fetch_dataset(self, data_id: str) -> tuple[bool, str]:
        """
        Download a dataset from the online repository to `database_dir`

        Args:
            data_id: The ID of the dataset to download.

        Returns:
            A tuple (success: bool, message: str):
            - success: True if the dataset was successfully downloaded, False otherwise.
            - message: A message indicating the result of the download.
        """

        if data_id not in self.remote_datasets:
            return False, f"Dataset ID {data_id!r} not found in remote database."

        json_url = urljoin(DATABASE_URL, data_id + "/dataset.json")
        response = requests.get(json_url)

        # confirm if the json is according to spec
        try:
            dataset = HDXDataSet.model_validate_json(
                response.content,
            )
        except Exception as e:
            return False, f"Error validating dataset JSON: {e}"

        # create a list of all Path objects in the dataset plus the dataset.json file
        data_files = list(set(extract_values_by_types(dataset, Path))) + [Path("dataset.json")]

        # create the target directory to store the dataset
        output_pth = self.database_dir / data_id
        if output_pth.exists():
            return False, "Dataset already exists in the local database."
        else:
            output_pth.mkdir()

        for data_file in data_files:
            data_url = urljoin(DATABASE_URL, data_id + "/" + data_file.as_posix())

            response = requests.get(data_url)
            if response.ok:
                # write the file to disk
                fpath = output_pth / Path(data_file)
                fpath.parent.mkdir(parents=True, exist_ok=True)
                fpath.write_bytes(response.content)
            else:
                shutil.rmtree(output_pth)  # clean up partial download
                return False, f"Failed to download {data_file}: {response.status_code}"

        return True, ""
