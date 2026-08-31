import cv2

def quality_score(rgb, detection_score):
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    blur = min(1.0, float(cv2.Laplacian(gray, cv2.CV_64F).var()) / 150.0)
    brightness = max(0.0, 1.0 - abs(float(gray.mean()) - 128.0) / 128.0)
    return float(0.55*detection_score + 0.30*blur + 0.15*brightness)
