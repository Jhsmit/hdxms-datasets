from __future__ import annotations

import dataclasses
import uuid
import warnings
from collections import UserList
from dataclasses import dataclass, field, make_dataclass, replace
from pathlib import Path
from typing import (
    Callable,
    ContextManager,
    Generic,
    Optional,
    Tuple,
    TypedDict,
    TypeVar,
)

import numpy as np
import polars as pl
import solara
from solara.toestand import merge_state

from hdxms_datasets.web.models import PeptideInfo


T = TypeVar("T")
R = TypeVar("R")
K = TypeVar("K")
V = TypeVar("V")


class _NoDefault:
    """Sentinel class to distinguish between no default and None as default"""

    pass


NO_DEFAULT = _NoDefault()
DEFAULT_TIMEOUT = 5000  # snackbar timeout default


def reactive_factory(factory: Callable[[], T]) -> solara.Reactive[T]:
    return solara.reactive(factory())


@dataclass
class SnackbarMessage:
    message: str = ""
    color: str = "primary"
    timeout: int = 3000
    btn_color: str = "text-primary-color"

    show: bool = False


class Store(Generic[T]):
    def __init__(self, initial_value: T):
        self._reactive = solara.reactive(initial_value)

    @property
    def value(self) -> T:
        return self._reactive.value

    def subscribe(self, listener: Callable[[T], None], scope: Optional[ContextManager] = None):
        return self._reactive.subscribe(listener, scope=scope)

    def subscribe_change(
        self, listener: Callable[[T, T], None], scope: Optional[ContextManager] = None
    ):
        return self._reactive.subscribe_change(listener, scope=scope)


class SnackbarStore(Store[SnackbarMessage]):
    def __init__(self, message: SnackbarMessage | None = None):
        super().__init__(message if message is not None else SnackbarMessage())

    def update(self, **kwargs):
        self._reactive.update(**kwargs)

    def set_message(self, msg: str, timeout: Optional[int] = DEFAULT_TIMEOUT, **kwargs):
        self._reactive.update(message=msg, timeout=timeout, show=True, **kwargs)

    def info(self, msg: str, timeout: Optional[int] = None):
        self.set_message(msg, color="primary", btn_color="text-primary-color", timeout=timeout)

    def secondary(self, msg: str, timeout: Optional[int] = None):
        self.set_message(msg, color="secondary", btn_color="text-secondary-color", timeout=timeout)

    def warning(self, msg: str, timeout: Optional[int] = None):
        self.set_message(msg, color="warning", btn_color="text-warning-color", timeout=timeout)

    def error(self, msg: str, timeout: Optional[int] = None):
        self.set_message(msg, color="error", btn_color="text-error-color", timeout=timeout)

    def success(self, msg: str, timeout: Optional[int] = None):
        self.set_message(msg, color="success", btn_color="text-success-color", timeout=timeout)


class ListStore(Store[list[T]]):
    """baseclass for reactive list"""

    def __init__(self, items: Optional[list[T]] = None):
        super().__init__(items if items is not None else [])

    def __len__(self):
        return len(self.value)

    def __getitem__(self, idx: int) -> T:
        return self.value[idx]

    def __iter__(self):
        return iter(self.value)

    def get_item(self, idx: int, default: R = NO_DEFAULT) -> T | R:
        try:
            return self._reactive.value[idx]
        except IndexError:
            if default is NO_DEFAULT:
                raise IndexError(f"Index {idx} is out of range")
            return default

    def set(self, items: list[T]) -> None:
        self._reactive.value = items

    def set_item(self, idx: int, item: T) -> None:
        new_items = self._reactive.value.copy()
        if idx == len(new_items):
            new_items.append(item)
        elif idx < len(new_items):
            new_items[idx] = item
        else:
            raise IndexError(f"Index {idx} is out of range")
        self._reactive.value = new_items

    def append(self, item: T) -> None:
        self._reactive.value = [*self._reactive.value, item]

    def extend(self, items: list[T]) -> None:
        new_value = self.value.copy()
        new_value.extend(items)
        self._reactive.value = new_value

    def insert(self, idx: int, item: T) -> None:
        new_value = self.value.copy()
        new_value.insert(idx, item)
        self._reactive.value = new_value

    def remove(self, item: T) -> None:
        self._reactive.value = [it for it in self.value if it != item]

    def pop(self, idx: int) -> T:
        item = self.value[idx]
        self._reactive.value = self.value[:idx] + self.value[idx + 1 :]
        return item

    def clear(self) -> None:
        self._reactive.value = []

    def index(self, item: T) -> int:
        return self.value.index(item)

    def update(self, idx: int, **kwargs):
        new_value = self.value.copy()
        updated_item = merge_state(new_value[idx], **kwargs)
        new_value[idx] = updated_item
        self._reactive.value = new_value

    def count(self, item: T) -> int:
        return self.value.count(item)

    def find_item(self, **kwargs) -> Optional[T]:
        """find item in list by attributes"""
        for item in self.value:
            if all(getattr(item, k) == v for k, v in kwargs.items()):
                return item
        return None

    def find_index(self, **kwargs) -> Optional[int]:
        """find item in list by attributes"""
        for idx, item in enumerate(self.value):
            if all(getattr(item, k) == v for k, v in kwargs.items()):
                return idx
        return None


class DictStore(Store[dict[K, V]]):
    # todo maybe require values to be a dict
    def __init__(self, values: Optional[dict] = None):
        super().__init__(values if values is not None else {})

    def set(self, items: dict[K, V]) -> None:
        self._reactive.value = items

    def set_item(self, key: K, value: V) -> None:
        self[key] = value

    def __len__(self) -> int:
        return len(self._reactive.value)  # todo self.value

    def __getitem__(self, key):
        return self._reactive.value[key]

    def __setitem__(self, key, value):
        new_value = self._reactive.value.copy()
        new_value[key] = value
        self._reactive.value = new_value

    def items(self):
        return self._reactive.value.items()

    def keys(self):
        return self._reactive.value.keys()

    def values(self):
        return self._reactive.value.values()

    def pop(self, key) -> V:
        new_value = self._reactive.value.copy()
        item = new_value.pop(key)
        self.set(new_value)
        return item

    def popitem(self) -> tuple[K, V]:
        new_value = self._reactive.value.copy()
        item = new_value.popitem()
        self.set(new_value)
        return item


# move to state file
snackbar = SnackbarStore()


class PeptideStore(DictStore[str, ListStore[PeptideInfo]]):
    def add_peptide(self, state: str | None, peptide_type: str):  # TODO type ppetide_type
        if state is None:
            snackbar.info("Select a state to add peptides")
            return

        current_peptide_types = [p.type for p in self[state].value]
        if peptide_type in current_peptide_types:
            snackbar.warning(f"Peptide type {peptide_type!r} already exists in state {state!r}")
            return

        new_peptide = PeptideInfo(type=peptide_type)
        self[state].append(new_peptide)

    def remove_peptide(self, state: str, peptide_idx: int):
        new_peptides = self.value[state]
        new_peptides.pop(peptide_idx)
        self.set_item(state, new_peptides)

    def add_state(self, state: str):
        if not state:
            snackbar.warning("State name cannot be empty")
            return

        if state in self.value:
            snackbar.warning(f"State {state!r} already exists")
            return
        self.set_item(state, ListStore[PeptideInfo]([]))
