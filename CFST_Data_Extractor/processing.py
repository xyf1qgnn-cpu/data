"""
Intelligent text processing for PDF extraction (Workflow 2.0)
Based on requirements spec: 06-requirements-spec.md
"""

import re
from typing import List, Tuple


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


def optimize_text_for_extraction(text: str) -> str:
    """
    Optimize text for AI extraction by focusing on data-rich sections.

    Args:
        text: Original PDF text

    Returns:
        Optimized text
    """
    # Segment text
    segments = segment_pdf_text_intelligently(text, max_length=30000)

    # Score each segment for data richness
    scored_segments = []
    for segment in segments:
        score = 0

        # Higher score for beginning sections
        if re.search(r'(?i)\b(abstract|introduction|methodology)\b', segment):
            score += 10

        # Higher score for tables and figures
        if re.search(r'(?i)\b(table|figure)\s+\d+\b', segment):
            score += 20

        # Score based on numeric data presence
        numeric_count = len(re.findall(r'\b\d+\.\d+\b', segment))
        score += numeric_count * 0.5

        # Score based on unit presence
        unit_count = len(re.findall(r'\b(mm|MPa|kN)\b', segment))
        score += unit_count * 2

        scored_segments.append((score, segment))

    # Sort by score descending
    scored_segments.sort(key=lambda x: x[0], reverse=True)

    # Take top segments up to character limit
    optimized_text = ""
    char_limit = 50000
    for score, segment in scored_segments:
        if len(optimized_text) + len(segment) <= char_limit:
            if optimized_text:
                optimized_text += "\n\n" + segment
            else:
                optimized_text = segment
        else:
            # Add partial segment if needed
            remaining = char_limit - len(optimized_text)
            if remaining > 1000:  # Only add if significant space remains
                optimized_text += "\n\n" + segment[:remaining]
            break

    return optimized_text if optimized_text else text[:char_limit]