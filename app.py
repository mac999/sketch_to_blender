import streamlit as st, os, json
from PIL import Image
from io import BytesIO
from vision_analyzer import analyze_sketch
from script_generator import generate_blender_script

# Streamlit app configuration
st.set_page_config(
	page_title="Sketch to Blender",
	layout="wide",
	initial_sidebar_state="expanded",
)

# Dark mode style  
dark_mode_style = """
<style>
	#root > div:nth-child(1) > div > div > div > div > section > div {
		padding-top: 2rem;
	}
	.stApp {
		background-color: #0E1117;
		color: #FAFAFA;
	}
	h1, h2, h3, h4, h5, h6 {
		color: #FAFAFA;
	}
	.st-emotion-cache-16txtl3 {
		padding: 2rem 1rem 1rem;
	}
</style>
"""
st.markdown(dark_mode_style, unsafe_allow_html=True)

# Callback function
def add_message_to_chat(content, role="assistant"):
	"""Add a message to the chat UI and update the state."""
	st.session_state.messages.append({"role": role, "content": content})
	# Immediately update UI by directly calling chat_message
	with st.chat_message(role):
		st.markdown(content)

# Sidebar
with st.sidebar:
	st.title("Sketch to Blender")
	st.markdown("")
	uploaded_file = st.file_uploader(
		"Upload floor plan sketch image",
		type=["png", "jpg", "jpeg"],
		help="Upload a floor plan sketch containing walls, doors, and windows."
	)
	st.markdown("")
	st.subheader("Status")
	
	# Initialize chat history
	if "messages" not in st.session_state:
		st.session_state.messages = []

	# Display chat history
	for message in st.session_state.messages:
		with st.chat_message(message["role"]):
			st.markdown(message["content"])

# Main panel
st.header("Result")

if uploaded_file is not None:
	uploaded_file.seek(0)
	image_bytes = uploaded_file.read()
	image = Image.open(BytesIO(image_bytes))

	st.image(image, caption="Uploaded Sketch", use_column_width=True)

	# Re-run the whole process when a new file is uploaded
	if "generated_script" not in st.session_state or st.session_state.get("uploaded_file_name") != uploaded_file.name:
		st.session_state.uploaded_file_name = uploaded_file.name
		st.session_state.messages = [] # Reset chat history when a new file is uploaded

		# Call modular functions (pass callback for UI updates)
		parsed_data_json = analyze_sketch(image, progress_callback=add_message_to_chat)

		# Save parsed_data_json to sketch.json file as a string with 4-space indentation
		sketch_json_path = os.path.join(os.path.dirname(__file__), "sketch.json")
		with open(sketch_json_path, "w", encoding="utf-8") as f:
			f.write(json.dumps(parsed_data_json, indent=4, ensure_ascii=False))

		# Display parsed_data_json in Streamlit as markup style
		st.subheader("Analysis Result (JSON)")
		st.markdown(f"```json\n{json.dumps(parsed_data_json, indent=2, ensure_ascii=False)}\n```")

		generated_script = generate_blender_script(parsed_data_json, progress_callback=add_message_to_chat)
		st.session_state.generated_script = generated_script

	st.subheader("Generated Blender Python Script")
	st.code(st.session_state.generated_script, language="python", line_numbers=True)

	st.download_button(
		label="Download Script File (.py)",
		data=st.session_state.generated_script,
		file_name="generated_blender_script.py",
		mime="text/python",
	)

else:
	st.info("Please upload a floor plan sketch image in the sidebar.")

if prompt := st.chat_input("Request script modification (e.g., change wall height to 3 meters)"):
	st.session_state.messages.append({"role": "user", "content": prompt})
	with st.chat_message("user"):
		st.markdown(prompt)

	# Pass the existing Blender script and user request to LLM to generate a modified script
	old_script = st.session_state.get("generated_script", "")
	if not old_script:
		with st.chat_message("assistant"):
			st.write("Please upload a floor plan image first to generate a Blender script.")
	else:
		import requests
		fix_prompt = f"""
You are a Blender Python script expert. The following script was generated for a house model. Please modify the script according to the user's request below.

**User Request:**
{prompt}

**Original Script:**
```python
{old_script}
```

**Modified Blender Python Script (code only):**
"""
try:
	response = requests.post(
		"http://localhost:11434/api/generate",
		json={"model": "qwen2.5-coder:7", "prompt": fix_prompt, "stream": False},
		timeout=60
	)
	response.raise_for_status()
	response_data = response.json()
	new_script = response_data.get("response", "").strip()
	# Extract only code
	if "```python" in new_script:
		new_script = new_script.split("```python")[1].split("```", 1)[0].strip()
	elif "```" in new_script:
		new_script = new_script.split("```", 1)[1].split("```", 1)[0].strip()
	st.session_state.generated_script = new_script
	st.session_state.messages.append({"role": "assistant", "content": "Modified Blender script generated."})
	with st.chat_message("assistant"):
		st.code(new_script, language="python", line_numbers=True)

except Exception as e:
	st.session_state.messages.append({"role": "assistant", "content": f"Error occurred while modifying script: {e}"})
	with st.chat_message("assistant"):
		st.write(f"Error occurred while modifying script: {e}")
