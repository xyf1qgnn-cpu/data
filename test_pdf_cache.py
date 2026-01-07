"""
Unit tests for PDF cache processing functionality

Test coverage:
- process_pdf with mode="extract_only" and mode="full"
- process_from_cache normal and failure scenarios
- archive_cache functionality
"""

import os
import sys
import pytest
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from processing import process_pdf, process_from_cache
from main import archive_cache
from config_manager import load_and_validate_config


class TestProcessPdfExtractOnly:
    """Test process_pdf with mode='extract_only'"""

    def test_extract_only_creates_cache_directory(self):
        """Test that extract_only mode creates cache directory"""
        # Setup
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock PDF with PIL
            pdf_path = os.path.join(tmpdir, "test.pdf")
            img = Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))
            img.save(pdf_path, "PDF", resolution=100)

            config = {
                "processing_settings": {
                    "image_dpi": 150,
                    "max_pages": 25
                },
                "api_settings": {
                    "model_name": "test-model"
                }
            }

            # Execute
            with patch('processing.convert_pdf_to_images') as mock_convert:
                # Mock image conversion
                mock_images = [Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))]
                mock_convert.return_value = mock_images

                result = process_pdf(pdf_path, None, config, "test prompt", mode="extract_only")

                # Verify
                assert result is not None
                assert "cache_dir" in result
                assert "image_paths" in result
                assert isinstance(result["cache_dir"], str)
                assert isinstance(result["image_paths"], list)

    def test_extract_only_returns_image_paths(self):
        """Test that extract_only mode returns correct image paths"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock PDF
            pdf_path = os.path.join(tmpdir, "test.pdf")
            img = Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))
            img.save(pdf_path, "PDF", resolution=100)

            config = {
                "processing_settings": {
                    "image_dpi": 150,
                    "max_pages": 25
                },
                "api_settings": {
                    "model_name": "test-model"
                }
            }

            with patch('processing.convert_pdf_to_images') as mock_convert:
                # Mock 2 pages
                mock_images = [
                    Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8)),
                    Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))
                ]
                mock_convert.return_value = mock_images

                result = process_pdf(pdf_path, None, config, "test prompt", mode="extract_only")

                # Verify we got 2 image paths
                assert len(result["image_paths"]) == 2
                for path in result["image_paths"]:
                    assert path.endswith(".jpg")

    def test_extract_only_does_not_call_api(self):
        """Test that extract_only mode doesn't call the API"""
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "test.pdf")
            img = Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))
            img.save(pdf_path, "PDF", resolution=100)

            config = {
                "processing_settings": {
                    "image_dpi": 150,
                    "max_pages": 25
                },
                "api_settings": {
                    "model_name": "test-model"
                }
            }

            with patch('processing.convert_pdf_to_images') as mock_convert:
                mock_images = [Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))]
                mock_convert.return_value = mock_images

                with patch('processing.call_vision_api') as mock_api:
                    result = process_pdf(pdf_path, None, config, "test prompt", mode="extract_only")

                    # Verify API was NOT called
                    mock_api.assert_not_called()
                    assert result is not None


class TestProcessPdfFullMode:
    """Test process_pdf with mode='full'"""

    def test_full_mode_returns_result_and_cache_dir(self):
        """Test that full mode returns result with data"""
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "test.pdf")
            img = Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))
            img.save(pdf_path, "PDF", resolution=100)

            config = {
                "processing_settings": {
                    "image_dpi": 150,
                    "max_pages": 25
                },
                "api_settings": {
                    "model_name": "test-model"
                }
            }

            with patch('processing.convert_pdf_to_images') as mock_convert:
                mock_images = [Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))]
                mock_convert.return_value = mock_images

                with patch('processing.call_vision_api') as mock_api:
                    # Mock successful API response
                    mock_api.return_value = {
                        "Group_A": [{"ref_no": "test", "fc_value": 30.5}]
                    }

                    result = process_pdf(pdf_path, None, config, "test prompt", mode="full")

                    # Verify
                    assert result is not None
                    assert "result" in result
                    assert "cache_dir" in result
                    assert result["result"]["Group_A"][0]["fc_value"] == 30.5

    def test_full_mode_calls_api(self):
        """Test that full mode calls the API"""
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "test.pdf")
            img = Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))
            img.save(pdf_path, "PDF", resolution=100)

            config = {
                "processing_settings": {
                    "image_dpi": 150,
                    "max_pages": 25
                },
                "api_settings": {
                    "model_name": "test-model"
                }
            }

            with patch('processing.convert_pdf_to_images') as mock_convert:
                mock_images = [Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))]
                mock_convert.return_value = mock_images

                with patch('processing.call_vision_api') as mock_api:
                    mock_api.return_value = {
                        "Group_A": [{"ref_no": "test", "fc_value": 30.5}]
                    }

                    process_pdf(pdf_path, None, config, "test prompt", mode="full")

                    # Verify API was called
                    mock_api.assert_called_once()

    def test_full_mode_handles_api_failure(self):
        """Test that full mode handles API failure gracefully"""
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "test.pdf")
            img = Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))
            img.save(pdf_path, "PDF", resolution=100)

            config = {
                "processing_settings": {
                    "image_dpi": 150,
                    "max_pages": 25
                },
                "api_settings": {
                    "model_name": "test-model"
                }
            }

            with patch('processing.convert_pdf_to_images') as mock_convert:
                mock_images = [Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))]
                mock_convert.return_value = mock_images

                with patch('processing.call_vision_api') as mock_api:
                    # Mock API failure
                    mock_api.return_value = None

                    result = process_pdf(pdf_path, None, config, "test prompt", mode="full")

                    # Verify None returned on failure
                    assert result is None


class TestProcessFromCache:
    """Test process_from_cache function"""

    def test_process_from_cache_success(self):
        """Test successful processing from cache"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = os.path.join(tmpdir, "test_cache")
            os.makedirs(cache_dir)

            # Create mock image files
            image_paths = []
            for i in range(2):
                img_path = os.path.join(cache_dir, f"{i+1}.jpg")
                img = Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))
                img.save(img_path, "JPEG")
                image_paths.append(img_path)

            config = {
                "api_settings": {
                    "model_name": "test-model"
                }
            }

            mock_client = Mock()

            with patch('processing.call_vision_api') as mock_api:
                # Mock successful API response
                mock_api.return_value = {
                    "Group_A": [{"ref_no": "test", "fc_value": 30.5}]
                }

                result = process_from_cache(
                    cache_dir=cache_dir,
                    pdf_name="test",
                    image_paths=image_paths,
                    client=mock_client,
                    config=config,
                    system_prompt="test prompt"
                )

                # Verify
                assert result is not None
                assert "Group_A" in result
                assert result["Group_A"][0]["fc_value"] == 30.5
                mock_api.assert_called_once()

    def test_process_from_cache_api_failure(self):
        """Test process_from_cache handles API failure"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = os.path.join(tmpdir, "test_cache")
            os.makedirs(cache_dir)

            # Create mock image file
            img_path = os.path.join(cache_dir, "1.jpg")
            img = Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))
            img.save(img_path, "JPEG")

            config = {
                "api_settings": {
                    "model_name": "test-model"
                }
            }

            mock_client = Mock()

            with patch('processing.call_vision_api') as mock_api:
                # Mock API failure
                mock_api.return_value = None

                result = process_from_cache(
                    cache_dir=cache_dir,
                    pdf_name="test",
                    image_paths=[img_path],
                    client=mock_client,
                    config=config,
                    system_prompt="test prompt"
                )

                # Verify None returned on failure
                assert result is None

    def test_process_from_cache_reads_images(self):
        """Test that process_from_cache correctly reads images from cache"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = os.path.join(tmpdir, "test_cache")
            os.makedirs(cache_dir)

            # Create test image with specific color
            img_path = os.path.join(cache_dir, "1.jpg")
            test_img = Image.fromarray(np.ones((50, 50, 3), dtype=np.uint8) * 128)
            test_img.save(img_path, "JPEG")

            config = {
                "api_settings": {
                    "model_name": "test-model"
                }
            }

            mock_client = Mock()

            with patch('processing.encode_images_to_base64') as mock_encode:
                with patch('processing.call_vision_api') as mock_api:
                    mock_api.return_value = {"Group_A": []}

                    process_from_cache(
                        cache_dir=cache_dir,
                        pdf_name="test",
                        image_paths=[img_path],
                        client=mock_client,
                        config=config,
                        system_prompt="test prompt"
                    )

                    # Verify encode_images_to_base64 was called
                    mock_encode.assert_called_once()
                    # Verify it was passed images (list)
                    args, _ = mock_encode.call_args
                    assert isinstance(args[0], list)
                    assert len(args[0]) == 1


class TestArchiveCache:
    """Test archive_cache function"""

    def test_archive_cache_creates_zip(self):
        """Test that archive_cache creates zip file successfully"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = os.path.join(tmpdir, "test_cache")
            os.makedirs(cache_dir)

            # Create test image in cache
            img_path = os.path.join(cache_dir, "1.jpg")
            img = Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))
            img.save(img_path, "JPEG")

            batch_num = 1
            pdf_name = "test_pdf"

            # Create fake archive base
            archive_base = os.path.join(tmpdir, "archive")
            os.makedirs(archive_base)

            # Mock load_and_validate_config
            with patch('main.load_and_validate_config') as mock_config:
                mock_config.return_value = {
                    "paths": {
                        "archive_destination": archive_base
                    }
                }

                result = archive_cache(cache_dir, pdf_name, batch_num)

                # Verify
                assert result is not None
                assert result.endswith("_images.zip")
                assert os.path.exists(result)

                # Verify cache was deleted
                assert not os.path.exists(cache_dir)

    def test_archive_cache_skips_existing_zip(self):
        """Test that archive_cache skips if zip already exists"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = os.path.join(tmpdir, "test_cache")
            os.makedirs(cache_dir)

            img_path = os.path.join(cache_dir, "1.jpg")
            img = Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))
            img.save(img_path, "JPEG")

            batch_num = 1
            pdf_name = "test_pdf"
            archive_base = os.path.join(tmpdir, "archive")
            os.makedirs(archive_base)

            with patch('main.load_and_validate_config') as mock_config:
                mock_config.return_value = {
                    "paths": {
                        "archive_destination": archive_base
                    }
                }

                # Create first archive
                result1 = archive_cache(cache_dir, pdf_name, batch_num)
                assert result1 is not None

                # Recreate cache
                os.makedirs(cache_dir)
                img.save(img_path, "JPEG")

                # Try to archive again (should skip)
                result2 = archive_cache(cache_dir, pdf_name, batch_num)
                assert result2 == result1  # Should return same path
                assert not os.path.exists(cache_dir)  # Should still delete cache

    def test_archive_cache_handles_failure(self):
        """Test that archive_cache handles failure gracefully"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = os.path.join(tmpdir, "test_cache")
            os.makedirs(cache_dir)

            img_path = os.path.join(cache_dir, "1.jpg")
            img = Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))
            img.save(img_path, "JPEG")

            batch_num = 1
            archive_base = os.path.join(tmpdir, "archive")
            os.makedirs(archive_base)

            with patch('main.load_and_validate_config') as mock_config:
                mock_config.return_value = {
                    "paths": {
                        "archive_destination": archive_base
                    }
                }

                with patch('shutil.make_archive') as mock_zip:
                    mock_zip.side_effect = Exception("Zip creation failed")

                    result = archive_cache(cache_dir, "test", batch_num)

                    # Verify failure handling
                    assert result is None
                    # Cache should still exist
                    assert os.path.exists(cache_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
