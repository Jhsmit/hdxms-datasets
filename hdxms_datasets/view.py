from __future__ import annotations
import itertools
from typing import Optional
from hdxms_datasets.utils import peptide_redundancy
from hdxms_datasets.models import Structure, StructureMapping, ValueType
import narwhals as nw

from hdxms_datasets.utils import contiguous_peptides, non_overlapping_peptides


class StructureView:
    def __init__(
        self,
        structure: Structure,
        mapping: StructureMapping = StructureMapping(),
        hide_water=True,
        **kwargs: dict,
    ):
        """
        Initialize the PDBeMolstar visualization namespace.
        Can uses a `StructureMapping` which relates peptides to the structure

        Args:
            structure: The structure to visualize.
            mapping: Optional structure mapping information.
            **kwargs: Additional keyword arguments for customization.
        """
        self.structure = structure
        self.mapping = mapping

        from ipymolstar import PDBeMolstar

        self.view = PDBeMolstar(
            custom_data=self.structure.pdbemolstar_custom_data(),
            hide_water=hide_water,
            **kwargs,
        )

    def show(self):
        return self.view

    def highlight(self, resi: int) -> StructureView:
        """
        Highlights a residue in the structure.

        Args:
            resi: Residue number to highlight.

        Returns:
            The updated StructureView object.
        """
        param = self.get_query_param(resi)
        data = self._augment_chain([param])
        self.view.highlight = {"data": data}

        return self

    def color_peptide(
        self,
        start: int,
        end: int,
        color: str = "red",
        non_selected_color: str = "lightgray",
    ) -> StructureView:
        """
        Color a peptide by start and end residue numbers.

        Args:
            start: Start residue number.
            end: End residue number.
            color: Color for the peptide.
            non_selected_color: Color for non-selected regions.

        Returns:
            The updated StructureView object.
        """
        kwargs = {"color": color}
        param = self.get_query_param_range(start, end, **kwargs)
        data = self._augment_chain([param])

        color_data = {
            "data": data,
            "nonSelectedColor": non_selected_color,
        }

        self.view.color_data = color_data
        self.view.tooltips = None

        return self

    def peptide_coverage(
        self,
        peptides: nw.DataFrame,
        color: str = "darkgreen",
        non_selected_color: str = "lightgray",
    ):
        """
        Plots peptide coverage on the structure.

        Args:
            peptides: Peptides object or DataFrame containing peptide data.
            color: Color for the covered regions.
            non_selected_color: Color for non-covered regions.

        Returns:
            The updated StructureView object.
        """
        intervals = contiguous_peptides(peptides)

        data = [self.get_query_param_range(start, end, color=color) for start, end in intervals]
        color_data = {
            "data": self._augment_chain(data),
            "nonSelectedColor": non_selected_color,
        }

        self.view.color_data = color_data
        self.view.tooltips = None
        return self

    def non_overlapping_peptides(
        self,
        peptides: nw.DataFrame,
        colors: list[str] | None = None,
        non_selected_color: str = "lightgray",
    ):
        """Selects a set of non-overlapping peptides to display on the structure. Starts with the first
        peptide and successively adds peptides that do not overlap with already selected peptides.

        Args:
            peptides: Peptides object or DataFrame containing peptide data.
            colors: List of colors to cycle through for different peptides.
            non_selected_color: Color for non-covered regions.

        Returns:
            The updated StructureView object.

        """

        intervals = non_overlapping_peptides(peptides)

        colors = (
            colors
            if colors is not None
            else ["#1B9E77", "#D95F02", "#7570B3", "#E7298A", "#66A61E", "#E6AB02"]
        )

        cdata = []
        tdata = []
        for (start, end), color in zip(intervals, itertools.cycle(colors)):
            cdata.append(self.get_query_param_range(start, end, color=color))
            df_f = peptides.filter((nw.col("start") == start) & (nw.col("end") == end)).to_native()
            sequence = df_f["sequence"].unique().first()
            tdata.append(self.get_query_param_range(start, end, tooltip=f"Peptide: {sequence}"))

        color_data = {
            "data": self._augment_chain(cdata),
            "nonSelectedColor": non_selected_color,
        }

        self.view.color_data = color_data
        self.view.tooltips = {"data": self._augment_chain(tdata)}
        return self

    def peptide_redundancy(
        self,
        peptides: nw.DataFrame,
        colors: list[str] | None = None,
        clip: Optional[int] = None,
        non_selected_color: str = "lightgray",
    ):
        """Colors residues by peptide redundancy.

        Args:
            peptides: Peptides DataFrame containing peptide data.
            colors: List of colors to use for different redundancy levels.
            clip: Optional maximum redundancy value for clipping.
            non_selected_color: Color for non-covered regions.

        Returns:
            The updated StructureView object.

        """
        r_number, redundancy = peptide_redundancy(peptides)

        colors = (
            colors
            if colors is not None
            else ["#C6DBEF", "#9ECAE1", "#6BAED6", "#4292C6", "#2171B5", "#08519C", "#08306B"]
        )

        if clip:
            vals = ((redundancy.clip(None, clip) / clip) * (len(colors) - 1)).astype(int)
        else:
            vals = ((redundancy / redundancy.max()) * (len(colors) - 1)).astype(int)

        data = []
        tooltips = []
        for rn, rv, rv_clip in zip(r_number, redundancy, vals):
            tooltips.append(self.get_query_param(int(rn), tooltip=f"Redundancy: {rv} peptides"))

            if rv == 0:
                continue

            color_elem = self.get_query_param(int(rn), color=colors[rv_clip])
            data.append(color_elem)

        color_data = {
            "data": self._augment_chain(data),
            "nonSelectedColor": non_selected_color,
        }

        self.view.color_data = color_data
        self.view.tooltips = {"data": self._augment_chain(tooltips)}
        return self

    def set_mapping(self, mapping: StructureMapping):
        self.mapping = mapping
        return self

    def get_query_param(self, resi: int, **kwargs):
        resi = resi + self.mapping.residue_offset

        # TODO entity support
        c_dict = {
            self.residue_name: int(resi),
            **kwargs,
        }

        return c_dict

    def get_query_param_range(self, start: int, end: int, **kwargs):
        start = start + self.mapping.residue_offset
        end = end + self.mapping.residue_offset

        # TODO entity support
        c_dict = {
            "start_" + self.residue_name: int(start),
            "end_" + self.residue_name: int(end),
            **kwargs,
        }

        return c_dict

    @property
    def residue_name(self) -> str:
        """
        Returns the residue name based on whether auth residue numbers are used.
        """
        return "auth_residue_number" if self.mapping.auth_residue_numbers else "residue_number"

    @property
    def chain_name(self) -> str:
        """
        Returns the chain name based on whether auth chain labels are used.

        Note that 'struct_asym_id' used in PDBeMolstar is equivalent to
        'label_asym_id' in mmCIF.

        """
        return "auth_asym_id" if self.mapping.auth_chain_labels else "struct_asym_id"

    def _augment_chain(
        self,
        data: list[dict[str, ValueType]],
    ) -> list[dict[str, ValueType]]:
        """Augment a list of data with chain information"""
        if self.mapping.chain:
            aug_data = []
            for elem, chain in itertools.product(data, self.mapping.chain):
                aug_data.append(elem | {self.chain_name: chain})
        else:
            aug_data = data

        return aug_data

    def _repr_mimebundle_(self, include=None, exclude=None):
        return self.show()._repr_mimebundle_(include=include, exclude=exclude)
