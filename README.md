# Sketch to Blender

Sketch drawing image to Blender objecs App that converts architectural sketch floor plans into Blender Python scripts using computer vision and LLMs. This is demo version for researching the object reconstruction from raster images in construction domain.

<p align="center">
   <img src="https://github.com/mac999/sketch_to_blender/blob/main/doc/img1.jpg" width="400"></img>
</p>

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
3. Install and run Ollama locally for LLM-based script generation:
   - See [Ollama documentation](https://ollama.com/) for setup instructions.
   - Download LLM weight file like gemma3

4. Make .env:
   - Setup RAINBOW_API_KEY after login Rainbow flow(https://app.roboflow.com)

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


