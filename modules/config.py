import os

# System Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "attendance.db")
SAMPLE_IMAGES_DIR = os.path.join(BASE_DIR, "sample_images")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
BASELINE_SIGNATURES_DIR = os.path.join(BASE_DIR, "baseline_signatures")

# Ensure required directories exist
for path in [os.path.dirname(DB_PATH), SAMPLE_IMAGES_DIR, OUTPUTS_DIR, BASELINE_SIGNATURES_DIR]:
    os.makedirs(path, exist_ok=True)

# Image Processing Parameters
DEFAULT_CANNY_TH1 = 50
DEFAULT_CANNY_TH2 = 150
INK_DENSITY_THRESHOLD = 0.02  # Minimum ink ratio in cell to be considered present (2.0%)
NOISE_MAX_THRESHOLD = 0.005    # Noise cutoff

# Verification Thresholds
SSIM_SIMILARITY_THRESHOLD = 0.45  # 45% SSIM score for match
ORB_MATCH_THRESHOLD = 15         # Minimum good ORB keypoint matches
