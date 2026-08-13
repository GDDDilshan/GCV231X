#!/usr/bin/env python3
"""
Student Attendance Management System (SAMS)
Usage: python sams.py <image_path> info.xml [--show]
Example: python sams.py sample_images/12.07.2019.png info.xml --show
"""

import sys
import os
import re
import cv2

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.db_manager import DatabaseManager
from modules.image_processor import ImageProcessor
from modules.config import BASELINE_SIGNATURES_DIR

def parse_date_from_filename(filename):
    match = re.search(r'(\d{2}[\.\/]\d{2}[\.\/]\d{4})', filename)
    if match:
        return match.group(1).replace('/', '.')
    return "UNKNOWN_DATE"

def process_single_image(image_path, xml_path, db, student_indices, show_windows=False):
    print(f"\n[Image Processing] Processing file: {image_path}")
    print(" [Step 1/5] Loading original image...")
    processor = ImageProcessor(image_path)

    print(" [Step 2/5] Converting image to Grayscale...")
    print(" [Step 3/5] Applying Adaptive Otsu Binarization...")
    print(" [Step 4/5] Detecting Table Grid Lines & Signature ROIs...")
    print(" [Step 5/5] Analyzing Ink Density & Classifying Attendance...")

    results = processor.process_pipeline(expected_students=len(student_indices))

    # Save visual step outputs
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    saved_steps = processor.save_step_visualizations(output_prefix=base_name)
    print(f"\n[Visual Progress] Saved step-by-step processing images to 'outputs/' directory:")
    for step, path in saved_steps.items():
        print(f"  - {step}: {os.path.basename(path)}")

    # Show live interactive OpenCV windows if requested
    if show_windows:
        print("\n[UI Display] Opening OpenCV live progress windows. Press any key on window to close...")
        for step_name, img in processor.processing_steps.items():
            resized_view = cv2.resize(img, (500, 620))
            cv2.imshow(f"SAMS Progress - {step_name}", resized_view)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    # Map processed rows with XML student indices
    session_date = parse_date_from_filename(os.path.basename(image_path))
    lecturer = "Dr. Rasika Ranaweera"
    time_range = "13:00-16:00"

    attendance_data = []
    print("\n" + "-" * 65)
    print(f"{'No.':<4} | {'Student Index':<14} | {'Ink Ratio':<10} | {'Status':<10}")
    print("-" * 65)

    for i, res in enumerate(results):
        student_idx = student_indices[i] if i < len(student_indices) else f"STUDENT_{i+1}"
        row_status = res['status']
        density = res['ink_density']
        crop_img = res['signature_crop']

        crop_filename = f"sig_{student_idx}_{session_date}.png"
        crop_save_path = os.path.join(BASELINE_SIGNATURES_DIR, crop_filename)

        if row_status == 'PRESENT' and crop_img is not None:
            cv2.imwrite(crop_save_path, crop_img)
            if session_date in ['31.05.2019', '21.06.2019']:
                templates = db.get_signature_templates(student_idx)
                if crop_save_path not in templates:
                    db.register_signature_template(student_idx, crop_save_path)



        attendance_data.append({
            'student_index': student_idx,
            'status': row_status,
            'ink_density': density,
            'crop_path': crop_save_path if row_status == 'PRESENT' else ''
        })

        print(f"{i+1:<4} | {student_idx:<14} | {density*100:6.2f}%     | {row_status:<10}")

    print("-" * 65)

    session_id = db.save_session_attendance(
        session_date=session_date,
        time_range=time_range,
        lecturer_name=lecturer,
        image_source=image_path,
        attendance_results=attendance_data
    )
    print(f"\n[DB] Successfully recorded Session ID #{session_id} for date {session_date} into SQLite database!")
    print("=" * 65)

def main():
    if len(sys.argv) < 3:
        print("Usage: python sams.py <image_path_or_directory> info.xml [--show]")
        print("Example 1 (Single): python sams.py sample_images/12.07.2019.png info.xml")
        print("Example 2 (Batch):  python sams.py sample_images/ info.xml")
        sys.exit(1)

    target_path = sys.argv[1]
    xml_path = sys.argv[2]
    show_windows = "--show" in sys.argv or "-s" in sys.argv

    if not os.path.exists(target_path):
        print(f"Error: Target file or directory not found: {target_path}")
        sys.exit(1)

    if not os.path.exists(xml_path):
        print(f"Error: XML file not found: {xml_path}")
        sys.exit(1)

    print("=" * 65)
    print("      STUDENT ATTENDANCE MANAGEMENT SYSTEM (SAMS)      ")
    print("=" * 65)

    db = DatabaseManager()
    synced_students = db.sync_students_from_xml(xml_path)
    print(f"[DB] Synced {synced_students} student records from '{xml_path}' into database.")

    student_indices = db.get_all_student_indices()

    if os.path.isdir(target_path):
        image_files = sorted([
            os.path.join(target_path, f) for f in os.listdir(target_path)
            if f.endswith(('.png', '.jpg', '.jpeg'))
        ])
        print(f"\n[Batch Mode] Found {len(image_files)} signing sheet images in '{target_path}'. Processing all...")
        for img_p in image_files:
            process_single_image(img_p, xml_path, db, student_indices, show_windows)
        print("\n[Batch Mode Complete] All signing sheets processed successfully!")
    else:
        process_single_image(target_path, xml_path, db, student_indices, show_windows)

if __name__ == '__main__':
    main()