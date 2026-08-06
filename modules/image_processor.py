import cv2
import numpy as np
import os
from modules.config import OUTPUTS_DIR










class ImageProcessor:
    def __init__(self, image_path):
        self.image_path = image_path
        self.filename = os.path.basename(image_path)
        self.original_image = cv2.imread(image_path)
        if self.original_image is None:
            raise FileNotFoundError(f"Could not read image file at: {image_path}")

        self.gray = None
        self.binary = None
        self.aligned_image = None
        self.signature_crops = {}   # index -> image array
        self.processing_steps = {}  # step_name -> image array
        self._session_date = self._parse_date_from_filename(self.filename)

    def _parse_date_from_filename(self, filename):
        """Extract date string from filename like '12.07.2019.png'"""
        import re
        m = re.search(r'(\d{2}[.\\/]\d{2}[.\\/]\d{4})', filename)
        if m:
            return m.group(1).replace('/', '.').replace('\\', '.')
        return None

    def process_pipeline(self, expected_students=6):
        """
        Execute 5-step image processing pipeline as required by CS402.3 coursework.
        Returns metadata (session date, lecturer) and student attendance list.
        """
        # Step 1: Original Image
        self.processing_steps['01_Original'] = self.original_image.copy()
        self.aligned_image = self.original_image.copy()

        # Step 2: Grayscale Conversion
        self.gray = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2GRAY)
        self.processing_steps['02_Grayscale'] = cv2.cvtColor(self.gray, cv2.COLOR_GRAY2BGR)