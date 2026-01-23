import cv2
import os
import glob
import json

def detect_qr_codes(file, debug=False):
    """
    Detects QR codes in an image file and returns decoded data.
    
    Args:
        file: Path to image file
        debug: If True, prints debug information
    
    Returns:
        List of dictionaries containing QR code data and positions
    """
    img = cv2.imread(file)
    if img is None:
        print(f"Error: Could not read image {file}")
        return []
    
    # Initialize QR code detector
    qr_detector = cv2.QRCodeDetector()
    
    # Detect and decode QR codes
    data, bbox, straight_qrcode = qr_detector.detectAndDecode(img)
    
    results = []
    
    if data:
        if debug:
            print(f"QR Code detected!")
            print(f"Data: {data}")
            print(f"Bounding box: {bbox}")
        
        # Draw bounding box on image
        if bbox is not None:
            bbox = bbox.astype(int)
            for i in range(len(bbox[0])):
                pt1 = tuple(bbox[0][i])
                pt2 = tuple(bbox[0][(i + 1) % len(bbox[0])])
                cv2.line(img, pt1, pt2, (0, 255, 0), 3)
        
        results.append({
            'data': data,
            'bbox': bbox.tolist() if bbox is not None else None
        })
    else:
        if debug:
            print("No QR code detected")
    
    return img, results

def process_folder_qr(input_folder, output_folder=None):
    """
    Process all images in a folder and detect QR codes.
    
    Args:
        input_folder: Path to folder containing images
        output_folder: Path to save processed images (if None, creates 'qr_output' subfolder)
    """
    # Create output folder
    if output_folder is None:
        output_folder = os.path.join(input_folder, 'qr_output')
    
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
    print("=" * 60)
    
    # Store results for JSON export
    all_results = {}
    
    for img_path in image_files:
        filename = os.path.basename(img_path)
        print(f"\nProcessing: {filename}")
        
        processed_img, qr_results = detect_qr_codes(img_path, debug=False)
        
        if processed_img is not None:
            # Save processed image
            output_path = os.path.join(output_folder, f"qr_{filename}")
            cv2.imwrite(output_path, processed_img)
            
            if qr_results:
                print(f"  ✓ Found {len(qr_results)} QR code(s)")
                for i, qr in enumerate(qr_results):
                    print(f"    QR {i+1}: {qr['data']}")
            else:
                print(f"  ✗ No QR codes detected")
            
            all_results[filename] = {
                'num_qr_codes': len(qr_results),
                'qr_codes': qr_results
            }
    
    # Save results to JSON
    json_path = os.path.join(output_folder, 'qr_detection_results.json')
    with open(json_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    # Print summary
    print("\n" + "=" * 60)
    print("Processing complete!")
    print(f"Results saved to: {json_path}")
    print(f"Processed images saved to: {output_folder}")
    
    # Print all QR codes found
    total_qr_codes = sum(len(results['qr_codes']) for results in all_results.values())
    print(f"\nTotal QR codes found: {total_qr_codes}")
    
    if total_qr_codes > 0:
        print("\nAll QR code data:")
        for filename, results in all_results.items():
            if results['qr_codes']:
                print(f"\n  {filename}:")
                for i, qr in enumerate(results['qr_codes']):
                    print(f"    {i+1}. {qr['data']}")

if __name__ == '__main__':
    # Configuration
    input_folder = r"C:\Users\MarcosDaSilvaEleoter\OneDrive - Smart Photonics\Coding\Img_recog"
    
    process_folder_qr(input_folder=input_folder)
