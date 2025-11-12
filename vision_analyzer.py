# title: Blender Script Generator
# description: Generates Blender Python scripts from parsed sketch data using Ollama LLM.
# contact: Taewook Kang(laputa99999@gmail.com)
import time, json, tempfile, os
from PIL import Image
from dotenv import load_dotenv
 
load_dotenv()
ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY")

def analyze_sketch(image: Image.Image, progress_callback=None):
	if progress_callback:
		progress_callback("Analyzing image... (Object Detection)")

	# Object detection (wall, door, window, etc.)
	from inference_sdk import InferenceHTTPClient
	import numpy as np
	import pytesseract

	# Save image to a temporary file (InferenceHTTPClient requires file path)
	# Determine extension based on image format
	ext = '.jpg' if image.format and image.format.lower() == 'jpeg' else '.png'
	with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
		image.save(tmp.name)
		image_path = tmp.name

	# Call object detection model
	CLIENT = InferenceHTTPClient(
		api_url="https://serverless.roboflow.com",
		api_key=ROBOFLOW_API_KEY
	)
	# Use same model ID as in test_obj_detection.py
	result = CLIENT.infer(image_path, model_id="wall-detection-xi9ox/2")
	if progress_callback:
		progress_callback("Analyzing image... (OCR)")

	# OCR (pytesseract)
	# Convert image to numpy array
	img_height = image.size[1] / 10.0  # y-axis max value (scaled)
	img_np = np.array(image)
	ocr_data = pytesseract.image_to_data(img_np, output_type=pytesseract.Output.DICT)
	annotations = []
	n_boxes = len(ocr_data['level'])
	for i in range(n_boxes):
		text = ocr_data['text'][i].strip()
		if text:
			x = ocr_data['left'][i] + ocr_data['width'][i] // 2
			y_raw = ocr_data['top'][i] + ocr_data['height'][i] // 2
			x = x / 10.0 # Coordinate scaling
			y = img_height - (y_raw / 10.0)  # y-axis correction: flip for top view
			annotations.append({"text": text, "position": [x, y]})

	# Parse object detection results (coordinate correction: y-axis flip)
	elements = []
	for pred in result.get('predictions', []):
		cls = pred.get('class', '')
		x = pred.get('x', 0) / 10.0
		y_raw = pred.get('y', 0) / 10.0
		w = pred.get('width', 0) / 10.0
		h = pred.get('height', 0) / 10.0
		y = img_height - y_raw
		if cls == 'wall':
			if w > h:
				start = [x - w/2, y]
				end = [x + w/2, y]
			elif h > w:
				start = [x, y - h/2]
				end = [x, y + h/2]
			else:
				start = [x - w/2, y - h/2]
				end = [x + w/2, y + h/2]
			elements.append({"type": "wall", "start": [float(start[0]), float(start[1])], "end": [float(end[0]), float(end[1])]})
		elif cls == 'door':
			elements.append({"type": "door", "position": [float(x), float(y)], "size": float(max(w, h))})
		elif cls == 'window':
			elements.append({"type": "window", "position": [float(x), float(y)], "size": float(max(w, h))})

	output_json = {
		"elements": elements,
		"annotations": annotations,
		"image_size": image.size
	}

	if progress_callback:
		progress_callback("Image analysis complete. Starting Blender script generation.")

	return output_json

