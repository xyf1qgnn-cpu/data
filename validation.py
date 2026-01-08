"""
Physical validation formulas for CFST data (Workflow 2.0)
Based on requirements spec: 06-requirements-spec.md
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional


def calculate_inner_radius(r0: float, h: float, t: float) -> float:
    """
    Calculate inner radius r1 for round-ended sections.

    Formula: r1 = (h - 2t) / h * r0

    Args:
        r0: External corner/radius (mm)
        h: Depth/Minor axis (mm)
        t: Thickness of steel tube (mm)

    Returns:
        Inner radius r1 (mm)
    """
    if h == 0:
        return 0.0
    return (h - 2 * t) / h * r0


def calculate_concrete_area(b: float, h: float, t: float, r0: float, r1: float) -> float:
    """
    Calculate concrete area Ac for CFST sections.

    Formula: Ac = (b - 2t)(h - 2t) - (4 - π) * r1²

    Args:
        b: Width/Diameter/Major axis (mm)
        h: Depth/Diameter/Minor axis (mm)
        t: Thickness of steel tube (mm)
        r0: External corner/radius (mm)
        r1: Inner radius (mm) - calculated from calculate_inner_radius()

    Returns:
        Concrete area Ac (mm²)
    """
    # For circular sections (b == h), use circular formula
    if abs(b - h) < 0.001:
        # Circular section: Ac = π * ((b/2) - t)²
        radius_inner = (b / 2) - t
        return np.pi * radius_inner ** 2

    # For rectangular sections (r0 == 0)
    if r0 == 0:
        # Rectangular section: Ac = (b - 2t) * (h - 2t)
        return (b - 2 * t) * (h - 2 * t)

    # For round-ended sections
    # Ac = (b - 2t)(h - 2t) - (4 - π) * r1²
    return (b - 2 * t) * (h - 2 * t) - (4 - np.pi) * (r1 ** 2)


def calculate_steel_area(b: float, h: float, t: float, r0: float, r1: float) -> float:
    """
    Calculate steel area As for CFST sections.

    Formula: As = 2t(b + h) - 4t² - (4 - π)(r0² - r1²)

    Args:
        b: Width/Diameter/Major axis (mm)
        h: Depth/Diameter/Minor axis (mm)
        t: Thickness of steel tube (mm)
        r0: External corner/radius (mm)
        r1: Inner radius (mm) - calculated from calculate_inner_radius()

    Returns:
        Steel area As (mm²)
    """
    # For circular sections (b == h)
    if abs(b - h) < 0.001:
        # Circular section: As = π * ((b/2)² - ((b/2) - t)²)
        radius_outer = b / 2
        radius_inner = radius_outer - t
        return np.pi * (radius_outer ** 2 - radius_inner ** 2)

    # For rectangular sections (r0 == 0)
    if r0 == 0:
        # Rectangular section: As = 2t(b + h) - 4t²
        return 2 * t * (b + h) - 4 * (t ** 2)

    # For round-ended sections
    # As = 2t(b + h) - 4t² - (4 - π)(r0² - r1²)
    return 2 * t * (b + h) - 4 * (t ** 2) - (4 - np.pi) * (r0 ** 2 - r1 ** 2)


def calculate_theoretical_capacity(fc_value: float, fy: float,
                                  b: float, h: float, t: float, r0: float) -> Optional[float]:
    """
    Calculate theoretical capacity Nt for CFST sections.

    Formula: Nt = As * fy + Ac * fc_value

    Args:
        fc_value: Concrete compressive strength (MPa)
        fy: Steel yield strength (MPa)
        b: Width/Diameter/Major axis (mm)
        h: Depth/Diameter/Minor axis (mm)
        t: Thickness of steel tube (mm)
        r0: External corner/radius (mm)

    Returns:
        Theoretical capacity Nt (kN), or None if any critical parameter is None
    """
    # Check for None values in critical parameters
    if any(v is None for v in [fc_value, fy, b, h, t, r0]):
        return None

    # Calculate inner radius
    r1 = calculate_inner_radius(r0, h, t)

    # Calculate areas
    Ac = calculate_concrete_area(b, h, t, r0, r1)  # mm²
    As = calculate_steel_area(b, h, t, r0, r1)     # mm²

    # Convert MPa to N/mm² (1 MPa = 1 N/mm²)
    # Calculate force in N: Nt = As * fy + Ac * fc_value
    Nt_N = As * fy + Ac * fc_value

    # Convert N to kN
    Nt_kN = Nt_N / 1000

    return Nt_kN


def calculate_validation_coefficient(n_exp: float, n_theory: float) -> Optional[float]:
    """
    Calculate validation coefficient ξ.

    Formula: ξ = N_exp / N_theory

    Args:
        n_exp: Experimental capacity (kN)
        n_theory: Theoretical capacity (kN)

    Returns:
        Validation coefficient ξ (dimensionless), or None if parameters are None
    """
    if n_exp is None or n_theory is None:
        return None
    if n_theory == 0:
        return float('inf')
    return n_exp / n_theory


def determine_manual_check_status(xi: float) -> bool:
    """
    Determine if manual check is needed based on validation coefficient.

    Rules:
    - Green (0.8 < ξ < 2.5): Data correct, no manual check needed
    - Red (ξ > 10 or ξ < 0.1): Unit errors, batch correction required
    - Yellow: Manual review required
    - None or NaN: Missing data, manual check needed

    Args:
        xi: Validation coefficient

    Returns:
        True if manual check is needed, False otherwise
    """
    if xi is None or (isinstance(xi, float) and np.isnan(xi)):
        return True  # Missing data, needs manual check
    if 0.8 < xi < 2.5:
        return False  # Green zone, no manual check needed
    elif xi > 10 or xi < 0.1:
        return True   # Red zone, unit errors - manual check needed
    else:
        return True   # Yellow zone, manual review required


def validate_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply physical validation to a DataFrame of specimen data.

    Adds columns:
    - N_theory: Theoretical capacity (kN)
    - xi: Validation coefficient
    - needs_manual_check: Boolean flag for manual review
    - has_missing_data: Boolean flag indicating if any critical data is missing

    Args:
        df: DataFrame with columns: fc_value, fy, b, h, t, r0, n_exp

    Returns:
        DataFrame with added validation columns
    """
    # Make a copy to avoid modifying original
    result_df = df.copy()

    # Check for missing critical data
    critical_fields = ['fc_value', 'fy', 'b', 'h', 't', 'n_exp']
    result_df['has_missing_data'] = result_df[critical_fields].isnull().any(axis=1)

    # Calculate theoretical capacity for each row
    result_df['N_theory'] = result_df.apply(
        lambda row: calculate_theoretical_capacity(
            row['fc_value'], row['fy'],
            row['b'], row['h'], row['t'], row['r0']
        ), axis=1
    )

    # Calculate validation coefficient
    result_df['xi'] = result_df.apply(
        lambda row: calculate_validation_coefficient(row['n_exp'], row['N_theory']),
        axis=1
    )

    # Determine if manual check is needed
    result_df['needs_manual_check'] = result_df['xi'].apply(determine_manual_check_status)

    # Also mark as needing check if data is missing
    result_df['needs_manual_check'] = result_df['needs_manual_check'] | result_df['has_missing_data']

    return result_df


def get_validation_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate summary statistics for validation results.

    Args:
        df: DataFrame with validation columns (N_theory, xi, needs_manual_check)

    Returns:
        Dictionary with validation summary
    """
    if df.empty:
        return {
            'total_specimens': 0,
            'needs_manual_check': 0,
            'green_zone': 0,
            'yellow_zone': 0,
            'red_zone': 0,
            'avg_xi': 0.0,
            'min_xi': 0.0,
            'max_xi': 0.0
        }

    total = len(df)
    needs_check = df['needs_manual_check'].sum()

    # Count specimens in each zone
    green_zone = ((df['xi'] > 0.8) & (df['xi'] < 2.5)).sum()
    red_zone = ((df['xi'] > 10) | (df['xi'] < 0.1)).sum()
    yellow_zone = total - green_zone - red_zone

    # Calculate statistics
    avg_xi = df['xi'].mean()
    min_xi = df['xi'].min()
    max_xi = df['xi'].max()

    return {
        'total_specimens': total,
        'needs_manual_check': int(needs_check),
        'green_zone': int(green_zone),
        'yellow_zone': int(yellow_zone),
        'red_zone': int(red_zone),
        'avg_xi': float(avg_xi),
        'min_xi': float(min_xi),
        'max_xi': float(max_xi)
    }