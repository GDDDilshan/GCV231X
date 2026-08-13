#!/usr/bin/env python3
"""
Student Signature Verification & Investigation Tool
Usage: python investigate.py <student_index>
Example: python investigate.py 10000409
"""

import sys
import os
import cv2

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.db_manager import DatabaseManager
from modules.signature_verifier import SignatureVerifier

def main():
    if len(sys.argv) < 2:
        print("Usage: python investigate.py <student_index>")
        print("Example: python investigate.py 10000409")
        sys.exit(1)

    student_index = sys.argv[1].strip()
    db = DatabaseManager()

    # Match student index (handle short format like 001)
    student_info = db.get_student_info(student_index)
    if not student_info:
        all_indices = db.get_all_student_indices()
        matched = [idx for idx in all_indices if idx.endswith(student_index)]
        if matched:
            student_index = matched[0]
            student_info = db.get_student_info(student_index)

    if not student_info:
        print(f"Error: Student index '{sys.argv[1]}' not found in database.")
        sys.exit(1)

    templates = db.get_signature_templates(student_index)
    history = db.get_student_attendance_history(student_index)

    print("=" * 70)
    print("      STUDENT SIGNATURE RECOGNITION & VERIFICATION SYSTEM      ")
    print("=" * 70)
    print(f"Investigating Student : {student_info['name']} ({student_info['student_index']})")
    print("-" * 70)

    if not templates:
        print(f"[Warning] No baseline reference template found for student {student_index}.")
        print("Registering current available cropped signature as baseline template...")
        valid_crops = [h['signature_path'] for h in history if h['signature_path'] and os.path.exists(h['signature_path'])]
        if valid_crops:
            db.register_signature_template(student_index, valid_crops[0])
            templates = [valid_crops[0]]
        else:
            print("Error: No signed crops available to perform signature verification.")
            sys.exit(1)

    template_imgs = [cv2.imread(tp) for tp in templates if os.path.exists(tp)]
    template_imgs = [img for img in template_imgs if img is not None]
    verifier = SignatureVerifier()

    print(f"Reference Baseline Signatures: {[os.path.basename(tp) for tp in templates]}")
    print("-" * 70)
    print(f"{'Date':<12} | {'SSIM Score':<12} | {'ORB Matches':<12} | {'Confidence':<12} | {'Verification Verdict'}")
    print("-" * 70)

    for item in history:
        crop_path = item['signature_path']
        date_str = item['date']

        if not crop_path or not os.path.exists(crop_path):
            print(f"{date_str:<12} | {'N/A':<12} | {'N/A':<12} | {'0.0%':<12} | ABSENT (No Signature)")
            continue

        query_img = cv2.imread(crop_path)
        ver_result = verifier.verify_signature(query_img, template_imgs)


        ssim_str = f"{ver_result['ssim_score']:.4f}"
        orb_str = f"{ver_result['orb_matches']} keypoints"
        conf_str = f"{ver_result['confidence']:.1f}%"
        verdict = ver_result['verdict']

        print(f"{date_str:<12} | {ssim_str:<12} | {orb_str:<12} | {conf_str:<12} | {verdict}")



    print("-" * 70)
    print("Verification Completed Successfully.")
    print("=" * 70 + "\n")

if __name__ == '__main__':
    main()
