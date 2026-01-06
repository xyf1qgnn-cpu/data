"""
Unit tests for smart page selection logic
Tests the get_smart_pages_to_process() function with mocked dependencies
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, MagicMock
import pytest
from processing import get_smart_pages_to_process, get_pages_to_process


@pytest.fixture
def mock_config():
    """Mock configuration with smart filtering enabled"""
    return {
        "processing_settings": {
            "short_paper_threshold": 10,
            "page_filtering": {
                "max_selected_pages": 8,
                "mandatory_include_first_page": True,
                "weights": {
                    "table_weight": 10,
                    "data_weight": 5,
                    "reference_weight": -5,
                    "base_weight": 1
                },
                "patterns": {
                    "table_patterns": [r'(?i)Table\s+\d+'],
                    "data_patterns": [r'(?i)Specimen'],
                    "reference_patterns": [r'(?i)References?']
                }
            }
        }
    }


class TestSmartPageSelection:
    """Test smart page selection logic"""

    @patch('processing.extract_page_texts')
    def test_short_paper_bypasses_filtering(self, mock_extract, mock_config):
        """Short papers (≤10 pages) should process all pages"""
        # Mock PDF with 8 pages
        mock_extract.return_value = {
            i: f"Page {i} content" for i in range(1, 9)
        }

        pages, desc, info = get_smart_pages_to_process("test.pdf", mock_config)

        # Should process all 8 pages
        assert len(pages) == 8
        assert 1 in pages and 8 in pages
        assert "短论文" in desc or "10页" in desc

    @patch('processing.extract_page_texts')
    def test_long_paper_uses_smart_filtering(self, mock_extract, mock_config):
        """Long papers (>10 pages) should use smart filtering"""
        # Mock PDF with 20 pages
        page_texts = {
            i: f"Page {i} content" for i in range(1, 21)
        }

        # Give some pages high scores
        page_texts[5] = "Table 1: Results for Specimen A-1"
        page_texts[8] = "Table 2: Test data"
        page_texts[12] = "Table 3: Additional results"

        mock_extract.return_value = page_texts

        pages, desc, info = get_smart_pages_to_process("test.pdf", mock_config)

        # Should process ≤ max_selected_pages (8)
        assert len(pages) <= 8
        # Should include page 1 (mandatory)
        assert 1 in pages
        # Should use smart filtering
        assert "智能筛选" in desc or "smart" in desc.lower()

    @patch('processing.extract_page_texts')
    def test_mandatory_first_page(self, mock_extract, mock_config):
        """Page 1 should always be included if configured"""
        mock_extract.return_value = {
            i: f"Page {i} content" for i in range(1, 101)
        }

        pages, desc, info = get_smart_pages_to_process("test.pdf", mock_config)

        assert 1 in pages, "Page 1 should be included"
        # Check debug info for reason
        page1_info = next((item for item in info if item["page"] == 1), None)
        assert page1_info is not None
        assert "强制包含" in page1_info["reason"] or "mandatory" in page1_info["reason"]

    @patch('processing.extract_page_texts')
    def test_negative_scores_excluded(self, mock_extract, mock_config):
        """Pages with negative scores should be excluded"""
        page_texts = {}
        for i in range(1, 21):
            if i >= 15:  # Last pages are references
                page_texts[i] = "References: [1, 2, 3, 4, 5]"
            else:
                page_texts[i] = f"Normal content for page {i}"

        mock_extract.return_value = page_texts

        pages, desc, info = get_smart_pages_to_process("test.pdf", mock_config)

        # Should not include reference pages (15+)
        assert all(p < 15 for p in pages), f"Should not include reference pages, got {pages}"

    @patch('processing.extract_page_texts')
    def test_debug_info_provided(self, mock_extract, mock_config):
        """Debug info should include scores and reasons for each selected page"""
        mock_extract.return_value = {
            i: f"Page content {i}" if i > 1 else "Table 1: Results"
            for i in range(1, 51)
        }

        pages, desc, info = get_smart_pages_to_process("test.pdf", mock_config)

        assert len(info) == len(pages), "Debug info should match selected pages"
        for debug_item in info:
            assert "page" in debug_item
            assert "score" in debug_item
            assert "reason" in debug_item
            assert debug_item["page"] in pages


class TestSmartFilteringDisabled:
    """Test behavior when smart filtering is disabled"""

    @patch('processing.extract_page_texts')
    @patch('processing.get_page_count')
    def test_fallback_when_disabled(self, mock_count, mock_extract):
        """Should use simple truncation when smart filtering is disabled"""
        config = {
            "processing_settings": {
                "short_paper_threshold": 10,
                "max_scan_limit": 10,
                "enable_smart_filtering": False,  # DISABLED
            }
        }

        mock_count.return_value = 50
        config["pdf_path"] = "test.pdf"

        pages, desc = get_pages_to_process(50, config)

        # Should use simple truncation
        assert "截断" in desc or "truncat" in desc.lower()
        assert len(pages) <= 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
