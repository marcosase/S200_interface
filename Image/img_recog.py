import cv2
import time

def sqrt_det(file, min_area=500, epsilon_factor=0.02, debug=True):
    """
    Detects squares in an image file and draws them. Returns a list of square contours.
    min_area: minimum area threshold to filter out small squares.
    epsilon_factor: controls contour simplification (0.01-0.04 typical).
    debug: if True, prints area and epsilon for each contour and shows debug image.
    """
    img = cv2.imread(file)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    squares = []
    debug_img = img.copy()
    for cnt in contours:
        epsilon = epsilon_factor * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)
        area = cv2.contourArea(approx)
        if debug:
            print(f"Contour area: {area:.2f}, epsilon: {epsilon:.2f}, vertices: {len(approx)}")
        if len(approx) == 4 and cv2.isContourConvex(approx):
            if area > min_area:
                x, y, w, h = cv2.boundingRect(approx)
                aspect_ratio = float(w) / h
                if 0.9 <= aspect_ratio <= 1.1:
                    squares.append(approx)
                    cv2.drawContours(img, [approx], -1, (0, 255, 0), 3)
                    cv2.drawContours(debug_img, [approx], -1, (255, 0, 0), 2)
    cv2.imwrite('test'+str(int(time.time()))+'.png', img)
    if debug:
        cv2.imshow('Debug Squares', debug_img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    return squares