"""Tests for OCR preprocessing module."""

import numpy as np
import pytest

from app.core.ocr.preprocessing import (
    ImagePreprocessor,
    ProcessedImage,
    QualityScore,
)


class TestQualityScore:
    """Tests for QualityScore dataclass."""

    def test_is_high_quality_above_threshold(self):
        """Test high quality detection above threshold."""
        score = QualityScore(
            sharpness=200.0,
            contrast=0.8,
            noise_level=0.2,
            text_density=0.5,
            overall_score=0.85,
            recommended_engine="tesseract",
        )
        assert score.is_high_quality(threshold=0.7) is True

    def test_is_high_quality_below_threshold(self):
        """Test high quality detection below threshold."""
        score = QualityScore(
            sharpness=50.0,
            contrast=0.3,
            noise_level=0.6,
            text_density=0.3,
            overall_score=0.4,
            recommended_engine="gpt4_vision",
        )
        assert score.is_high_quality(threshold=0.7) is False

    def test_is_high_quality_at_threshold(self):
        """Test high quality detection at exact threshold."""
        score = QualityScore(
            sharpness=100.0,
            contrast=0.5,
            noise_level=0.3,
            text_density=0.4,
            overall_score=0.7,
            recommended_engine="tesseract",
        )
        assert score.is_high_quality(threshold=0.7) is True


class TestImagePreprocessor:
    """Tests for ImagePreprocessor class."""

    @pytest.fixture
    def preprocessor(self):
        """Create preprocessor instance."""
        return ImagePreprocessor(quality_threshold=0.7)

    @pytest.fixture
    def sample_grayscale_image(self):
        """Create a sample grayscale image."""
        # Create a simple test image with some structure
        image = np.zeros((100, 100), dtype=np.uint8)
        # Add some text-like patterns
        image[20:30, 10:90] = 255  # Horizontal line
        image[40:50, 10:90] = 255  # Another line
        image[60:70, 10:90] = 255  # Another line
        return image

    @pytest.fixture
    def sample_color_image(self):
        """Create a sample color image."""
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        image[20:30, 10:90] = [255, 255, 255]
        image[40:50, 10:90] = [255, 255, 255]
        return image

    def test_assess_quality_grayscale(self, preprocessor, sample_grayscale_image):
        """Test quality assessment on grayscale image."""
        score = preprocessor.assess_quality(sample_grayscale_image)

        assert isinstance(score, QualityScore)
        assert 0 <= score.overall_score <= 1
        assert score.sharpness >= 0
        assert 0 <= score.contrast <= 1
        assert 0 <= score.noise_level <= 1
        assert 0 <= score.text_density <= 1
        assert score.recommended_engine in ["tesseract", "gpt4_vision"]

    def test_assess_quality_color(self, preprocessor, sample_color_image):
        """Test quality assessment on color image."""
        score = preprocessor.assess_quality(sample_color_image)

        assert isinstance(score, QualityScore)
        assert 0 <= score.overall_score <= 1

    def test_to_grayscale(self, preprocessor, sample_color_image):
        """Test grayscale conversion."""
        gray = preprocessor._to_grayscale(sample_color_image)

        assert len(gray.shape) == 2
        assert gray.shape == (100, 100)

    def test_to_grayscale_already_gray(self, preprocessor, sample_grayscale_image):
        """Test grayscale conversion on already grayscale image."""
        gray = preprocessor._to_grayscale(sample_grayscale_image)

        assert len(gray.shape) == 2
        np.testing.assert_array_equal(gray, sample_grayscale_image)

    def test_remove_noise(self, preprocessor, sample_grayscale_image):
        """Test noise removal."""
        denoised = preprocessor._remove_noise(sample_grayscale_image)

        assert denoised.shape == sample_grayscale_image.shape
        assert denoised.dtype == sample_grayscale_image.dtype

    def test_enhance_contrast(self, preprocessor, sample_grayscale_image):
        """Test contrast enhancement."""
        enhanced = preprocessor._enhance_contrast(sample_grayscale_image)

        assert enhanced.shape == sample_grayscale_image.shape
        assert enhanced.dtype == sample_grayscale_image.dtype

    def test_binarize(self, preprocessor, sample_grayscale_image):
        """Test binarization."""
        binary = preprocessor._binarize(sample_grayscale_image)

        assert binary.shape == sample_grayscale_image.shape
        # Binary image should only have 0 and 255 values
        unique_values = np.unique(binary)
        assert all(v in [0, 255] for v in unique_values)

    def test_calculate_sharpness(self, preprocessor, sample_grayscale_image):
        """Test sharpness calculation."""
        sharpness = preprocessor._calculate_sharpness(sample_grayscale_image)

        assert isinstance(sharpness, float)
        assert sharpness >= 0

    def test_calculate_contrast(self, preprocessor, sample_grayscale_image):
        """Test contrast calculation."""
        contrast = preprocessor._calculate_contrast(sample_grayscale_image)

        assert isinstance(contrast, float)
        assert 0 <= contrast <= 1

    def test_estimate_noise(self, preprocessor, sample_grayscale_image):
        """Test noise estimation."""
        noise = preprocessor._estimate_noise(sample_grayscale_image)

        assert isinstance(noise, float)
        assert 0 <= noise <= 1

    def test_estimate_text_density(self, preprocessor, sample_grayscale_image):
        """Test text density estimation."""
        density = preprocessor._estimate_text_density(sample_grayscale_image)

        assert isinstance(density, float)
        assert 0 <= density <= 1

    def test_preprocess_array(self, preprocessor, sample_grayscale_image):
        """Test preprocessing from numpy array."""
        result = preprocessor.preprocess_array(sample_grayscale_image)

        assert isinstance(result, ProcessedImage)
        assert result.image is not None
        assert result.original_path is None
        assert isinstance(result.quality_score, QualityScore)
        assert isinstance(result.preprocessing_applied, list)

    def test_preprocess_array_with_options(self, preprocessor, sample_grayscale_image):
        """Test preprocessing with specific options."""
        result = preprocessor.preprocess_array(
            sample_grayscale_image,
            apply_deskew=False,
            apply_denoise=True,
            apply_contrast=True,
            apply_binarize=True,
        )

        assert isinstance(result, ProcessedImage)
        assert "denoise" in result.preprocessing_applied
        assert "contrast_enhance" in result.preprocessing_applied
        assert "binarize" in result.preprocessing_applied

    def test_preprocess_file_not_found(self, preprocessor):
        """Test preprocessing with non-existent file."""
        with pytest.raises(FileNotFoundError):
            preprocessor.preprocess("/nonexistent/path/image.png")

    def test_deskew_no_lines(self, preprocessor):
        """Test deskew with image containing no lines."""
        # Create blank image
        blank = np.zeros((100, 100), dtype=np.uint8)
        deskewed, angle = preprocessor._deskew(blank)

        assert angle == 0.0
        np.testing.assert_array_equal(deskewed, blank)

    def test_engine_recommendation_high_quality(self, preprocessor):
        """Test engine recommendation for high quality image."""
        # Create a high-contrast, sharp image
        image = np.zeros((200, 200), dtype=np.uint8)
        # Add clear text-like patterns
        for i in range(5):
            y = 20 + i * 30
            image[y:y+10, 20:180] = 255

        score = preprocessor.assess_quality(image)

        # High quality images should recommend tesseract
        if score.overall_score >= 0.7:
            assert score.recommended_engine == "tesseract"

    def test_engine_recommendation_low_quality(self, preprocessor):
        """Test engine recommendation for low quality image."""
        # Create a noisy, low-contrast image
        image = np.random.randint(100, 150, (100, 100), dtype=np.uint8)

        score = preprocessor.assess_quality(image)

        # Low quality images should recommend gpt4_vision
        if score.overall_score < 0.7:
            assert score.recommended_engine == "gpt4_vision"
