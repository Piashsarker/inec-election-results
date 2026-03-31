"""Image preprocessing for optimal OCR performance.

This module provides image preprocessing capabilities to enhance OCR accuracy
on election result sheet images. It includes grayscale conversion, deskewing,
noise removal, contrast enhancement, and quality assessment.

Requirements: 3.1
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Tuple, Union

import cv2
import numpy as np
from PIL import Image


class ImageFormat(str, Enum):
    """Supported image formats."""
    
    PNG = "png"
    JPEG = "jpeg"
    PDF = "pdf"


@dataclass
class QualityScore:
    """Image quality assessment result for OCR engine selection.
    
    Attributes:
        sharpness: Laplacian variance measuring image sharpness (0-1000+)
        contrast: Contrast ratio of the image (0-1)
        noise_level: Estimated noise level (0-1, lower is better)
        text_density: Estimated text density in the image (0-1)
        overall_score: Combined quality score (0-1)
        recommended_engine: Suggested OCR engine based on quality
    """
    
    sharpness: float
    contrast: float
    noise_level: float
    text_density: float
    overall_score: float
    recommended_engine: str
    
    def is_high_quality(self, threshold: float = 0.7) -> bool:
        """Check if image quality is above threshold."""
        return self.overall_score >= threshold


@dataclass
class ProcessedImage:
    """Result of image preprocessing.
    
    Attributes:
        image: Preprocessed image as numpy array
        original_path: Path to the original image
        quality_score: Quality assessment of the preprocessed image
        preprocessing_applied: List of preprocessing steps applied
        deskew_angle: Rotation angle applied for deskewing (degrees)
    """
    
    image: np.ndarray
    original_path: Optional[str]
    quality_score: QualityScore
    preprocessing_applied: list[str]
    deskew_angle: float


class ImagePreprocessor:
    """Preprocesses images for optimal OCR performance.
    
    This class implements a preprocessing pipeline that includes:
    1. Grayscale conversion
    2. Deskew (rotation correction)
    3. Noise removal (Gaussian blur + thresholding)
    4. Contrast enhancement (CLAHE)
    5. Binarization (Otsu's method)
    
    The quality assessment helps determine which OCR engine to use:
    - High quality images -> Tesseract (faster, good for clean documents)
    - Low quality/handwritten -> GPT-4 Vision (better understanding)
    
    Requirements: 3.1
    """
    
    # Quality thresholds for engine selection
    HIGH_QUALITY_THRESHOLD = 0.7
    SHARPNESS_THRESHOLD = 100.0
    CONTRAST_THRESHOLD = 0.3
    NOISE_THRESHOLD = 0.3
    
    def __init__(
        self,
        quality_threshold: float = 0.7,
        clahe_clip_limit: float = 2.0,
        clahe_tile_size: Tuple[int, int] = (8, 8),
        gaussian_kernel_size: int = 5,
        denoise_strength: int = 10,
    ):
        """Initialize the image preprocessor.
        
        Args:
            quality_threshold: Threshold for high/low quality classification
            clahe_clip_limit: Clip limit for CLAHE contrast enhancement
            clahe_tile_size: Tile grid size for CLAHE
            gaussian_kernel_size: Kernel size for Gaussian blur
            denoise_strength: Strength parameter for denoising
        """
        self.quality_threshold = quality_threshold
        self.clahe_clip_limit = clahe_clip_limit
        self.clahe_tile_size = clahe_tile_size
        self.gaussian_kernel_size = gaussian_kernel_size
        self.denoise_strength = denoise_strength
    
    def preprocess(
        self,
        image_path: Union[str, Path],
        apply_deskew: bool = True,
        apply_denoise: bool = True,
        apply_contrast: bool = True,
        apply_binarize: bool = False,
    ) -> ProcessedImage:
        """Apply preprocessing pipeline to an image.
        
        Steps:
        1. Load and convert to grayscale
        2. Deskew (correct rotation)
        3. Remove noise (Gaussian blur + threshold)
        4. Enhance contrast (CLAHE)
        5. Optionally binarize (Otsu's method)
        
        Args:
            image_path: Path to the input image
            apply_deskew: Whether to apply deskew correction
            apply_denoise: Whether to apply noise removal
            apply_contrast: Whether to apply contrast enhancement
            apply_binarize: Whether to apply binarization
            
        Returns:
            ProcessedImage with preprocessed image and metadata
            
        Raises:
            FileNotFoundError: If image file doesn't exist
            ValueError: If image cannot be loaded
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Load image
        image = self._load_image(image_path)
        if image is None:
            raise ValueError(f"Failed to load image: {image_path}")
        
        preprocessing_applied = []
        deskew_angle = 0.0
        
        # Step 1: Convert to grayscale
        if len(image.shape) == 3:
            image = self._to_grayscale(image)
            preprocessing_applied.append("grayscale")
        
        # Step 2: Deskew
        if apply_deskew:
            image, deskew_angle = self._deskew(image)
            if abs(deskew_angle) > 0.1:
                preprocessing_applied.append(f"deskew({deskew_angle:.2f}°)")
        
        # Step 3: Denoise
        if apply_denoise:
            image = self._remove_noise(image)
            preprocessing_applied.append("denoise")
        
        # Step 4: Contrast enhancement
        if apply_contrast:
            image = self._enhance_contrast(image)
            preprocessing_applied.append("contrast_enhance")
        
        # Step 5: Binarization (optional)
        if apply_binarize:
            image = self._binarize(image)
            preprocessing_applied.append("binarize")
        
        # Assess quality
        quality_score = self.assess_quality(image)
        
        return ProcessedImage(
            image=image,
            original_path=str(image_path),
            quality_score=quality_score,
            preprocessing_applied=preprocessing_applied,
            deskew_angle=deskew_angle,
        )
    
    def preprocess_array(
        self,
        image: np.ndarray,
        apply_deskew: bool = True,
        apply_denoise: bool = True,
        apply_contrast: bool = True,
        apply_binarize: bool = False,
    ) -> ProcessedImage:
        """Apply preprocessing pipeline to a numpy array image.
        
        Args:
            image: Input image as numpy array
            apply_deskew: Whether to apply deskew correction
            apply_denoise: Whether to apply noise removal
            apply_contrast: Whether to apply contrast enhancement
            apply_binarize: Whether to apply binarization
            
        Returns:
            ProcessedImage with preprocessed image and metadata
        """
        preprocessing_applied = []
        deskew_angle = 0.0
        
        # Step 1: Convert to grayscale
        if len(image.shape) == 3:
            image = self._to_grayscale(image)
            preprocessing_applied.append("grayscale")
        
        # Step 2: Deskew
        if apply_deskew:
            image, deskew_angle = self._deskew(image)
            if abs(deskew_angle) > 0.1:
                preprocessing_applied.append(f"deskew({deskew_angle:.2f}°)")
        
        # Step 3: Denoise
        if apply_denoise:
            image = self._remove_noise(image)
            preprocessing_applied.append("denoise")
        
        # Step 4: Contrast enhancement
        if apply_contrast:
            image = self._enhance_contrast(image)
            preprocessing_applied.append("contrast_enhance")
        
        # Step 5: Binarization (optional)
        if apply_binarize:
            image = self._binarize(image)
            preprocessing_applied.append("binarize")
        
        # Assess quality
        quality_score = self.assess_quality(image)
        
        return ProcessedImage(
            image=image,
            original_path=None,
            quality_score=quality_score,
            preprocessing_applied=preprocessing_applied,
            deskew_angle=deskew_angle,
        )
    
    def assess_quality(self, image: np.ndarray) -> QualityScore:
        """Assess image quality for OCR engine selection.
        
        Metrics evaluated:
        - Sharpness: Laplacian variance (higher = sharper)
        - Contrast: Standard deviation ratio (higher = better contrast)
        - Noise level: Estimated from high-frequency components
        - Text density: Estimated from edge detection
        
        Args:
            image: Grayscale image as numpy array
            
        Returns:
            QualityScore with metrics and recommended OCR engine
        """
        # Ensure grayscale
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Calculate sharpness using Laplacian variance
        sharpness = self._calculate_sharpness(image)
        
        # Calculate contrast ratio
        contrast = self._calculate_contrast(image)
        
        # Estimate noise level
        noise_level = self._estimate_noise(image)
        
        # Estimate text density
        text_density = self._estimate_text_density(image)
        
        # Calculate overall score (weighted combination)
        # Normalize sharpness to 0-1 range (assuming max useful sharpness ~500)
        normalized_sharpness = min(sharpness / 500.0, 1.0)
        
        overall_score = (
            0.35 * normalized_sharpness +
            0.25 * contrast +
            0.25 * (1.0 - noise_level) +  # Lower noise is better
            0.15 * text_density
        )
        overall_score = max(0.0, min(1.0, overall_score))
        
        # Determine recommended engine
        if overall_score >= self.quality_threshold:
            recommended_engine = "tesseract"
        else:
            recommended_engine = "gpt4_vision"
        
        return QualityScore(
            sharpness=sharpness,
            contrast=contrast,
            noise_level=noise_level,
            text_density=text_density,
            overall_score=overall_score,
            recommended_engine=recommended_engine,
        )
    
    def _load_image(self, image_path: Path) -> Optional[np.ndarray]:
        """Load image from file path.
        
        Supports common image formats (PNG, JPEG, etc.) and PDF first page.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Image as numpy array or None if loading fails
        """
        suffix = image_path.suffix.lower()
        
        if suffix == ".pdf":
            return self._load_pdf_first_page(image_path)
        
        # Use OpenCV for standard image formats
        image = cv2.imread(str(image_path))
        if image is not None:
            return image
        
        # Fallback to PIL for other formats
        try:
            pil_image = Image.open(image_path)
            return np.array(pil_image.convert("RGB"))
        except Exception:
            return None
    
    def _load_pdf_first_page(self, pdf_path: Path) -> Optional[np.ndarray]:
        """Load first page of PDF as image.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            First page as numpy array or None if loading fails
        """
        try:
            # Try using pdf2image if available
            from pdf2image import convert_from_path
            
            pages = convert_from_path(str(pdf_path), first_page=1, last_page=1)
            if pages:
                return np.array(pages[0].convert("RGB"))
        except ImportError:
            # pdf2image not available, try alternative
            pass
        except Exception:
            pass
        
        return None
    
    def _to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """Convert image to grayscale.
        
        Args:
            image: Color image as numpy array (BGR or RGB)
            
        Returns:
            Grayscale image
        """
        if len(image.shape) == 2:
            return image
        
        # Check if BGR (OpenCV) or RGB (PIL)
        # Assume BGR for OpenCV loaded images
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    def _deskew(self, image: np.ndarray) -> Tuple[np.ndarray, float]:
        """Correct image rotation (deskew).
        
        Uses Hough line transform to detect dominant line angle
        and rotates the image to correct skew.
        
        Args:
            image: Grayscale image
            
        Returns:
            Tuple of (deskewed image, rotation angle in degrees)
        """
        # Detect edges
        edges = cv2.Canny(image, 50, 150, apertureSize=3)
        
        # Detect lines using Hough transform
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi / 180,
            threshold=100,
            minLineLength=100,
            maxLineGap=10,
        )
        
        if lines is None or len(lines) == 0:
            return image, 0.0
        
        # Calculate angles of detected lines
        angles = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if x2 - x1 != 0:
                angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
                # Only consider near-horizontal lines (within ±45°)
                if -45 <= angle <= 45:
                    angles.append(angle)
        
        if not angles:
            return image, 0.0
        
        # Use median angle to avoid outliers
        median_angle = np.median(angles)
        
        # Only deskew if angle is significant but not too large
        if abs(median_angle) < 0.5 or abs(median_angle) > 15:
            return image, 0.0
        
        # Rotate image to correct skew
        height, width = image.shape[:2]
        center = (width // 2, height // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
        
        # Calculate new image bounds
        cos_angle = abs(rotation_matrix[0, 0])
        sin_angle = abs(rotation_matrix[0, 1])
        new_width = int(height * sin_angle + width * cos_angle)
        new_height = int(height * cos_angle + width * sin_angle)
        
        # Adjust rotation matrix for new bounds
        rotation_matrix[0, 2] += (new_width - width) / 2
        rotation_matrix[1, 2] += (new_height - height) / 2
        
        deskewed = cv2.warpAffine(
            image,
            rotation_matrix,
            (new_width, new_height),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REPLICATE,
        )
        
        return deskewed, median_angle
    
    def _remove_noise(self, image: np.ndarray) -> np.ndarray:
        """Remove noise from image.
        
        Uses Non-local Means Denoising for grayscale images,
        which preserves edges while removing noise.
        
        Args:
            image: Grayscale image
            
        Returns:
            Denoised image
        """
        # Apply Non-local Means Denoising
        denoised = cv2.fastNlMeansDenoising(
            image,
            h=self.denoise_strength,
            templateWindowSize=7,
            searchWindowSize=21,
        )
        
        return denoised
    
    def _enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """Enhance image contrast using CLAHE.
        
        CLAHE (Contrast Limited Adaptive Histogram Equalization)
        enhances local contrast while limiting noise amplification.
        
        Args:
            image: Grayscale image
            
        Returns:
            Contrast-enhanced image
        """
        clahe = cv2.createCLAHE(
            clipLimit=self.clahe_clip_limit,
            tileGridSize=self.clahe_tile_size,
        )
        enhanced = clahe.apply(image)
        
        return enhanced
    
    def _binarize(self, image: np.ndarray) -> np.ndarray:
        """Binarize image using Otsu's method.
        
        Otsu's method automatically determines the optimal threshold
        for separating foreground (text) from background.
        
        Args:
            image: Grayscale image
            
        Returns:
            Binary image (black text on white background)
        """
        # Apply Gaussian blur to reduce noise before thresholding
        blurred = cv2.GaussianBlur(
            image,
            (self.gaussian_kernel_size, self.gaussian_kernel_size),
            0,
        )
        
        # Apply Otsu's thresholding
        _, binary = cv2.threshold(
            blurred,
            0,
            255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU,
        )
        
        return binary
    
    def _calculate_sharpness(self, image: np.ndarray) -> float:
        """Calculate image sharpness using Laplacian variance.
        
        Higher variance indicates sharper image with more defined edges.
        
        Args:
            image: Grayscale image
            
        Returns:
            Sharpness score (Laplacian variance)
        """
        laplacian = cv2.Laplacian(image, cv2.CV_64F)
        variance = laplacian.var()
        return float(variance)
    
    def _calculate_contrast(self, image: np.ndarray) -> float:
        """Calculate image contrast ratio.
        
        Uses standard deviation normalized by mean intensity.
        
        Args:
            image: Grayscale image
            
        Returns:
            Contrast ratio (0-1)
        """
        mean_intensity = np.mean(image)
        std_intensity = np.std(image)
        
        if mean_intensity == 0:
            return 0.0
        
        # Normalize to 0-1 range (assuming max useful std ~80)
        contrast = min(std_intensity / 80.0, 1.0)
        return float(contrast)
    
    def _estimate_noise(self, image: np.ndarray) -> float:
        """Estimate noise level in image.
        
        Uses high-pass filter to isolate noise components.
        
        Args:
            image: Grayscale image
            
        Returns:
            Noise level estimate (0-1, lower is better)
        """
        # Apply Laplacian to get high-frequency components
        laplacian = cv2.Laplacian(image, cv2.CV_64F)
        
        # Estimate noise as median absolute deviation
        sigma = np.median(np.abs(laplacian)) / 0.6745
        
        # Normalize to 0-1 range (assuming max noise sigma ~50)
        noise_level = min(sigma / 50.0, 1.0)
        return float(noise_level)
    
    def _estimate_text_density(self, image: np.ndarray) -> float:
        """Estimate text density in image.
        
        Uses edge detection to estimate how much of the image
        contains text or other content.
        
        Args:
            image: Grayscale image
            
        Returns:
            Text density estimate (0-1)
        """
        # Detect edges
        edges = cv2.Canny(image, 50, 150)
        
        # Calculate ratio of edge pixels to total pixels
        edge_ratio = np.sum(edges > 0) / edges.size
        
        # Normalize (typical text documents have 5-20% edge pixels)
        text_density = min(edge_ratio / 0.15, 1.0)
        return float(text_density)
    
    def save_processed_image(
        self,
        processed: ProcessedImage,
        output_path: Union[str, Path],
        format: str = "png",
    ) -> Path:
        """Save preprocessed image to file.
        
        Args:
            processed: ProcessedImage to save
            output_path: Output file path
            format: Output format (png, jpeg)
            
        Returns:
            Path to saved file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format.lower() == "jpeg":
            cv2.imwrite(
                str(output_path),
                processed.image,
                [cv2.IMWRITE_JPEG_QUALITY, 95],
            )
        else:
            cv2.imwrite(str(output_path), processed.image)
        
        return output_path
