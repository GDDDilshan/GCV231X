#!/usr/bin/env python3
"""
Modern Web Dashboard Server for CS402.3 Student Attendance Management System (SAMS)
Zero external dependencies - Uses Python built-in http.server & JSON REST API.
"""

import http.server
import socketserver
import json
import os
import sys
import urllib.parse
import base64
import webbrowser
import cv2

# Add root directory to python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.config import BASE_DIR, OUTPUTS_DIR, SAMPLE_IMAGES_DIR, BASELINE_SIGNATURES_DIR
from modules.db_manager import DatabaseManager
from modules.image_processor import ImageProcessor
from modules.visualizer import AttendanceVisualizer
from modules.signature_verifier import SignatureVerifier

PORT = 5001

class SAMSRequestHandler(http.server.BaseHTTPRequestHandler):

    def _send_json(self, data, status=200):
        body = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, filepath, content_type):
        if not os.path.exists(filepath):
            self.send_error(404, f"File not found: {filepath}")
            return
        with open(filepath, 'rb') as f:
            content = f.read()
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            html_path = os.path.join(BASE_DIR, "web", "index.html")
            self._send_file(html_path, "text/html")
        elif path.startswith("/static/"):
            file_rel = path.replace("/static/", "")
            full_path = os.path.join(BASE_DIR, "web", file_rel)
            mime = "text/css" if file_rel.endswith(".css") else "application/javascript"
            self._send_file(full_path, mime)
        elif path.startswith("/outputs/"):
            file_rel = path.replace("/outputs/", "")
            full_path = os.path.join(OUTPUTS_DIR, file_rel)
            self._send_file(full_path, "image/png")
        elif path.startswith("/sample_images/"):
            file_rel = path.replace("/sample_images/", "")
            full_path = os.path.join(SAMPLE_IMAGES_DIR, file_rel)
            self._send_file(full_path, "image/png")
        elif path.startswith("/signatures/"):
            file_rel = path.replace("/signatures/", "")
            full_path = os.path.join(BASELINE_SIGNATURES_DIR, file_rel)
            self._send_file(full_path, "image/png")
        elif path == "/api/students":
            db = DatabaseManager()
            db.sync_students_from_xml(os.path.join(BASE_DIR, "info.xml"))
            indices = db.get_all_student_indices()
            students = [db.get_student_info(idx) for idx in indices]
            self._send_json({"students": students})
        elif path == "/api/sample_images":
            files = [f for f in os.listdir(SAMPLE_IMAGES_DIR) if f.endswith(".png") or f.endswith(".jpg")]
            self._send_json({"images": sorted(files)})
        elif path.startswith("/api/student_stats/"):
            student_idx = path.replace("/api/student_stats/", "")
            db = DatabaseManager()
            info = db.get_student_info(student_idx)
            history = db.get_student_attendance_history(student_idx)
            self._send_json({"info": info, "history": history})
        elif path.startswith("/api/verify/"):
            student_idx = path.replace("/api/verify/", "")
            db = DatabaseManager()
            info = db.get_student_info(student_idx)
            templates = db.get_signature_templates(student_idx)
            history = db.get_student_attendance_history(student_idx)

            if not templates or not history:
                self._send_json({"error": "No templates or history found for verification."}, status=400)
                return

            verifier = SignatureVerifier()
            template_imgs = [cv2.imread(tp) for tp in templates if os.path.exists(tp)]
            template_imgs = [img for img in template_imgs if img is not None]

            report = []
            for item in history:
                crop_p = item['signature_path']
                if not crop_p or not os.path.exists(crop_p):
                    report.append({"date": item['date'], "status": "ABSENT", "ssim": 0.0, "orb": 0, "confidence": 0.0, "verdict": "ABSENT (No Signature)"})
                else:
                    q_img = cv2.imread(crop_p)
                    res = verifier.verify_signature(q_img, template_imgs)
                    report.append({"date": item['date'], "status": "PRESENT", "ssim": round(res['ssim_score'], 4), "orb": res['orb_matches'], "confidence": round(res['confidence'], 1), "verdict": res['verdict']})

            self._send_json({"info": info, "template": os.path.basename(templates[0]) if templates else "", "report": report})



        elif path == "/api/export_csv":
            db = DatabaseManager()
            db.sync_students_from_xml(os.path.join(BASE_DIR, "info.xml"))
            indices = db.get_all_student_indices()

            lines = ["Student Index,Student Name,Total Sessions,Sessions Attended,Sessions Missed,Attendance Rate (%)"]
            for idx in indices:
                info = db.get_student_info(idx)
                name = info['name'] if info else ''
                history = db.get_student_attendance_history(idx)
                tot = len(history)
                pres = sum(1 for h in history if h['status'] == 'PRESENT')
                absent = tot - pres
                rate = (pres / tot * 100) if tot > 0 else 0
                lines.append(f'"{idx}","{name}",{tot},{pres},{absent},{rate:.1f}')

            csv_body = "\n".join(lines).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/csv')
            self.send_header('Content-Disposition', 'attachment; filename="attendance_report.csv"')
            self.send_header('Content-Length', str(len(csv_body)))
            self.end_headers()
            self.wfile.write(csv_body)
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/api/upload_image":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            params = json.loads(post_data.decode('utf-8'))

            filename = params.get('filename', 'uploaded_sheet.png')
            raw_b64 = params.get('image_data', '')
            if ',' in raw_b64:
                raw_b64 = raw_b64.split(',', 1)[1]

            safe_name = os.path.basename(filename).replace(" ", "_")
            if not safe_name.endswith(('.png', '.jpg', '.jpeg')):
                safe_name += '.png'

            save_path = os.path.join(SAMPLE_IMAGES_DIR, safe_name)
            with open(save_path, 'wb') as f:
                f.write(base64.b64decode(raw_b64))

            # Automatically process uploaded image
            params['image_name'] = safe_name

        if self.path in ["/api/process_image", "/api/upload_image"]:
            content_length = int(self.headers.get('Content-Length', 0))
            if self.path == "/api/process_image":
                post_data = self.rfile.read(content_length)
                params = json.loads(post_data.decode('utf-8'))

            image_name = params.get('image_name', '12.07.2019.png')
            image_path = os.path.join(SAMPLE_IMAGES_DIR, image_name)

            if not os.path.exists(image_path):
                self._send_json({"error": f"Image file not found: {image_name}"}, status=404)
                return

            db = DatabaseManager()
            db.sync_students_from_xml(os.path.join(BASE_DIR, "info.xml"))
            student_indices = db.get_all_student_indices()

            processor = ImageProcessor(image_path)
            results = processor.process_pipeline(expected_students=len(student_indices))

            base_name = os.path.splitext(image_name)[0]
            saved_steps = processor.save_step_visualizations(output_prefix=base_name)

            session_date = base_name.replace(".png", "").replace("uploaded_", "")
            attendance_data = []
            formatted_results = []

            for i, res in enumerate(results):
                student_idx = student_indices[i] if i < len(student_indices) else f"STUDENT_{i+1}"
                student_info = db.get_student_info(student_idx)
                status = res['status']
                density = res['ink_density']
                crop_img = res['signature_crop']

                crop_filename = f"sig_{student_idx}_{session_date}.png"
                crop_save_path = os.path.join(BASELINE_SIGNATURES_DIR, crop_filename)

                if status == 'PRESENT' and crop_img is not None:
                    cv2.imwrite(crop_save_path, crop_img)
                    if session_date in ['31.05.2019', '21.06.2019']:
                        templates = db.get_signature_templates(student_idx)
                        if crop_save_path not in templates:
                            db.register_signature_template(student_idx, crop_save_path)



                attendance_data.append({
                    'student_index': student_idx,
                    'status': status,
                    'ink_density': density,
                    'crop_path': crop_save_path if status == 'PRESENT' else ''
                })

                formatted_results.append({
                    'no': i + 1,
                    'student_index': student_idx,
                    'name': student_info['name'] if student_info else '',
                    'ink_density': round(density * 100, 2),
                    'status': status
                })

            db.save_session_attendance(
                session_date=session_date,
                time_range="13:00-16:00",
                lecturer_name="Dr. Rasika Ranaweera",
                image_source=image_path,
                attendance_results=attendance_data
            )

            step_urls = {step: f"/outputs/{os.path.basename(path)}" for step, path in saved_steps.items()}

            self._send_json({
                "message": "Processing complete",
                "session_date": session_date,
                "steps": step_urls,
                "results": formatted_results,
                "image_name": image_name
            })


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

def start_server():

    os.makedirs(os.path.join(BASE_DIR, "web"), exist_ok=True)
    httpd = None
    port = 5001
    for p in range(5001, 5020):
        try:
            httpd = ReusableTCPServer(('127.0.0.1', p), SAMSRequestHandler)
            port = p
            break
        except OSError:
            continue


    if httpd is None:
        print("Error: Could not bind to any port in range 5001-5020.")
        return

    print(f"==================================================================")
    print(f"   🚀 SAMS Web Dashboard running at: http://localhost:{port}")
    print(f"==================================================================")
    webbrowser.open(f"http://localhost:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down web server...")
        httpd.server_close()


if __name__ == '__main__':
    start_server()
