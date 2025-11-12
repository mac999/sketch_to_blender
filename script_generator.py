# title: Blender Script Generator
# description: Generates Blender Python scripts from parsed sketch data using Ollama LLM.
# contact: Taewook Kang(laputa99999@gmail.com)
import requests, json, ast, openai, math
from ollama import chat
from ollama import ChatResponse
from openai import OpenAI
 
OLLAMA_API_URL = "http://localhost:11434"
OLLAMA_MODEL = "gemma3" # "codegemma:7b" or "qwen2.5-coder:7b". Adjust as needed.
MAX_RETRIES = 2

def _create_prompt(json_data_str: str) -> str:
	safe_json_string = json.dumps(json_data_str)
	
	# Script preamble to be copied at the top (remove mathutils import)
	script_preamble = f"""import bpy
import math
import json
# from mathutils import Vector # Do not use this module

# 1. Parse JSON data and initialize scene
# Parse JSON string to Python dictionary
with open("sketch.json", "r", encoding="utf-8") as f:
	json_string = f.read()
	data = json.loads(json_string)

# Scene settings
wall_height = 2.5
wall_thickness = 0.5
wall_objects = [] # List to store created wall objects

# Scene initialization
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
"""

	prompt = f"""
You are a Blender Python script generation expert. Your task is to create a Python script for Blender using the `bpy` module based on the provided JSON data.

**CRITICAL RULES (MUST FOLLOW):**
1.  **START WITH PREAMBLE:** You MUST start your code output with the *entire* 'Script Preamble' section, exactly as written. This includes `import json` and `import math`.
2.  **NO mathutils:** You MUST NOT import or use the `mathutils` or `Vector` module. Use the standard `math` library only.
3.  **NO ANNOTATIONS:** You MUST completely ignore any element with type `'annotation'`. DO NOT create text objects.
4.  **NO MODIFYING PREAMBLE:** You MUST NOT change any part like json_string of the 'Script Preamble'. It must remain exactly as provided.
5.  **NO BMESH:** You MUST NOT use the `bmesh` module. Use `bpy.ops.mesh.primitive_cube_add()`.
6.  **NO HELPER FUNCTIONS:** Do NOT define helper functions. Write all logic in the main script scope.
7.  **3D VECTORS:** All `location` parameters for `bpy.ops` MUST be 3-item tuples `(x, y, z)`. DO NOT pass 2-item lists.
8.  **OUTPUT:** Provide ONLY the pure Python code. No explanations, no markdown.

---
**Script Preamble (Use this exact code at the top):**
{script_preamble}
---

**Logic for Wall Creation (Follow these steps exactly):**

1.  Loop through `data['elements']`.
2.  If `element['type'] == 'wall'`:
	* Get `start = element['start']` and `end = element['end']`.
	* Calculate `length = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)`.
	* Calculate `angle = math.atan2(end[1] - start[1], end[0] - start[0])`.
	* **Calculate 3D Center:** `center_3d = ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2, wall_height / 2)`. (This MUST be a 3D tuple).
	* **Create Cube:** Call `bpy.ops.mesh.primitive_cube_add(location=center_3d)`.
	* Get the new object: `wall = bpy.context.object`.
	* Set rotation: `wall.rotation_euler[2] = angle`.
	* Set Dimensions: `wall.dimensions = (length, wall_thickness, wall_height)`.
	* Add to list: `wall_objects.append(wall)`.

---
**Logic for Hole Creation (Doors/Windows - Follow these steps exactly):**

1.  Loop through `data['elements']` a **SECOND TIME**.
2.  If `element['type'] == 'door'` or `element['type'] == 'window'`:
	* Get `position = element['position']` (this is a 2D position [x, y]).
	* Define `door_size = (0.9, 2.1)` and `window_size = (1.2, 1.2)`.
	* Set `hole_z_pos` = 1.05 for 'door', 1.5 for 'window'.
	* Set `hole_dims` = `(door_size[0], wall_thickness * 2, door_size[1])` for 'door' or `(window_size[0], wall_thickness * 2, window_size[1])` for 'window'.
	* **Find Closest Wall (Using standard math):**
		* Initialize `min_dist = float('inf')` and `closest_wall = None`.
		* `hole_pos_2d = (position[0], position[1])`
		* Loop through `wall_objects`:
			* `wall_pos_2d = (wall.location[0], wall.location[1])`
			* `dist = math.sqrt((hole_pos_2d[0] - wall_pos_2d[0])**2 + (hole_pos_2d[1] - wall_pos_2d[1])**2)`
			* If `dist < min_dist`: `min_dist = dist`, `closest_wall = wall`.
	* If `closest_wall is not None`:
		* **Calculate 3D Cutter Location:** `cutter_location_3d = (position[0], position[1], hole_z_pos)`. (This MUST be a 3D tuple).
		* **Create Cutter:** `bpy.ops.mesh.primitive_cube_add(location=cutter_location_3d)`.
		* Get the cutter: `cutter = bpy.context.object`.
		* Set cutter dimensions: `cutter.dimensions = hole_dims`.
		* **Align Cutter:** `cutter.rotation_euler[2] = closest_wall.rotation_euler[2]`.
		* **Apply Boolean (Follow exactly):**
			1.  `bpy.context.view_layer.objects.active = closest_wall`
			2.  `mod = closest_wall.modifiers.new(name="Hole", type='BOOLEAN')`
			3.  `mod.object = cutter`
			4.  `mod.operation = 'DIFFERENCE'`
			5.  `bpy.ops.object.modifier_apply(modifier=mod.name)`
			6.  `bpy.data.objects.remove(cutter, do_unlink=True)`

---
**Final Script (Provide only this):**
"""
	
	return prompt.strip()

	
def _fix_code_prompt(code: str, error: str) -> str:
	prompt = f"""
The following Blender Python script has a syntax error. Please fix it.

**Error:**
```
{error}
```

**Incorrect Code:**
```python
{code}
```

**Corrected Blender Python Script (code only):**
"""
	return prompt

def llm_agent(option, prompt):
	response = chat(
		model=option,
		messages=[{"role": "user", "content": prompt}],
		options={
			'temperature': 0.1
		}
	)
	if response and isinstance(response, ChatResponse):
		return response.message.content
	else:
		raise Exception("Failed to get a valid response from the model")

def generate_blender_script(json_data_str: str, progress_callback=None) -> str:
	prompt = _create_prompt(json_data_str)
	generated_code = ""

	for attempt in range(MAX_RETRIES + 1):
		if progress_callback:
			if attempt == 0:
				progress_callback(f"Calling Ollama model `{OLLAMA_MODEL}`...")
			else:
				progress_callback(f"Script error detected. Attempting to fix... (try {attempt}/{MAX_RETRIES})")

		try:
			# Call Ollama API
			output = llm_agent(OLLAMA_MODEL, prompt)
			generated_code = output

			# In case LLM includes non-code text
			if "```python" in generated_code:
				generated_code = generated_code.split("```python")[1].split("```")[0].strip()
			elif "```" in generated_code:
				 generated_code = generated_code.split("```")[1].split("```")[0].strip()

			# Code validation (Feature 4)
			ast.parse(generated_code)

			if progress_callback:
				progress_callback("Script generation and validation complete!")
			return generated_code # Return code on success

		except requests.exceptions.RequestException as e:
			error_message = f"Ollama server connection error: {e}"
			if progress_callback:
				progress_callback(error_message)
			return f"# ERROR: {error_message}"

		except SyntaxError as e:
			if attempt < MAX_RETRIES:
				prompt = _fix_code_prompt(generated_code, str(e))
				continue # retry
			else:
				error_message = f"Script auto-fix failed: {e}"
				if progress_callback:
					progress_callback(error_message)
				return f"# ERROR: {error_message}\n\n# --- FAILED CODE ---\n{generated_code}"
		except Exception as e:
			error_message = f"Unknown error occurred: {e}"
			if progress_callback:
				progress_callback(error_message)
			return f"# ERROR: {error_message}"

	return "# ERROR: Maximum retry count exceeded."

