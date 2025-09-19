from __future__ import annotations
import itertools
from typing import Sequence
from hdxms_datasets.utils import peptide_redundancy
from hdxms_datasets.models import Peptides, Structure, ValueType
import narwhals as nw

from hdxms_datasets.utils import contiguous_peptides, non_overlapping_peptides


class StructureView:
    def __init__(self, structure: Structure, hide_water=True, **kwargs):
        """
        Initialize the PDBeMolstar visualization namespace.

        Args:
            structure: The structure to visualize.
            **kwargs: Additional keyword arguments for customization.
        """
        self.structure = structure

        from ipymolstar import PDBeMolstar

        self.view = PDBeMolstar(
            custom_data=self.structure.pdbemolstar_custom_data(),
            hide_water=hide_water,
            **kwargs,
        )

    @property
    def residue_name(self) -> str:
        """
        Returns the residue name based on whether auth residue numbers are used.
        """
        return "auth_residue_number" if self.structure.auth_residue_numbers else "residue_number"

    def rn(self, r: int) -> int:
        """Apply residue numbering offset"""
        return r + self.structure.residue_offset

    @property
    def chain_name(self) -> str:
        """
        Returns the chain name based on whether auth chain labels are used.
        """
        return "auth_asym_id" if self.structure.auth_chain_labels else "struct_asym_id"

    @staticmethod
    def resolve_peptides(peptides: Peptides | nw.DataFrame) -> nw.DataFrame:
        """
        Loads peptides as a DataFrame or returns the DataFrame.
        """
        if isinstance(peptides, Peptides):
            df = peptides.load()
        else:
            df = peptides

        return df

    @staticmethod
    def resolve_chain(peptides: Peptides | nw.DataFrame, chain: list[str] | None) -> list[str]:
        """
        Resolves the chain information from a Peptides object or a DataFrame.
        """
        if isinstance(chain, list):
            return chain
        elif isinstance(peptides, Peptides):
            return peptides.chain if peptides.chain else []
        else:
            return []

    def show(self) -> StructureView:
        return self.view

    def color_peptide(
        self,
        start: int,
        end: int,
        chain: list[str] | None = None,
        color: str = "red",
        non_selected_color: str = "lightgray",
    ) -> StructureView:
        c_dict = {
            "start_" + self.residue_name: self.rn(start),
            "end_" + self.residue_name: self.rn(end),
            "color": color,
        }

        data = self._augment_chain([c_dict], chain or [])

        color_data = {
            "data": data,
            "nonSelectedColor": non_selected_color,
        }

        self.view.color_data = color_data
        self.view.tooltips = None

        return self

    def peptide_coverage(
        self,
        peptides: Peptides | nw.DataFrame,
        color="darkgreen",
        chain: list[str] | None = None,
        non_selected_color: str = "lightgray",
    ) -> StructureView:
        """
        Plots peptide coverage on the structure.

        Args:
            peptides: Peptides object or DataFrame containing peptide data.
            color: Color for the covered regions.
            chain: List of chains to apply the coloring to.
            non_selected_color: Color for non-covered regions.
        """
        df = self.resolve_peptides(peptides)
        chain = self.resolve_chain(peptides, chain)
        intervals = contiguous_peptides(df)

        data = []
        for start, end in intervals:
            elem = {
                f"start_{self.residue_name}": self.rn(start),
                f"end_{self.residue_name}": self.rn(end),
                "color": color,
            }
            data.append(elem)

        color_data = {
            "data": self._augment_chain(data, chain),
            "nonSelectedColor": non_selected_color,
        }

        self.view.color_data = color_data
        self.view.tooltips = None
        return self

    def non_overlapping_peptides(
        self,
        peptides: Peptides | nw.DataFrame,
        colors: list[str] | None = None,
        chain: list[str] | None = None,
        non_selected_color: str = "lightgray",
    ) -> StructureView:
        """Selects a set of non-overlapping peptides to display on the structure. Starts with the first
        peptide and successively adds peptides that do not overlap with already selected peptides.

        Args:
            peptides: Peptides object or DataFrame containing peptide data.
            colors: List of colors to cycle through for different peptides.
            chain: List of chains to apply the coloring to.
            non_selected_color: Color for non-covered regions.

        Returns:
            StructureView: The updated StructureView object.

        """
        df = self.resolve_peptides(peptides)
        chain = self.resolve_chain(peptides, chain)

        intervals = non_overlapping_peptides(df)

        colors = (
            colors
            if colors is not None
            else ["#1B9E77", "#D95F02", "#7570B3", "#E7298A", "#66A61E", "#E6AB02"]
        )

        cdata = []
        tdata = []
        for (start, end), color in zip(intervals, itertools.cycle(colors)):
            cdata.append(
                {
                    f"start_{self.residue_name}": self.rn(start),
                    f"end_{self.residue_name}": self.rn(end),
                    "color": color,
                }
            )
            df_f = df.filter((nw.col("start") == start) & (nw.col("end") == end)).to_native()
            sequence = df_f["sequence"].unique().first()
            tdata.append(
                {
                    f"start_{self.residue_name}": self.rn(start),
                    f"end_{self.residue_name}": self.rn(end),
                    "tooltip": f"Peptide: {sequence}",
                }
            )

        color_data = {
            "data": self._augment_chain(cdata, chain),
            "nonSelectedColor": non_selected_color,
        }

        self.view.color_data = color_data
        self.view.tooltips = {"data": self._augment_chain(tdata, chain)}
        return self

    def peptide_redundancy(
        self,
        peptides: Peptides | nw.DataFrame,
        chain: list[str] | None = None,
        colors: list[str] | None = None,
        non_selected_color: str = "lightgray",
    ) -> StructureView:
        """Colors residues by peptide redundancy.

        Args:
            peptides: Peptides object or DataFrame containing peptide data.
            chain: List of chains to apply the coloring to.
            colors: List of colors to use for different redundancy levels.
            non_selected_color: Color for non-covered regions.

        """
        df = self.resolve_peptides(peptides)
        chain = self.resolve_chain(peptides, chain)

        r_number, redundancy = peptide_redundancy(df)

        colors = (
            colors
            if colors is not None
            else ["#C6DBEF", "#9ECAE1", "#6BAED6", "#4292C6", "#2171B5", "#08519C", "#08306B"]
        )
        color_lut = {i + 1: colors[i] for i in range(len(colors))}

        data = []
        tooltips = []
        for rn, rv in zip(r_number, redundancy.clip(0, len(colors) - 1)):
            tooltips.append(
                {
                    f"{self.residue_name}": self.rn(int(rn)),
                    "tooltip": f"Redundancy: {rv} peptides",
                }
            )

            if rv == 0:
                continue
            color_elem = {
                f"{self.residue_name}": self.rn(int(rn)),
                "color": color_lut[rv],
            }
            data.append(color_elem)

        color_data = {
            "data": self._augment_chain(data, chain),
            "nonSelectedColor": non_selected_color,
        }

        self.view.color_data = color_data
        self.view.tooltips = {"data": self._augment_chain(tooltips, chain)}
        return self

    def _augment_chain(
        self, data: list[dict[str, ValueType]], chains: Sequence[str]
    ) -> list[dict[str, ValueType]]:
        """Augment a list of data with chain information"""
        if chains:
            aug_data = []
            for elem, chain in itertools.product(data, chains):
                aug_data.append(elem | {self.chain_name: chain})
        else:
            aug_data = data

        return aug_data

    def _repr_mimebundle_(self, include=None, exclude=None):
        return self.show()._repr_mimebundle_(include=include, exclude=exclude)
