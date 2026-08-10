import cv2
import numpy as np
import os
from modules.config import SSIM_SIMILARITY_THRESHOLD, ORB_MATCH_THRESHOLD

class SignatureVerifier:
   def __init__(self):
        self.orb = cv2.ORB_create(nfeatures=500)
        self.bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)


    def calculate_ssim(self, img1, img2):
        """
        Compute Structural Similarity Index (SSIM) between two signature images.
        """
        # Resize both images to standard size 200x80
        target_size = (200, 80)
        g1 = cv2.resize(cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY) if len(img1.shape) == 3 else img1, target_size)
        g2 = cv2.resize(cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY) if len(img2.shape) == 3 else img2, target_size)

        # SSIM calculation formula constants
        C1 = (0.01 * 255) ** 2
        C2 = (0.03 * 255) ** 2

        img1_f = g1.astype(np.float64)
        img2_f = g2.astype(np.float64)

        mu1 = cv2.GaussianBlur(img1_f, (11, 11), 1.5)
        mu2 = cv2.GaussianBlur(img2_f, (11, 11), 1.5)

        mu1_sq = mu1 ** 2
        mu2_sq = mu2 ** 2
        mu1_mu2 = mu1 * mu2

        sigma1_sq = cv2.GaussianBlur(img1_f ** 2, (11, 11), 1.5) - mu1_sq
        sigma2_sq = cv2.GaussianBlur(img2_f ** 2, (11, 11), 1.5) - mu2_sq
        sigma12 = cv2.GaussianBlur(img1_f * img2_f, (11, 11), 1.5) - mu1_mu2

        ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
        return float(ssim_map.mean())

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


        h_corr = float(np.corrcoef(f1['h_proj'], f2['h_proj'])[0, 1]) if np.std(f1['h_proj']) > 0 and np.std(f2['h_proj']) > 0 else 0.0
        v_corr = float(np.corrcoef(f1['v_proj'], f2['v_proj'])[0, 1]) if np.std(f1['v_proj']) > 0 and np.std(f2['v_proj']) > 0 else 0.0
        proj = max(0.0, (h_corr + v_corr) / 2.0)

        C1, C2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
        g1, g2 = f1['padded'].astype(np.float64), f2['padded'].astype(np.float64)
        mu1, mu2 = cv2.GaussianBlur(g1, (11, 11), 1.5), cv2.GaussianBlur(g2, (11, 11), 1.5)
        mu1_sq, mu2_sq, mu1_mu2 = mu1**2, mu2**2, mu1*mu2
        sigma1_sq = cv2.GaussianBlur(g1**2, (11, 11), 1.5) - mu1_sq
        sigma2_sq = cv2.GaussianBlur(g2**2, (11, 11), 1.5) - mu2_sq
        sigma12 = cv2.GaussianBlur(g1*g2, (11, 11), 1.5) - mu1_mu2
        stroke_ssim = float((((2*mu1_mu2 + C1)*(2*sigma12 + C2)) / ((mu1_sq + mu2_sq + C1)*(sigma1_sq + sigma2_sq + C2))).mean())

        conf = (stroke_ssim * 0.40) + (proj * 0.40) + (min(1.0, sift_c / 10.0) * 0.20)
        return conf * 100.0, stroke_ssim, sift_c, proj

    def verify_signature(self, query_img, template_img_or_list):
        """
        Verify query signature against baseline template image or list of template images.
        """
        f_q = self.extract_stroke_features(query_img)
        if f_q is None:
            return {
                "verdict": "ABSENT (NO SIGNATURE)",
                "ssim_score": 0.0,
                "orb_matches": 0,
                "confidence": 0.0,
                "is_match": False
            }

        templates = template_img_or_list if isinstance(template_img_or_list, list) else [template_img_or_list]
        template_features = [self.extract_stroke_features(t) for t in templates]
        template_features = [tf for tf in template_features if tf is not None]

        if not template_features:
            return {
                "verdict": "ABSENT (NO SIGNATURE)",
                "ssim_score": 0.0,
                "orb_matches": 0,
                "confidence": 0.0,
                "is_match": False
            }

        best_conf, best_ssim, best_sift, best_proj = 0.0, 0.0, 0, 0.0
        for f_b in template_features:
            conf, ssim, sift_c, proj = self.compare_single_pair(f_q, f_b)
            if conf > best_conf:
                best_conf, best_ssim, best_sift, best_proj = conf, ssim, sift_c, proj

        is_match = (best_sift >= 3 or best_conf >= 45.0)
        verdict = "AUTHENTIC MATCH" if is_match else "SUSPECTED MISMATCH / FRAUD"











        return {
            "verdict": verdict,
            "ssim_score": float(best_ssim),
            "orb_matches": int(best_sift),
            "confidence": float(best_conf),
            "is_match": is_match
        }




