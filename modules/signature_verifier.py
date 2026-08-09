import cv2
import numpy as np
import os
from modules.config import SSIM_SIMILARITY_THRESHOLD, ORB_MATCH_THRESHOLD

class SignatureVerifier:
    def __init__(self):
        self.orb = cv2.ORB_create(nfeatures=500)
        self.bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    def extract_stroke_features(self, img):
        """Extract padded stroke features, aspect ratio, and contour complexity."""
        if img is None or img.size == 0:
            return None
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)


        pts = cv2.findNonZero(thresh)
        if pts is None or len(pts) < 15:
            return None

        density = float(len(pts)) / float(img.shape[0] * img.shape[1])
        if density < 0.015:
            return None

        x, y, w, h = cv2.boundingRect(pts)
        crop = thresh[y:y+h, x:x+w]
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        significant_contours = [c for c in contours if cv2.contourArea(c) >= 50]



        target_h = 60
        target_w = max(20, int(w * (60.0 / float(h))))
        norm = cv2.resize(crop, (target_w, target_h))

        padded = np.zeros((60, 180), dtype=np.uint8)
        pw = min(180, norm.shape[1])
        padded[:, :pw] = norm[:, :pw]

        h_proj = np.sum(padded > 0, axis=1).astype(np.float32) / 180.0
        v_proj = np.sum(padded > 0, axis=0).astype(np.float32) / 60.0

        norm_stroke = cv2.resize(crop, (160, 50))

        sift = cv2.SIFT_create()
        kp, _ = sift.detectAndCompute(padded, None)

        return {
            'img': img,
            'thresh': thresh,
            'crop': crop,
            'norm': norm_stroke,
            'padded': padded,
            'h_proj': h_proj,
            'v_proj': v_proj,
            'contours': len(significant_contours),
            'sift_count': len(kp) if kp is not None else 0,
            'aspect': float(w)/float(h)
        }



    def compare_single_pair(self, f1, f2):
        if f1 is None or f2 is None:
            return 0.0, 0.0, 0, 0.0

        sift = cv2.SIFT_create()
        kp1, des1 = sift.detectAndCompute(f1['norm'], None)
        kp2, des2 = sift.detectAndCompute(f2['norm'], None)


        sift_c = 0
        if des1 is not None and des2 is not None and len(des1) >= 2 and len(des2) >= 2:
            bf = cv2.BFMatcher()
            matches = bf.knnMatch(des1, des2, k=2)
            good = [m for m_p in matches if len(m_p) == 2 for m, n in [m_p] if m.distance < 0.75 * n.distance]
            sift_c = len(good)


        return 0.0, 0.0, sift_c, 0.0

    def verify_signature(self, query_img, template_img_or_list):
        """
        Verify query signature against baseline template image or list of template images.
        """
        f_q = self.extract_stroke_features(query_img)
        if f_q is None:
            return None

        templates = template_img_or_list if isinstance(template_img_or_list, list) else [template_img_or_list]
        template_features = [self.extract_stroke_features(t) for t in templates]
        template_features = [tf for tf in template_features if tf is not None]

        if not template_features:
            return None

        best_conf, best_ssim, best_sift, best_proj = 0.0, 0.0, 0, 0.0
        for f_b in template_features:
            conf, ssim, sift_c, proj = self.compare_single_pair(f_q, f_b)
            if conf > best_conf:
                best_conf, best_ssim, best_sift, best_proj = conf, ssim, sift_c, proj

        is_match = False
        verdict = ""











        return {
            "verdict": verdict,
            "ssim_score": float(best_ssim),
            "orb_matches": int(best_sift),
            "confidence": float(best_conf),
            "is_match": is_match
        }




