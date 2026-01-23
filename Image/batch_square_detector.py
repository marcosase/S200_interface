import cv2
import time
import os
import json
import glob

def sqrt_det(file, min_area=500, epsilon_factor=0.02, debug=False):
    """
    Detects squares in an image file and draws them. Returns a list of square contours.
    min_area: minimum area threshold to filter out small squares.
    epsilon_factor: controls contour simplification (0.01-0.04 typical).
    debug: if True, prints area and epsilon for each contour.
    """
    img = cv2.imread(file)
    if img is None:
        print(f"Error: Could not read image {file}")
        return []
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    squares = []
    
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
                if 0.8 <= aspect_ratio <= 1.2:  # More lenient aspect ratio
                    squares.append(approx)
                    cv2.drawContours(img, [approx], -1, (0, 255, 0), 3)
    
    return img, squares

def process_folder(input_folder, output_folder=None, min_area=500, epsilon_factor=0.02):
    """
    Process all images in a folder and detect squares.
    
    Args:
        input_folder: Path to folder containing images
        output_folder: Path to save processed images (if None, creates 'output' subfolder)
        min_area: Minimum area threshold for square detection
        epsilon_factor: Epsilon factor for contour approximation
    """
    # Create output folder
    if output_folder is None:
        output_folder = os.path.join(input_folder, 'output')
    
    os.makedirs(output_folder, exist_ok=True)
    
    # Supported image extensions
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff', '*.tif']
    image_files = []
    
    for ext in image_extensions:
        image_files.extend(glob.glob(os.path.join(input_folder, ext)))
        image_files.extend(glob.glob(os.path.join(input_folder, ext.upper())))
    
    if not image_files:
        print(f"No images found in {input_folder}")
        return
    
    print(f"Found {len(image_files)} images to process")
    
    # Store results for JSON export
    results = {}
    
    for img_path in image_files:
        filename = os.path.basename(img_path)
        print(f"\nProcessing: {filename}")
        
        processed_img, squares = sqrt_det(img_path, min_area=min_area, epsilon_factor=epsilon_factor, debug=False)
        
        if processed_img is not None:
            # Save processed image
            output_path = os.path.join(output_folder, f"detected_{filename}")
            cv2.imwrite(output_path, processed_img)
            print(f"  Found {len(squares)} squares")
            print(f"  Saved to: {output_path}")
            
            # Extract boundary coordinates
            boundaries = []
            for i, square in enumerate(squares):
                coords = square.reshape(-1, 2).tolist()
                x, y, w, h = cv2.boundingRect(square)
                boundaries.append({
                    'square_id': i,
                    'vertices': coords,
                    'bounding_box': {'x': int(x), 'y': int(y), 'width': int(w), 'height': int(h)},
                    'area': float(cv2.contourArea(square))
                })
            
            results[filename] = {
                'num_squares': len(squares),
                'squares': boundaries
            }
    
    # Save results to JSON
    json_path = os.path.join(output_folder, 'detection_results.json')
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'='*50}")
    print(f"Processing complete!")
    print(f"Results saved to: {json_path}")
    print(f"Processed images saved to: {output_folder}")

if __name__ == '__main__':
    # Configuration
    input_folder = r"C:\Users\MarcosDaSilvaEleoter\OneDrive - Smart Photonics\Coding\Img_recog"
    
    # Adjust these parameters as needed:
    # - min_area: minimum area for square detection (increase to ignore small squares)
    # - epsilon_factor: contour simplification (0.01-0.04 typical)
    
    process_folder(
        input_folder=input_folder,
        min_area=100,           # Lower threshold for large squares (area ~4000px means side ~63px, so area ~4000)
        epsilon_factor=0.005    # Much smaller epsilon to detect larger, well-defined squares
    )
