"""
Unit tests for page scoring algorithm
Tests the score_page_content() function in isolation
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from processing import score_page_content


@pytest.fixture
def mock_config():
    """Mock configuration with page filtering settings"""
    return {
        "processing_settings": {
            "page_filtering": {
                "weights": {
                    "table_weight": 10,
                    "data_weight": 5,
                    "reference_weight": -5,
                    "base_weight": 1
                },
                "patterns": {
                    "table_patterns": [
                        r'(?i)Table\s+\d+',
                        r'(?i)Tab\.\s*\d+'
                    ],
                    "data_patterns": [
                        r'(?i)Specimen',
                        r'(?i)Experimental',
                        r'\d+\.\d+\s*mm'
                    ],
                    "reference_patterns": [
                        r'(?i)References?',
                        r'\[[\d,\s]+\]'
                    ]
                }
            }
        }
    }


class TestPageScoring:
    """Test cases for page content scoring"""

    def test_empty_text(self, mock_config):
        """Empty text should return 0"""
        assert score_page_content("", mock_config) == 0

    def test_whitespace_only(self, mock_config):
        """Whitespace-only text should return 0"""
        assert score_page_content("   \n\t  ", mock_config) == 0

    def test_table_detection(self, mock_config):
        """Table titles should add +10 points each"""
        text = "Table 1: Experimental Results"
        score = score_page_content(text, mock_config)
        assert score >= 10  # At least table weight

    def test_multiple_tables(self, mock_config):
        """Multiple tables should accumulate score"""
        text = "Table 1: Results\nTable 2: Dimensions"
        score = score_page_content(text, mock_config)
        assert score >= 20  # Two tables

    def test_data_keywords(self, mock_config):
        """Data keywords should add +5 points each"""
        text = "Specimen C-1 had experimental data"
        score = score_page_content(text, mock_config)
        assert score >= 5  # At least one data keyword

    def test_reference_patterns(self, mock_config):
        """Reference patterns should subtract -5 points"""
        text = "References: [1, 2, 3]"
        score = score_page_content(text, mock_config)
        assert score <= -5  # Negative due to references

    def test_mixed_content(self, mock_config):
        """Mixed content with both positive and negative patterns"""
        text = "Table 1: Results for Specimen A-1. References: [1]"
        score = score_page_content(text, mock_config)
        # Table (+10) + Specimen (+5) - Reference (-5) = +10 (approximately)
        # Note: Base score adds +1 per 10 words, so actual will be slightly higher
        assert score >= 6  # At least Table + Specimen - Reference

    def test_base_score(self, mock_config):
        """Normal text should get base score +1 per 10 words"""
        text = "This is a normal paragraph with many words that should generate a base score. " * 20
        score = score_page_content(text, mock_config)
        assert score >= 1  # At least base score

    def test_unicode_chinese(self, mock_config):
        """Should handle Chinese text correctly"""
        text = "试验试件 Table 1: 结果数据"
        score = score_page_content(text, mock_config)
        assert score >= 10  # Should detect "Table 1"

    def test_performance_benchmark(self, mock_config):
        """Scoring should be fast (<1ms per page)"""
        text = "Table 1: Specimen Data\n\n" + "Normal text. " * 100
        import time

        start = time.time()
        score = score_page_content(text, mock_config)
        elapsed = time.time() - start

        assert elapsed < 0.001  # Less than 1ms
        assert score > 0

    def test_regex_edge_cases(self, mock_config):
        """Test edge cases in regex matching"""
        # Case variations
        text = "TABLE 1, Tab. 2, table 3"
        score = score_page_content(text, mock_config)
        assert score >= 30  # Three tables

    def test_table_abbreviations(self, mock_config):
        """Test table abbreviation patterns"""
        text = "Tab. 1 shows the results. Tab. 2 shows comparisons."
        score = score_page_content(text, mock_config)
        assert score >= 20  # Two abbreviated tables

    def test_case_sensitivity(self, mock_config):
        """Patterns should be case-insensitive"""
        text = "TABLE 1: SPECIMEN DATA"
        score = score_page_content(text, mock_config)
        assert score >= 15  # Table + Specimen

    def test_zero_score_content(self, mock_config):
        """Content without patterns should still get base score"""
        text = "This is normal text without any special keywords."
        score = score_page_content(text, mock_config)
        assert score >= 1  # Base score for non-empty content


class TestScoringConfigurability:
    """Test that scoring is properly configurable"""

    def test_custom_weights(self):
        """Custom weights should affect scoring"""
        config = {
            "processing_settings": {
                "page_filtering": {
                    "weights": {
                        "table_weight": 20,  # Double the default
                        "data_weight": 5,
                        "reference_weight": -5,
                        "base_weight": 1
                    },
                    "patterns": {
                        "table_patterns": [r'(?i)Table\s+\d+'],
                        "data_patterns": [],
                        "reference_patterns": []
                    }
                }
            }
        }

        text = "Table 1: Results"
        score = score_page_content(text, config)
        assert score >= 20  # Should use custom weight

    def test_custom_patterns(self):
        """Custom patterns should be used for matching"""
        config = {
            "processing_settings": {
                "page_filtering": {
                    "weights": {
                        "table_weight": 10,
                        "data_weight": 5,
                        "reference_weight": -5,
                        "base_weight": 1
                    },
                    "patterns": {
                        "data_patterns": [r'CUSTOM_KEYWORD'],  # Custom pattern
                        "table_patterns": [],
                        "reference_patterns": []
                    }
                }
            }
        }

        text = "CUSTOM_KEYWORD appears in text"
        score = score_page_content(text, config)
        assert score >= 5  # Should match custom pattern


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
