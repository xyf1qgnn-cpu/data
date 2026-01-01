"""
Pydantic models for CFST data extraction (Workflow 2.0)
Based on requirements spec: 06-requirements-spec.md
"""

from pydantic import BaseModel, Field
from typing import Optional


class SpecimenData(BaseModel):
    """CFST specimen data model with source evidence support"""

    # Existing 15 fields from COL_MAPPING (Workflow 1.0)
    ref_no: str = Field(default="", description="Reference number (auto-filled with filename)")
    fc_value: float = Field(description="Concrete compressive strength value (MPa)")
    fc_type: str = Field(description="Concrete type description (e.g., 'Cube 150', 'Cylinder 150x300')")
    specimen_label: str = Field(description="Unique ID/Label of the specimen")
    fy: float = Field(description="Yield strength of steel (MPa)")
    fcy150: str = Field(default="", description="Always empty string")
    r_ratio: float = Field(default=0.0, description="Recycled aggregate ratio (%)")
    b: float = Field(description="Width/Diameter/Major axis (mm)")
    h: float = Field(description="Depth/Diameter/Minor axis (mm)")
    t: float = Field(description="Thickness of the steel tube (mm)")
    r0: float = Field(description="External corner/radius (mm)")
    L: float = Field(description="Length of the specimen (mm)")
    e1: float = Field(default=0.0, description="Eccentricity 1 (mm)")
    e2: float = Field(default=0.0, description="Eccentricity 2 (mm)")
    n_exp: float = Field(description="Experimental ultimate bearing capacity (kN)")

    # New field for Workflow 2.0
    source_evidence: str = Field(description="Text evidence from source document supporting each value")


class ExtractionResult(BaseModel):
    """Complete extraction result with validation status"""
    is_valid: bool = Field(default=True, description="Whether the document contains valid CFST data")
    reason: str = Field(default="Valid CFST experimental data", description="Reason for validity status")
    Group_A: list[SpecimenData] = Field(default_factory=list, description="Square/Rectangular specimens")
    Group_B: list[SpecimenData] = Field(default_factory=list, description="Circular specimens")
    Group_C: list[SpecimenData] = Field(default_factory=list, description="Round-ended/Elliptical specimens")