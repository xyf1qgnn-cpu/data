"""
Vision-based PDF Processing for CFST Data Extraction (Workflow 3.0)
Architecture upgrade from text-based (pdfplumber) to vision-based AI analysis.
Supports adaptive page scanning, zero-data detection, and comprehensive error handling.

Key Features:
- Adaptive page scanning (full scan for ≤15 pages, truncated for >15 pages)
- Vision-based data extraction via Gemini 3 Flash
- Zero-data detection with Manual_Review workflow
- Configuration-driven architecture
- Comprehensive error handling and validation
"""

# Note: Text-based extraction functions (segment_pdf_text_intelligently, extract_tables, etc.)
# are kept for backward compatibility but are no longer actively used in the main workflow.
# The system has been upgraded to vision-based processing via process_pdf().

import re
import os
import base64
import io
import logging
import json
from typing import List, Tuple, Optional, Dict, Any
from pdf2image import convert_from_path
from PIL import Image
import pdfplumber

# Get logger instance
logger = logging.getLogger('cfst_extractor')


def parse_ai_response(response_content: str) -> Dict[str, Any]:
    """
    Parse AI response content as JSON with truncation detection.

    This function handles:
    1. Markdown code block removal
    2. Truncated JSON detection
    3. JSON parsing with error handling

    Args:
        response_content: Raw response content from AI model

    Returns:
        Parsed JSON dictionary

    Raises:
        json.JSONDecodeError: If JSON is malformed or truncated
        Exception: For other parsing errors
    """
    import json

    content = response_content.strip()

    # Remove markdown code block markers
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]

    content = content.strip()

    # Check for truncated JSON
    # 1. Check for unclosed braces
    open_braces = content.count('{')
    close_braces = content.count('}')
    if open_braces != close_braces:
        raise json.JSONDecodeError(
            f"JSON appears to be truncated: {open_braces} opening braces but {close_braces} closing braces",
            content,
            len(content)
        )

    # 2. Check for unclosed strings
    in_string = False
    escaped = False
    for i, char in enumerate(content):
        if not in_string:
            if char == '"':
                in_string = True
        else:
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == '"':
                in_string = False

    if in_string and not content.endswith('"'):
        raise json.JSONDecodeError(
            "JSON appears to have truncated string",
            content,
            len(content)
        )

    try:
        # Try to parse JSON
        result = json.loads(content)
        return result
    except json.JSONDecodeError as e:
        # Re-raise with more context
        raise json.JSONDecodeError(
            f"Invalid JSON format: {str(e)}",
            e.doc,
            e.pos
        )


def get_smart_pages_to_process(pdf_path: str, config: Dict[str, Any]) -> Tuple[List[int], str, List[Dict]]:
    """
    Main function: determine which pages to process using smart filtering.

    This function implements the two-phase processing strategy:
    Phase 1: Text scouting (extract text from all pages)
    Phase 2: Intelligent page selection (score and filter pages)

    Args:
        pdf_path: Path to the PDF file
        config: Configuration dictionary

    Returns:
        Tuple containing:
        - List of page numbers to process (1-indexed)
        - Strategy description string (for logging)
        - Debug info list (containing page scores and selection reasons)
    """
    processing_settings = config.get("processing_settings", {})
    page_filtering = processing_settings.get("page_filtering", {})

    # Get configuration parameters
    short_threshold = processing_settings.get("short_paper_threshold", 10)
    max_selected = page_filtering.get("max_selected_pages", 8)
    absolute_max = processing_settings.get("absolute_max_pages", 30)
    mandatory_first = page_filtering.get("mandatory_include_first_page", True)

    try:
        # Phase 1: Extract text from all pages
        page_texts = extract_page_texts(pdf_path)
        total_pages = len(page_texts)

        # Short paper: process all pages
        if total_pages <= short_threshold:
            pages_to_process = list(range(1, total_pages + 1))
            strategy_desc = f"全量扫描 ({total_pages}页 ≤ {short_threshold}页阈值，短论文)"
            debug_info = [{"page": i, "score": 0, "reason": "短论文全量扫描"} for i in pages_to_process]
            return pages_to_process, strategy_desc, debug_info

        # Long paper: apply smart filtering
        # Phase 2: Score all pages
        page_scores = []
        for page_num, text in page_texts.items():
            score = score_page_content(text, config)
            page_scores.append({
                "page": page_num,
                "score": score,
                "text_length": len(text)
            })

        # Sort by score (descending)
        page_scores.sort(key=lambda x: x["score"], reverse=True)

        # Select pages
        selected_pages = []
        debug_info = []

        # Always include page 1 if configured
        if mandatory_first and 1 not in selected_pages:
            selected_pages.append(1)
            debug_info.append({
                "page": 1,
                "score": next((p["score"] for p in page_scores if p["page"] == 1), 0),
                "reason": "强制包含第1页（摘要）"
            })

        # Select top-scoring pages (excluding negative scores)
        for page_info in page_scores:
            page_num = page_info["page"]
            score = page_info["score"]

            # Skip if already selected
            if page_num in selected_pages:
                continue

            # Skip pages with negative scores (likely references)
            if score < 0:
                continue

            # Add to selection
            selected_pages.append(page_num)
            debug_info.append({
                "page": page_num,
                "score": score,
                "reason": f"得分: {score}"
            })

            # Stop when we reach max_selected
            if len(selected_pages) >= max_selected:
                break

        # Sort selected pages by page number (for logical order)
        selected_pages.sort()

        # Apply absolute max limit
        if len(selected_pages) > absolute_max:
            selected_pages = selected_pages[:absolute_max]
            debug_info = debug_info[:absolute_max]
            strategy_desc = f"智能筛选 (选择{len(selected_pages)}页/{total_pages}页，受{absolute_max}页绝对限制)"
        else:
            strategy_desc = f"智能筛选 (选择{len(selected_pages)}页/{total_pages}页)"

        # Log detailed information (file only)
        logger.debug(f"页面评分详情: {page_scores}")
        logger.debug(f"选中页码: {selected_pages}")
        logger.debug(f"选择原因: {debug_info}")

        return selected_pages, strategy_desc, debug_info

    except Exception as e:
        # Fallback: use simple truncation if smart filtering fails
        print(f"  ❌ 智能筛选失败: {str(e)}")
        pages_to_process = list(range(1, min(get_page_count(pdf_path), max_selected) + 1))
        strategy_desc = f"智能筛选失败，回退到简单截断 (前{len(pages_to_process)}页)"
        debug_info = [{"page": i, "score": 0, "reason": "智能筛选失败，回退"} for i in pages_to_process]
        return pages_to_process, strategy_desc, debug_info


def score_page_content(text: str, config: Dict[str, Any]) -> int:
    """
    Score page content based on keyword matches and patterns.

    Scoring rules:
    - Table titles: +10 points
    - Data keywords: +5 points
    - References/citations: -5 points
    - Normal text: +1 point per significant word

    Args:
        text: Page text content
        config: Configuration dictionary with page_filtering settings

    Returns:
        Integer score for the page
    """
    if not text or not text.strip():
        return 0

    # Get filtering configuration
    page_filtering = config.get("processing_settings", {}).get("page_filtering", {})
    patterns = page_filtering.get("patterns", {})
    weights = page_filtering.get("weights", {})

    score = 0

    # Compile regex patterns for performance
    # Table patterns (high weight)
    table_patterns = patterns.get("table_patterns", [
        r'(?i)Table\s+\d+',
        r'(?i)Tab\.\s*\d+',
        r'(?i)TABLE\s+\d+'
    ])

    # Data keyword patterns (medium weight)
    data_patterns = patterns.get("data_patterns", [
        r'(?i)Specimen',
        r'(?i)Experimental',
        r'(?i)Test\s+results?',
        r'\d+\.\d+\s*(mm|MPa|kN)',
        r'(?i)[BD]\/t\s*[=:]?\s*\d+',
        r'(?i)Load[-\s]displacement',
        r'(?i)Axial\s+(load|force)',
        r'(?i)Compressive\s+strength'
    ])

    # Reference patterns (negative weight)
    reference_patterns = patterns.get("reference_patterns", [
        r'(?i)^\s*References?\s*$',
        r'(?i)^\s*Bibliography\s*$'
    ])

    # Simulation patterns (negative weight, lighter than references)
    simulation_patterns = patterns.get("simulation_patterns", [
        r'(?i)Finite\s+Element',
        r'(?i)FE\s+model',
        r'(?i)Mesh\s+generation',
        r'(?i)Simulation\s+results',
        r'(?i)Numerical\s+analysis',
        r'(?i)Analytical\s+study'
    ])

    # Apply table patterns (high weight)
    table_weight = weights.get("table_weight", 40)
    for pattern in table_patterns:
        matches = re.findall(pattern, text)
        score += len(matches) * table_weight

    # Apply data patterns (medium weight)
    data_weight = weights.get("data_weight", 5)
    for pattern in data_patterns:
        matches = re.findall(pattern, text)
        score += len(matches) * data_weight

    # Apply reference patterns (negative weight)
    reference_weight = weights.get("reference_weight", -20)
    for pattern in reference_patterns:
        matches = re.findall(pattern, text)
        score += len(matches) * reference_weight

    # Apply simulation patterns (lighter negative weight)
    simulation_weight = weights.get("simulation_weight", -10)
    for pattern in simulation_patterns:
        matches = re.findall(pattern, text)
        score += len(matches) * simulation_weight

    # Add base score for non-empty content (+1 per 10 words, minimum 1)
    base_weight = weights.get("base_weight", 1)
    word_count = len(text.split())
    if word_count > 0:
        base_score = max(1, word_count // 10)
        score += base_score * base_weight

    return score


def extract_page_texts(pdf_path: str) -> Dict[int, str]:
    """
    Extract text from all pages of a PDF using pdfplumber.

    This function performs phase-one text scouting for smart page filtering.
    It extracts text from all pages without converting to images or calling APIs.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Dictionary mapping page numbers (1-indexed) to extracted text

    Raises:
        FileNotFoundError: If PDF file doesn't exist
        Exception: If text extraction fails
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    try:
        page_texts = {}
        with pdfplumber.open(pdf_path) as pdf:
            # Iterate through pages (1-indexed)
            for page_num, page in enumerate(pdf.pages, 1):
                # Extract text from the page
                text = page.extract_text() or ""
                page_texts[page_num] = text

        return page_texts

    except Exception as e:
        raise Exception(f"Text extraction failed: {str(e)}")


def segment_pdf_text_intelligently(text: str, max_length: int = 50000) -> List[str]:
    """
    Intelligently segment PDF text to preserve important sections.

    Requirements:
    - Preserve beginning of document (abstract, introduction, methodology)
    - Extract tables and figures (likely containing specimen data)
    - Include appendices (often containing detailed test results)
    - Exclude references section
    - Implement efficient segmentation algorithm

    Args:
        text: Full PDF text
        max_length: Maximum length for each segment (default: 50,000 chars)

    Returns:
        List of text segments
    """
    if len(text) <= max_length:
        return [text]

    # Find important sections using common academic paper patterns
    sections = identify_important_sections(text)

    # If we can't identify sections, fall back to simple segmentation
    if not sections:
        return segment_text_simple(text, max_length)

    # Build segments prioritizing important sections
    segments = build_intelligent_segments(text, sections, max_length)

    return segments


def identify_important_sections(text: str) -> List[Tuple[str, int, int]]:
    """
    Identify important sections in academic paper text.

    Returns:
        List of tuples (section_name, start_index, end_index)
    """
    sections = []

    # Common section headers in academic papers
    section_patterns = [
        (r'(?i)\babstract\b', 'abstract'),
        (r'(?i)\bintroduction\b', 'introduction'),
        (r'(?i)\bmethodology\b', 'methodology'),
        (r'(?i)\bmaterials and methods\b', 'methodology'),
        (r'(?i)\bexperimental\b', 'experimental'),
        (r'(?i)\btest results\b', 'results'),
        (r'(?i)\bresults and discussion\b', 'results'),
        (r'(?i)\bconclusion\b', 'conclusion'),
        (r'(?i)\bappendix\b', 'appendix'),
        (r'(?i)\btable\s+\d+', 'table'),  # Table X
        (r'(?i)\bfigure\s+\d+', 'figure'),  # Figure X
        (r'(?i)\breferences\b', 'references'),
    ]

    # Find all matches
    for pattern, section_name in section_patterns:
        matches = list(re.finditer(pattern, text))
        for match in matches:
            sections.append((section_name, match.start(), match.end()))

    # Sort by position
    sections.sort(key=lambda x: x[1])

    # Merge adjacent sections and define boundaries
    merged_sections = []
    for i, (name, start, end) in enumerate(sections):
        # Find end of this section (start of next section or end of text)
        if i < len(sections) - 1:
            next_start = sections[i + 1][1]
            section_end = next_start
        else:
            section_end = len(text)

        # Skip references section (we want to exclude it)
        if name == 'references':
            continue

        merged_sections.append((name, start, section_end))

    return merged_sections


def build_intelligent_segments(text: str, sections: List[Tuple[str, int, int]],
                               max_length: int) -> List[str]:
    """
    Build intelligent text segments prioritizing important sections.

    Strategy:
    1. Always include abstract, introduction, methodology
    2. Prioritize tables and figures
    3. Include appendices
    4. Exclude references
    5. Fill remaining space with other content

    Args:
        text: Full text
        sections: Identified sections
        max_length: Maximum segment length

    Returns:
        List of segments
    """
    segments = []
    current_segment = ""
    current_length = 0

    # Define priority order
    priority_sections = ['abstract', 'introduction', 'methodology', 'experimental',
                         'table', 'figure', 'results', 'appendix']

    # Sort sections by priority and position
    sorted_sections = []
    for name, start, end in sections:
        priority = priority_sections.index(name) if name in priority_sections else len(priority_sections)
        sorted_sections.append((priority, start, end, name))

    sorted_sections.sort(key=lambda x: (x[0], x[1]))

    for priority, start, section_end, name in sorted_sections:
        section_text = text[start:section_end]
        section_length = len(section_text)

        # If section fits in current segment, add it
        if current_length + section_length <= max_length:
            if current_segment:
                current_segment += "\n\n" + section_text
            else:
                current_segment = section_text
            current_length += section_length
        else:
            # If current segment has content, save it
            if current_segment:
                segments.append(current_segment)

            # Start new segment with this section
            if section_length <= max_length:
                current_segment = section_text
                current_length = section_length
            else:
                # Section is too large, split it
                subsegments = segment_text_simple(section_text, max_length)
                # First subsegment goes to current segment
                current_segment = subsegments[0]
                current_length = len(current_segment)
                segments.append(current_segment)

                # Remaining subsegments become their own segments
                for subsegment in subsegments[1:]:
                    segments.append(subsegment)
                    current_segment = ""
                    current_length = 0

    # Add final segment if any
    if current_segment:
        segments.append(current_segment)

    # If no segments were created (e.g., no sections identified), fall back
    if not segments:
        return segment_text_simple(text, max_length)

    return segments


def segment_text_simple(text: str, max_length: int) -> List[str]:
    """
    Simple text segmentation by character count.

    Args:
        text: Text to segment
        max_length: Maximum length per segment

    Returns:
        List of text segments
    """
    segments = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + max_length, text_length)

        # Try to break at paragraph boundary if possible
        if end < text_length:
            # Look for paragraph break near the end
            paragraph_break = text.rfind('\n\n', start, end)
            if paragraph_break != -1 and paragraph_break > start + max_length * 0.7:
                end = paragraph_break

        segments.append(text[start:end])
        start = end

        # Skip whitespace at beginning of next segment
        while start < text_length and text[start].isspace():
            start += 1

    return segments


def extract_tables_and_figures(text: str) -> Tuple[List[str], List[str]]:
    """
    Extract tables and figures from text.

    Args:
        text: PDF text

    Returns:
        Tuple of (tables, figures) lists
    """
    tables = []
    figures = []

    # Pattern for tables (simplified - in real implementation would use more sophisticated parsing)
    table_pattern = r'(?i)table\s+\d+[^\n]*\n(?:.*?\n){1,20}?'  # Capture table title and some following lines
    figure_pattern = r'(?i)figure\s+\d+[^\n]*\n(?:.*?\n){1,10}?'  # Capture figure caption

    table_matches = re.finditer(table_pattern, text)
    figure_matches = re.finditer(figure_pattern, text)

    for match in table_matches:
        tables.append(match.group())

    for match in figure_matches:
        figures.append(match.group())

    return tables, figures


def is_likely_data_section(text: str) -> bool:
    """
    Determine if text section is likely to contain specimen data.

    Args:
        text: Text section

    Returns:
        True if likely to contain data
    """
    # Check for common data indicators
    indicators = [
        r'\b\d+\.\d+\b',  # Decimal numbers
        r'\bmm\b', r'\bMPa\b', r'\bkN\b',  # Common units
        r'\bspecimen\b', r'\btest\b', r'\bresult\b',  # Data-related terms
        r'\btable\b', r'\bfigure\b',  # Tables and figures
    ]

    score = 0
    for pattern in indicators:
        matches = re.findall(pattern, text, re.IGNORECASE)
        score += len(matches)

    # Arbitrary threshold - adjust based on testing
    return score > 5



# ============================================================================
# Vision-based PDF Processing Functions (Workflow 3.0)
# ============================================================================

def get_page_count(pdf_path: str) -> int:
    """
    Get the total number of pages in a PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Number of pages in the PDF

    Raises:
        FileNotFoundError: If PDF file doesn't exist
        Exception: If PDF cannot be read
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    try:
        # Use pdf2image with first_page and last_page to count pages
        # We'll try to convert just the first page to get metadata
        images = convert_from_path(
            pdf_path,
            first_page=1,
            last_page=1,
            dpi=72,  # Low DPI for faster processing
            fmt='ppm'  # Fast format
        )

        # If we can read the first page, the PDF is valid
        # pdf2image doesn't directly provide page count, so we'll use a different approach
        # Try to convert with a high page number and catch the error
        try:
            # Try to convert page 10000 - this will fail and tell us the actual page count
            images = convert_from_path(
                pdf_path,
                first_page=1,
                last_page=10000,
                dpi=72,
                fmt='ppm'
            )
            return len(images)
        except Exception as e:
            # Extract page count from error message if possible
            error_str = str(e)
            if "page" in error_str.lower() and "greater than" in error_str.lower():
                # Try to extract the max page number from error
                import re
                match = re.search(r'(\d+)', error_str)
                if match:
                    return int(match.group(1))

            # If we can't extract from error, we'll count manually
            # This is slower but reliable
            print(f"  警告: 无法快速获取页数，正在逐页统计...")
            page_num = 0
            while True:
                try:
                    images = convert_from_path(
                        pdf_path,
                        first_page=page_num + 1,
                        last_page=page_num + 1,
                        dpi=72,
                        fmt='ppm'
                    )
                    if images:
                        page_num += 1
                    else:
                        break
                except:
                    break
            return page_num

    except Exception as e:
        raise Exception(f"无法读取PDF页数: {str(e)}")


def should_scan_all_pages(page_count: int, threshold: int) -> bool:
    """
    Determine if all pages should be scanned based on page count.

    Args:
        page_count: Total number of pages in PDF
        threshold: Threshold for short papers (scan all if <= threshold)

    Returns:
        True if all pages should be scanned, False if should limit
    """
    return page_count <= threshold


def get_pages_to_process(page_count: int, config: dict) -> Tuple[List[int], str]:
    """
    Determine which pages to process based on adaptive strategy.

    This function decides whether to use smart filtering or fall back to simple truncation.
    The decision is based on the enable_smart_filtering configuration.

    Args:
        page_count: Total number of pages in PDF
        config: Configuration dictionary with processing_settings

    Returns:
        Tuple of (page_numbers, strategy_description)
            page_numbers: List of page numbers to process (1-indexed)
            strategy_description: Description of the strategy used
    """
    processing_settings = config.get("processing_settings", {})
    enable_smart = processing_settings.get("enable_smart_filtering", True)

    if enable_smart and "pdf_path" in config:
        # Use smart page filtering
        pages, desc, _ = get_smart_pages_to_process(config["pdf_path"], config)
        return pages, desc
    else:
        # Fall back to simple truncation strategy
        threshold = processing_settings.get("short_paper_threshold", 10)
        max_limit = processing_settings.get("max_scan_limit", 10)

        if should_scan_all_pages(page_count, threshold):
            # Process all pages
            pages = list(range(1, page_count + 1))
            description = f"全量扫描 ({page_count}页 ≤ {threshold}页阈值)"
        else:
            # Process only first max_limit pages
            pages = list(range(1, min(page_count, max_limit) + 1))
            description = f"截断扫描 (前{len(pages)}页/{page_count}页，阈值: {threshold}页)"

        return pages, description


def convert_pdf_to_images(
    pdf_path: str,
    page_numbers: Optional[List[int]] = None,
    dpi: int = 150,
    fmt: str = 'png'
) -> List[Image.Image]:
    """
    Convert PDF pages to images.

    Args:
        pdf_path: Path to the PDF file
        page_numbers: List of page numbers to convert (1-indexed)
                     If None, converts all pages
        dpi: DPI for image conversion (default: 150)
        fmt: Output image format ('png', 'jpeg', etc.)

    Returns:
        List of PIL Image objects

    Raises:
        FileNotFoundError: If PDF file doesn't exist
        Exception: If conversion fails
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    try:
        if page_numbers:
            # Convert specific pages
            min_page = min(page_numbers)
            max_page = max(page_numbers)

            images = convert_from_path(
                pdf_path,
                first_page=min_page,
                last_page=max_page,
                dpi=dpi,
                fmt=fmt
            )

            # If we requested specific pages but got a range,
            # extract only the pages we need
            if len(page_numbers) != len(images):
                # Map page numbers to indices (0-indexed)
                page_indices = [p - min_page for p in page_numbers]
                images = [images[i] for i in page_indices if i < len(images)]
        else:
            # Convert all pages
            images = convert_from_path(
                pdf_path,
                dpi=dpi,
                fmt=fmt
            )

        # Log success (console: brief, file: detailed)
        logger.info(f"成功转换 {len(images)} 页为图片")
        logger.debug(f"图片转换详情 - PDF: {pdf_path}, 页码: {page_numbers}, DPI: {dpi}, 格式: {fmt}")

        return images

    except Exception as e:
        raise Exception(f"PDF转图片失败: {str(e)}")


def encode_image_to_base64(image: Image.Image, format: str = 'PNG') -> str:
    """
    Encode a PIL Image to base64 string for API transmission.

    Args:
        image: PIL Image object
        format: Image format for encoding ('PNG', 'JPEG', etc.)

    Returns:
        Base64 encoded string with data URI prefix

    Raises:
        Exception: If encoding fails
    """
    try:
        # Create bytes buffer
        buffer = io.BytesIO()

        # Save image to buffer
        image.save(buffer, format=format)

        # Get the bytes value
        image_bytes = buffer.getvalue()

        # Encode to base64
        import base64
        base64_encoded = base64.b64encode(image_bytes).decode('utf-8')

        # Create data URI
        mime_type = f'image/{format.lower()}'
        data_uri = f'data:{mime_type};base64,{base64_encoded}'

        return data_uri

    except Exception as e:
        raise Exception(f"图片Base64编码失败: {str(e)}")


def encode_images_to_base64(images: List[Image.Image], format: str = 'PNG') -> List[str]:
    """
    Encode multiple PIL Images to base64 strings.

    Args:
        images: List of PIL Image objects
        format: Image format for encoding

    Returns:
        List of base64 encoded strings

    Raises:
        Exception: If encoding fails
    """
    encoded_images = []
    for idx, image in enumerate(images):
        try:
            encoded = encode_image_to_base64(image, format)
            encoded_images.append(encoded)
        except Exception as e:
            raise Exception(f"第 {idx + 1} 张图片编码失败: {str(e)}")

    return encoded_images


def build_vision_payload(
    encoded_images: List[str],
    system_prompt: str,
    user_message: str = "请分析这些学术论文页面并提取CFST试验数据。"
) -> dict:
    """
    Build OpenAI-compatible vision API payload.

    Args:
        encoded_images: List of base64 encoded images with data URI prefix
        system_prompt: System prompt for the AI model
        user_message: User message describing the task

    Returns:
        Dictionary payload for OpenAI chat completions API
    """
    # Build message content with images
    content = [{"type": "text", "text": user_message}]

    # Add each image to the content
    for idx, image_data in enumerate(encoded_images):
        content.append({
            "type": "image_url",
            "image_url": {
                "url": image_data,
                "detail": "high"  # Use high detail for better table recognition
            }
        })

    # Construct the payload
    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content}
        ]
    }

    return payload


def call_vision_api(
    client,
    payload: dict,
    model_name: str,
    temperature: float = 0.1,
    max_tokens: int = 8192,
    max_retries: int = 3
) -> dict:
    """
    Call vision API with retry logic and error handling.

    Args:
        client: OpenAI client instance
        payload: Vision API request payload
        model_name: Model name to use
        temperature: Temperature for generation (default: 0.1)
        max_tokens: Maximum tokens to generate (default: 8192)
        max_retries: Maximum retry attempts (default: 3)

    Returns:
        API response as dictionary

    Raises:
        Exception: If all retries fail
    """
    import time
    import json
    from openai import OpenAIError

    # Add model and parameters to payload
    payload["model"] = model_name
    payload["temperature"] = temperature
    payload["max_tokens"] = max_tokens

    last_error = None

    for attempt in range(max_retries):
        try:
            # Log API request (file only)
            logger.debug(f"API请求 - 模型: {model_name}, max_tokens: {max_tokens}")
            logger.debug(f"请求payload: {payload}")

            # Make API call
            logger.info("🤖 正在调用AI模型...")
            response = client.chat.completions.create(**payload)

            # Extract the response text
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content

                # Log API response (file only)
                logger.debug(f"API响应长度: {len(content)}")
                logger.debug(f"完整响应内容: {content}")

                # Parse response using new function with truncation detection
                try:
                    result = parse_ai_response(content)
                    return result
                except json.JSONDecodeError as e:
                    # Truncated JSON detected
                    truncated_preview = content[-500:] if len(content) > 500 else content
                    raise json.JSONDecodeError(
                        f"JSON解析失败（可能被截断）: {str(e)}",
                        truncated_preview,
                        0
                    )
            else:
                raise Exception("API返回空响应")

        except OpenAIError as e:
            last_error = e
            logger.error(f"API调用失败 (attempt {attempt + 1}/{max_retries}): {e}")

            # Check if we should retry
            if attempt < max_retries - 1:
                # Exponential backoff
                wait_time = (2 ** attempt) * 2  # 2, 4, 8 seconds
                logger.info(f"等待{wait_time}秒后重试...")
                time.sleep(wait_time)
            else:
                break

    # All retries failed
    raise Exception(f"API调用失败（重试{max_retries}次）: {str(last_error)}")


def process_pdf(
    pdf_path: str,
    client,
    config: Dict[str, Any],
    system_prompt: str
) -> Dict[str, Any]:
    """
    Main entry point for vision-based PDF processing.

    This function orchestrates the entire vision processing pipeline:
    1. Count pages and determine scanning strategy
    2. Convert PDF pages to images
    3. Encode images to base64
    4. Build vision API payload
    5. Call API and parse response

    Args:
        pdf_path: Path to the PDF file
        client: OpenAI client instance
        config: Configuration dictionary with processing_settings and api_settings
        system_prompt: System prompt for the AI model

    Returns:
        Parsed JSON response with extraction results

    Raises:
        FileNotFoundError: If PDF file doesn't exist
        Exception: If any step of the pipeline fails

    Workflow Summary:
    -----------------
    PDF → Page Count → Adaptive Strategy → Image Conversion → Base64 Encoding →
    Vision API Payload → API Call → JSON Parsing → Return Results
    """

    filename = os.path.basename(pdf_path)
    print(f"  📄 处理文件: {filename}")

    try:
        # Step 1: Get page count
        print(f"  📊 正在统计页数...")
        page_count = get_page_count(pdf_path)
        print(f"      总页数: {page_count}")

        # Step 2: Determine pages to process using adaptive strategy
        # Add pdf_path to config temporarily for get_smart_pages_to_process
        config_with_path = config.copy()
        config_with_path["pdf_path"] = pdf_path
        pages_to_process, strategy_desc = get_pages_to_process(page_count, config_with_path)
        print(f"  🎯 {strategy_desc}")
        print(f"      处理页码: {pages_to_process}")

        # Step 3: Convert PDF pages to images
        print(f"  🖼️  正在转换为图片...")
        processing_settings = config.get("processing_settings", {})
        dpi = processing_settings.get("image_dpi", 150)

        images = convert_pdf_to_images(
            pdf_path,
            page_numbers=pages_to_process,
            dpi=dpi,
            fmt='png'
        )
        print(f"      成功转换 {len(images)} 页为图片")

        # Step 4: Encode images to base64
        print(f"  🔐 正在编码图片...")
        encoded_images = encode_images_to_base64(images, format='PNG')
        print(f"      成功编码 {len(encoded_images)} 张图片")

        # Step 5: Build vision API payload
        print(f"  📨 正在构建API请求...")
        payload = build_vision_payload(
            encoded_images,
            system_prompt,
            user_message="请分析这些学术论文页面并提取CFST构件的试验数据。"
        )
        print(f"      请求包含 {len(encoded_images)} 张图片")

        # Step 6: Call vision API
        print(f"  🤖 正在调用AI模型...")
        api_settings = config.get("api_settings", {})
        model_name = api_settings.get("model_name")

        result = call_vision_api(
            client,
            payload,
            model_name,
            temperature=0.1,
            max_tokens=8192
        )

        print(f"  ✅ API调用成功！")
        return result

    except json.JSONDecodeError as e:
        # JSON parsing error - log detailed info to file, brief to console
        logger.error(f"❌ JSON解析失败: {filename}")
        logger.error(f"JSON解析错误详情: {str(e)}")
        logger.debug(f"截断内容预览: {e.doc[:500]}...")
        logger.exception("完整异常堆栈:")

        print(f"  ❌ JSON解析失败: {filename}")
        print(f"    错误: {str(e)}")
        if hasattr(e, 'doc'):
            print(f"    截断内容预览: {e.doc[:200]}...")
        raise

    except Exception as e:
        # General error - log to both console and file
        logger.error(f"处理失败: {filename} - {str(e)}")
        logger.exception("完整异常堆栈:")

        print(f"  ❌ 处理失败: {str(e)}")
        raise


