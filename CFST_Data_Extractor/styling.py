"""
Excel styling functions for CFST data export (Workflow 2.0)
Based on requirements spec: 06-requirements-spec.md
"""

import pandas as pd
from typing import Dict, Any


def apply_excel_styling(df: pd.DataFrame, writer: pd.ExcelWriter, sheet_name: str):
    """
    Apply styling to Excel sheet with highlighting for manual review.

    Requirements:
    - Apply light red background to rows where needs_manual_check == True
    - Position source_evidence next to n_exp
    - Maintain existing column order from COL_MAPPING

    Args:
        df: DataFrame to export
        writer: pandas ExcelWriter object
        sheet_name: Name of the Excel sheet
    """
    # Create a styled DataFrame
    styled_df = df.copy()

    # Define styling function for manual check highlighting
    def highlight_manual_check(row):
        """
        Apply light red background to rows needing manual review.
        """
        # 使用重命名后的列名 'Needs Manual Check'
        if 'Needs Manual Check' in row.index:
            needs_check = row['Needs Manual Check']
            # 处理各种可能的布尔值表示：True/False, 1/0, 'True'/'False'
            if isinstance(needs_check, bool) and needs_check:
                return ['background-color: #FFCCCC'] * len(row)
            elif isinstance(needs_check, (int, float)) and needs_check:
                return ['background-color: #FFCCCC'] * len(row)
            elif isinstance(needs_check, str) and needs_check.lower() in ('true', '1', 'yes'):
                return ['background-color: #FFCCCC'] * len(row)
        return [''] * len(row)

    # Apply styling if DataFrame is not empty
    if not df.empty:
        # Create a Styler object
        styler = df.style

        # Apply center alignment first (基础样式)
        all_columns = df.columns.tolist()
        columns_to_center = [col for col in all_columns if col != 'Ref.No.']
        if columns_to_center:
            center_style = {'text-align': 'center'}
            styler = styler.set_properties(subset=columns_to_center, **center_style)

        # Apply highlighting for manual check rows (叠加样式)
        if 'Needs Manual Check' in df.columns:
            styler = styler.apply(highlight_manual_check, axis=1)

        # Export styled DataFrame to Excel
        styler.to_excel(writer, sheet_name=sheet_name, index=False)

        # Get the workbook and worksheet for additional formatting
        workbook = writer.book
        worksheet = writer.sheets[sheet_name]

        # Auto-adjust column widths
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter  # Get the column name
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)  # Cap at 50 characters
            worksheet.column_dimensions[column_letter].width = adjusted_width

        # Freeze header row
        worksheet.freeze_panes = 'A2'
    else:
        # Export empty DataFrame without styling
        df.to_excel(writer, sheet_name=sheet_name, index=False)


def reorder_columns_for_export(df: pd.DataFrame, col_mapping: Dict[str, str]) -> pd.DataFrame:
    """
    Reorder DataFrame columns for export with source_evidence next to n_exp.

    Requirements:
    - Maintain existing 15-column structure from COL_MAPPING
    - Add new columns: source_evidence, N_theory, xi, needs_manual_check
    - Position source_evidence next to n_exp

    Args:
        df: DataFrame with all columns
        col_mapping: Original column mapping dictionary

    Returns:
        DataFrame with reordered columns
    """
    # Start with original columns in correct order
    original_columns = list(col_mapping.keys())

    # Ensure all original columns exist
    for col in original_columns:
        if col not in df.columns:
            df[col] = ""

    # Create new column order
    new_order = []

    # Add original columns up to n_exp
    for col in original_columns:
        new_order.append(col)
        # Insert source_evidence right after n_exp
        if col == 'n_exp':
            if 'source_evidence' in df.columns:
                new_order.append('source_evidence')
            else:
                df['source_evidence'] = ""
                new_order.append('source_evidence')

    # Add validation columns at the end
    validation_columns = ['N_theory', 'xi', 'needs_manual_check']
    for col in validation_columns:
        if col not in df.columns:
            df[col] = "" if col == 'needs_manual_check' else 0.0
        new_order.append(col)

    # Select columns in new order
    result_df = df[new_order].copy()

    # Rename columns according to mapping
    rename_dict = col_mapping.copy()
    # Add new column names for validation columns
    rename_dict.update({
        'source_evidence': 'Source Evidence',
        'N_theory': 'N_theory (kN)',
        'xi': 'ξ (Validation Coefficient)',
        'needs_manual_check': 'Needs Manual Check'
    })

    # Only rename columns that exist in the DataFrame
    existing_rename = {k: v for k, v in rename_dict.items() if k in result_df.columns}
    result_df.rename(columns=existing_rename, inplace=True)

    return result_df


def export_to_excel_with_styling(all_data: Dict[str, pd.DataFrame],
                                 output_file: str,
                                 col_mapping: Dict[str, str]):
    """
    Export all data to styled Excel file.

    Args:
        all_data: Dictionary mapping group names to DataFrames
        output_file: Path to output Excel file
        col_mapping: Column mapping dictionary

    Returns:
        Boolean indicating success
    """
    try:
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            has_data = False

            for group, df in all_data.items():
                if df is not None and not df.empty:
                    # Reorder columns with source_evidence next to n_exp
                    df_export = reorder_columns_for_export(df, col_mapping)

                    # Apply Excel styling
                    apply_excel_styling(df_export, writer, group)
                    has_data = True
                else:
                    # Create empty sheet with headers
                    df_empty = pd.DataFrame(columns=col_mapping.values())
                    df_empty.to_excel(writer, sheet_name=group, index=False)

            if has_data:
                print(f"Successfully exported styled Excel file: {output_file}")
                return True
            else:
                print("No data to export")
                return False

    except Exception as e:
        print(f"Error exporting Excel file: {e}")
        return False


def generate_validation_report(df: pd.DataFrame, group_name: str) -> str:
    """
    Generate a text report of validation results.

    Args:
        df: DataFrame with validation columns
        group_name: Name of the specimen group

    Returns:
        Formatted validation report
    """
    if df.empty or 'needs_manual_check' not in df.columns:
        return f"Group {group_name}: No validation data available"

    total = len(df)
    needs_check = df['needs_manual_check'].sum()
    percentage = (needs_check / total * 100) if total > 0 else 0

    # Count by zone
    if 'xi' in df.columns:
        green = ((df['xi'] > 0.8) & (df['xi'] < 2.5)).sum()
        red = ((df['xi'] > 10) | (df['xi'] < 0.1)).sum()
        yellow = total - green - red
    else:
        green = red = yellow = 0

    report = f"""
=== Validation Report for {group_name} ===
Total specimens: {total}
Need manual check: {needs_check} ({percentage:.1f}%)

Zone distribution:
- Green zone (0.8 < ξ < 2.5): {green} specimens
- Yellow zone (manual review): {yellow} specimens
- Red zone (unit errors): {red} specimens

Recommendations:
"""
    if red > 0:
        report += "- Check unit conversions for specimens in red zone\n"
    if yellow > 0:
        report += "- Review specimens in yellow zone for data accuracy\n"
    if green == total:
        report += "- All data passes physical validation checks ✓\n"

    return report