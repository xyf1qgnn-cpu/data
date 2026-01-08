"""
Parallel Processing Module for CFST Data Extraction
Implements concurrent processing of PDF files using thread pools
"""

import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
import instructor
from datetime import datetime
import shutil
from models import ExtractionResult

# Configuration loaded from main.py
API_KEY = "sk-TcRezCA6VhsQ5bQvUwQxB0A6HkqKYOmpddeIGC9JKYPC6bEU"
BASE_URL = "https://api.silra.cn/v1"
MODEL_NAME = "deepseek-chat"

def process_single_pdf(file_path, filename):
    """
    Process a single PDF file in a thread

    Args:
        file_path: Full path to the PDF file
        filename: Name of the PDF file

    Returns:
        dict: Processing result with status and data
    """
    try:
        # Delayed imports to avoid circular dependency
        from main import extract_text_from_pdf, extract_data_with_ai, move_failed_file, move_excluded_file

        # Create independent client instance for thread safety
        client = instructor.patch(OpenAI(api_key=API_KEY, base_url=BASE_URL))

        # Extract text from PDF
        text = extract_text_from_pdf(file_path)
        if not text.strip():
            print(f"  - {filename}: Empty text extraction")
            move_failed_file(file_path)
            return None

        # AI extraction
        print(f"  - {filename}: Calling AI extraction...")
        json_data = extract_data_with_ai(client, text)

        if json_data:
            # Check validity
            is_valid = json_data.get("is_valid", True)

            if not is_valid:
                reason = json_data.get("reason", "No reason provided")
                print(f"  - {filename}: Excluded - {reason}")
                move_excluded_file(file_path)
                return {"file": filename, "status": "excluded", "reason": reason}

            # Process successful extraction
            processed_data = process_extraction_result(json_data, filename)
            if processed_data:
                return {
                    "file": filename,
                    "data": processed_data,
                    "status": "success"
                }
            else:
                print(f"  - {filename}: No valid data extracted")
                move_failed_file(file_path)
                return {"file": filename, "status": "failed", "reason": "No data"}
        else:
            print(f"  - {filename}: AI extraction failed")
            move_failed_file(file_path)
            return {"file": filename, "status": "failed", "reason": "API error"}

    except Exception as e:
        print(f"  - {filename}: Exception - {e}")
        move_failed_file(file_path)
        return {"file": filename, "status": "failed", "error": str(e)}

def process_extraction_result(json_data, filename):
    """
    Convert extraction result to processed data format

    Args:
        json_data: Raw extraction result from AI
        filename: Source PDF filename for ref_no

    Returns:
        dict: Aggregated data in format {Group_A: [...], Group_B: [...], Group_C: [...]}
    """
    if not json_data:
        return None

    result = {
        "Group_A": [],
        "Group_B": [],
        "Group_C": []
    }

    for group in ["Group_A", "Group_B", "Group_C"]:
        if group in json_data and isinstance(json_data[group], list):
            items = json_data[group]
            for item in items:
                item["ref_no"] = filename
                result[group].append(item)

    # Return only groups with data
    return {k: v for k, v in result.items() if v}

def process_directory_parallel(dir_path, max_workers=10):
    """
    Process all PDF files in a directory concurrently

    Args:
        dir_path: Path to directory containing PDF files
        max_workers: Maximum number of concurrent threads (default: 10)

    Returns:
        dict: Aggregated results from all PDF processing
    """
    if not os.path.exists(dir_path):
        print(f"Directory does not exist: {dir_path}")
        return None

    # Find all PDF files
    pdf_files = [f for f in os.listdir(dir_path) if f.lower().endswith('.pdf')]

    if not pdf_files:
        print(f"No PDF files found in: {dir_path}")
        return None

    print(f"\nFound {len(pdf_files)} PDF files, processing with {max_workers} workers...")

    # Prepare tasks
    tasks = [(os.path.join(dir_path, filename), filename) for filename in pdf_files]

    # Process concurrently
    all_results = {
        "Group_A": [],
        "Group_B": [],
        "Group_C": []
    }

    success_count = 0
    excluded_count = 0
    failed_count = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_file = {
            executor.submit(process_single_pdf, file_path, filename): filename
            for file_path, filename in tasks
        }

        # Collect results as they complete
        for future in as_completed(future_to_file):
            filename = future_to_file[future]
            try:
                result = future.result(timeout=300)  # 5 minute timeout

                if result:
                    status = result.get("status", "unknown")

                    if status == "success" and "data" in result:
                        # Merge results into all_results
                        for group, items in result["data"].items():
                            all_results[group].extend(items)
                        success_count += 1
                        print(f"  ✓ Success: {filename} ({len(result['data'])} groups)")

                    elif status == "excluded":
                        excluded_count += 1
                        reason = result.get("reason", "Unknown")
                        print(f"  ⊘ Excluded: {filename} ({reason})")

                    elif status == "failed":
                        failed_count += 1
                        error = result.get("error", "Unknown")
                        print(f"  ✗ Failed: {filename} ({error})")

            except TimeoutError:
                print(f"  ✗ Timeout: {filename}")
                failed_count += 1
            except Exception as e:
                print(f"  ✗ Exception for {filename}: {e}")
                failed_count += 1

    # Print summary
    print(f"\n=== Parallel Processing Summary ===")
    print(f"Total files: {len(pdf_files)}")
    print(f"Successful: {success_count}")
    print(f"Excluded: {excluded_count}")
    print(f"Failed: {failed_count}")

    # Count total specimens extracted
    total_specimens = sum(len(items) for items in all_results.values())
    for group, items in all_results.items():
        if items:
            print(f"  {group}: {len(items)} specimens")

    return {
        "results": all_results,
        "summary": {
            "total_files": len(pdf_files),
            "successful": success_count,
            "excluded": excluded_count,
            "failed": failed_count,
            "total_specimens": total_specimens
        }
    }

def process_directory_sequential(dir_path):
    """
    Sequential processing of PDF files (for comparison)

    Args:
        dir_path: Path to directory containing PDF files

    Returns:
        dict: Aggregated results from all PDF processing
    """
    import main  # Import main module
    from main import client as global_client

    # Delayed imports to avoid circular dependency
    from main import extract_text_from_pdf, extract_data_with_ai, move_failed_file, move_excluded_file

    if not os.path.exists(dir_path):
        print(f"Directory does not exist: {dir_path}")
        return None

    pdf_files = [f for f in os.listdir(dir_path) if f.lower().endswith('.pdf')]

    if not pdf_files:
        print(f"No PDF files found in: {dir_path}")
        return None

    print(f"\nFound {len(pdf_files)} PDF files, processing sequentially...")

    all_results = {
        "Group_A": [],
        "Group_B": [],
        "Group_C": []
    }

    for filename in pdf_files:
        file_path = os.path.join(dir_path, filename)

        # Use global client for sequential processing
        text = extract_text_from_pdf(file_path)

        if not text.strip():
            print(f"  - {filename}: Empty text extraction")
            move_failed_file(file_path)
            continue

        print(f"  - {filename}: Calling AI extraction...")
        json_data = extract_data_with_ai(global_client, text)

        if json_data:
            is_valid = json_data.get("is_valid", True)

            if not is_valid:
                reason = json_data.get("reason", "No reason provided")
                print(f"  ⊘ Excluded: {reason}")
                move_excluded_file(file_path)
            else:
                processed_data = process_extraction_result(json_data, filename)
                if processed_data:
                    for group, items in processed_data.items():
                        all_results[group].extend(items)
                    print(f"  ✓ Success: {filename} ({len(processed_data)} groups)")
        else:
            print(f"  - {filename}: AI extraction failed")
            move_failed_file(file_path)

    total_specimens = sum(len(items) for items in all_results.values())
    print(f"\n=== Sequential Processing Summary ===")
    print(f"Total files: {len(pdf_files)}")
    print(f"Total specimens: {total_specimens}")

    return {
        "results": all_results,
        "summary": {
            "total_files": len(pdf_files),
            "total_specimens": total_specimens
        }
    }

def process_aggregation(results, config, state):
    """
    Aggregate parallel results and save to desired output format

    Args:
        results: Results from parallel or sequential processing
        config: Configuration dictionary
        state: State dictionary

    Returns:
        pandas.DataFrame: Combined dataframe for all groups
    """
    import pandas as pd
    from styling import reorder_columns_for_export

    if not results or "results" not in results:
        return None

    processed_data = results["results"]

    # Convert to DataFrames
    dataframes = {}
    for group, items in processed_data.items():
        if items:
            df = pd.DataFrame(items)
            df = reorder_columns_for_export(df)
            dataframes[group] = df
        else:
            dataframes[group] = pd.DataFrame()

    return dataframes
