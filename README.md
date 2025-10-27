# Sketch to Blender

Sketch image to Blender objecs App that converts architectural sketch floor plans into Blender Python scripts using computer vision and LLMs. This is demo version for researching the object reconstruction from raster images in construction domain.

## Introduction
This project analyzes architectural sketch images to detect walls, doors, and windows, then generates a Blender script to model the building in 3D. It uses object detection, OCR, and a local LLM (Ollama) for script generation.

## Installation
1. Clone the repository:
   ```sh
   git clone <your-repo-url>
   cd sketch_to_blender
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. (Optional) Install and run Ollama locally for LLM-based script generation:
   - See [Ollama documentation](https://ollama.com/) for setup instructions.

## Usage
1. Start the Streamlit app:
   ```sh
   streamlit run app.py
   ```
2. Upload a sketch image (PNG/JPG) via the web interface.
3. View the detected elements and generated Blender script.
4. Download the script and use it in Blender.

## Contact
Taewook Kang (laputa99999@gmail.com)

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.