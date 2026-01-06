"""
Unit tests for JSON parsing and truncation detection
Tests the parse_ai_response() function
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import pytest
from processing import parse_ai_response


class TestJSONParsing:
    """Test JSON parsing with various formats"""

    def test_valid_json_parsing(self):
        """Should parse valid JSON correctly"""
        response = '{"is_valid": true, "reason": "", "Group_A": []}'
        result = parse_ai_response(response)
        assert result == {"is_valid": True, "reason": "", "Group_A": []}

    def test_json_with_markdown_blocks(self):
        """Should handle JSON wrapped in markdown code blocks"""
        response = '```json\n{"is_valid": true, "reason": ""}\n```'
        result = parse_ai_response(response)
        assert result == {"is_valid": True, "reason": ""}

    def test_json_with_triple_backticks(self):
        """Should handle JSON wrapped in triple backticks without language"""
        response = '```\n{"is_valid": false, "Group_A": []}\n```'
        result = parse_ai_response(response)
        assert result == {"is_valid": False, "Group_A": []}

    def test_nested_json_structure(self):
        """Should handle nested JSON structures"""
        response = '''{
            "is_valid": true,
            "reason": "",
            "Group_A": [
                {"specimen_label": "C-1", "fc_value": 35},
                {"specimen_label": "C-2", "fc_value": 40}
            ]
        }'''
        result = parse_ai_response(response)
        assert result["is_valid"] is True
        assert len(result["Group_A"]) == 2
        assert result["Group_A"][0]["specimen_label"] == "C-1"

    def test_empty_json_object(self):
        """Should handle empty JSON object"""
        response = '{}'
        result = parse_ai_response(response)
        assert result == {}


class TestTruncationDetection:
    """Test detection of truncated JSON responses"""

    def test_unclosed_braces(self):
        """Should detect unclosed braces"""
        response = '{"is_valid": true, "Group_A": [{'
        with pytest.raises(json.JSONDecodeError) as exc_info:
            parse_ai_response(response)
        assert "truncated" in str(exc_info.value).lower() or "unclosed" in str(exc_info.value).lower()

    def test_truncated_in_middle_of_string(self):
        """Should detect truncation in middle of string value"""
        response = '{"reason": "Not experimental CFST column paper}'
        with pytest.raises(json.JSONDecodeError):
            parse_ai_response(response)

    def test_nested_unclosed_braces(self):
        """Should detect unclosed braces in nested structures"""
        response = '{"is_valid": true, "Group_A": [{"label": "C-1"}'
        with pytest.raises(json.JSONDecodeError):
            parse_ai_response(response)


class TestMarkdownTruncationScenarios:
    """Test real-world truncation scenarios from API responses"""

    def test_incomplete_markdown_block(self):
        """Should handle incomplete markdown code blocks"""
        response = '```json\n{"is_valid": true, "reason": "Too long explanation'
        with pytest.raises(json.JSONDecodeError):
            parse_ai_response(response)


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_malformed_json(self):
        """Should raise error for malformed JSON"""
        response = '{is_valid: true, reason: "wrong format"}'
        with pytest.raises(json.JSONDecodeError):
            parse_ai_response(response)

    def test_invalid_json_syntax(self):
        """Should handle various JSON syntax errors"""
        response = '{"is_valid": true,,,}'
        with pytest.raises(json.JSONDecodeError):
            parse_ai_response(response)

    def test_empty_string(self):
        """Should handle empty string gracefully"""
        response = ''
        with pytest.raises(json.JSONDecodeError):
            parse_ai_response(response)

    def test_whitespace_only(self):
        """Should handle whitespace-only response"""
        response = '   \n\t  '
        with pytest.raises(json.JSONDecodeError):
            parse_ai_response(response)


class TestRealWorldScenarios:
    """Test real-world response scenarios"""

    def test_complete_valid_response(self):
        """Simulate a complete valid AI response"""
        response = '{"is_valid": true, "reason": "", "Group_A": [{"ref_no": "", "specimen_label": "C-1", "fc_value": 35.2, "fc_type": "Cube 150", "fy": 345}], "Group_B": [], "Group_C": []}'
        result = parse_ai_response(response)
        assert result["is_valid"] is True
        assert result["reason"] == ""
        assert len(result["Group_A"]) == 1

    def test_invalid_rejection_response(self):
        """Simulate a rejection response"""
        response = '{"is_valid": false, "reason": "Not CFST", "Group_A": [], "Group_B": [], "Group_C": []}'
        result = parse_ai_response(response)
        assert result["is_valid"] is False
        assert result["reason"] == "Not CFST"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
