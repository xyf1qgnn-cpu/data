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
            # Log API request summary (file only) - optimize by not logging base64 content
            image_count = len([item for item in payload["messages"][1]["content"] if item["type"] == "image_url"])
            logger.debug(f"API请求 - 模型: {model_name}, 图片: {image_count}, max_tokens: {max_tokens}")
            # Note: Full payload with base64 excluded to reduce log size

            # Make API call
            logger.info("🤖 正在调用AI模型...")
            response = client.chat.completions.create(**payload)

            # Extract the response text
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content

                # Log API response (file only) - optimize for large responses
                logger.debug(f"API响应长度: {len(content)} 字符")
                if len(content) > 1000:
                    logger.debug(f"响应预览: {content[:500]}...")
                else:
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
    system_prompt: str,
    mode: str = "full"
) -> Optional[Dict[str, Any]]:
    """
    Main entry point for vision-based PDF processing with cache support.

    This function orchestrates the entire vision processing pipeline:
    1. Count pages and determine scanning strategy
    2. Convert PDF pages to images
    3. Save to cache (if mode='extract_only') or encode and call API (if mode='full')

    Args:
        pdf_path: Path to the PDF file
        client: OpenAI client instance
        config: Configuration dictionary with processing_settings and api_settings
        system_prompt: System prompt for the AI model
        mode: Processing mode
            - "full" (default): Complete processing with API call
            - "extract_only": Only extract and save images to cache

    Returns:
        mode="extract_only": {"cache_dir": str, "image_paths": List[str]}
        mode="full": {"result": Dict[str, Any], "cache_dir": str}
        None: If processing fails

    Raises:
        FileNotFoundError: If PDF file doesn't exist

    Workflow Summary:
    -----------------
    PDF → Page Count → Page Selection → Image Conversion → [Cache Save] →
    [Base64 Encoding → API Call → JSON Parsing] → Return Results
    """

    filename = os.path.basename(pdf_path)
    print(f"  📄 处理文件: {filename}")

    try:
        # Step 1: Get page count
        print(f"  📊 正在统计页数...")
        page_count = get_page_count(pdf_path)
        print(f"      总页数: {page_count}")

        # Step 2: Determine pages to process
        # Determine max_pages from config (default 25)
        max_pages = config.get('processing_settings', {}).get('max_pages', 25)

        if page_count > max_pages:
            print(f"  ⚠️  PDF页数({page_count})超过最大限制({max_pages})")
            print(f"      将只处理前{max_pages}页")
            pages_to_process = list(range(1, min(max_pages, page_count)))
        elif page_count > 1:
            # Process all pages except last (exclude references)
            pages_to_process = list(range(1, page_count))
        else:
            pages_to_process = [1]

        print(f"      处理页码: {pages_to_process}")

        # Step 3: Convert PDF pages to images
        print(f"  🖼️  正在提取图片并保存到cache...")
        processing_settings = config.get("processing_settings", {})
        dpi = processing_settings.get("image_dpi", 150)

        images = convert_pdf_to_images(
            pdf_path,
            page_numbers=pages_to_process,
            dpi=dpi,
            fmt='jpeg'  # Changed to JPEG for cache
        )
        print(f"      成功提取 {len(images)} 页为图片")

        # Step 4: Save to cache
        pdf_name = os.path.splitext(filename)[0]
        cache_dir = os.path.join("./cache", pdf_name)
        os.makedirs(cache_dir, exist_ok=True)

        image_paths = []
        for page_num, image in zip(pages_to_process, images):
            image_path = os.path.join(cache_dir, f"{page_num}.jpg")
            # Save as JPEG with quality 95
            image.save(image_path, 'JPEG', quality=95)
            image_paths.append(image_path)

        print(f"      已保存到 cache: {cache_dir}")

        # If extract_only mode, return cache info
        if mode == "extract_only":
            return {"cache_dir": cache_dir, "image_paths": image_paths}

        # Step 5: Encode images for API (for full mode)
        print(f"  🔐 正在编码图片...")
        # Read images from cache for encoding
        cache_images = [Image.open(path) for path in image_paths]
        encoded_images = encode_images_to_base64(cache_images, format='JPEG')
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
        processing_settings = config.get("processing_settings", {})
        max_tokens = processing_settings.get("max_tokens", 8192)

        result = call_vision_api(
            client,
            payload,
            model_name,
            temperature=0.1,
            max_tokens=max_tokens
        )

        if result:
            print(f"  ✅ API调用成功！")
            return {"result": result, "cache_dir": cache_dir}
        else:
            print(f"  ❌ API调用失败")
            return None

    except Exception as e:
        # General error - log to both console and file
        logger.error(f"处理失败: {filename} - {str(e)}")
        logger.exception("完整异常堆栈:")

        print(f"  ❌ 处理失败: {str(e)}")
        return None


def process_from_cache(
    cache_dir: str,
    pdf_name: str,
    image_paths: List[str],
    client,
    config: Dict[str, Any],
    system_prompt: str
) -> Optional[Dict[str, Any]]:
    """
    第二阶段：从cache读取图片并调用API

    Args:
        cache_dir: cache目录路径（用于日志）
        pdf_name: PDF文件名（用于日志和错误报告）
        image_paths: 图片文件路径列表
        client: OpenAI客户端
        config: 配置字典
        system_prompt: 系统提示词

    Returns:
        提取的数据字典（成功）或 None（失败）
    """
    print(f"  📂 从cache读取: {os.path.basename(cache_dir)}")
    print(f"      图片数: {len(image_paths)}")

    try:
        # Read images from cache
        images = []
        for path in image_paths:
            img = Image.open(path)
            images.append(img)

        # Encode images to base64
        encoded_images = encode_images_to_base64(images, format='JPEG')

        # Build vision API payload
        payload = build_vision_payload(
            encoded_images,
            system_prompt,
            user_message="请分析这些学术论文页面并提取CFST构件的试验数据。"
        )

        # Call vision API
        api_settings = config.get("api_settings", {})
        model_name = api_settings.get("model_name")
        processing_settings = config.get("processing_settings", {})
        max_tokens = processing_settings.get("max_tokens", 8192)

        result = call_vision_api(
            client,
            payload,
            model_name,
            temperature=0.1,
            max_tokens=max_tokens
        )

        if result:
            print(f"  ✅ 从cache处理成功！")
        else:
            print(f"  ❌ 从cache处理失败")

        return result

    except Exception as e:
        logger.error(f"从cache处理失败: {pdf_name} - {str(e)}")
        logger.exception("完整异常堆栈:")

        print(f"  ❌ 从cache处理失败: {str(e)}")
        return None


