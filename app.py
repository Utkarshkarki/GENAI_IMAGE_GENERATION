import streamlit as st
import os
from dotenv import load_dotenv
from services import (
    lifestyle_shot_by_image,
    lifestyle_shot_by_text,
    add_shadow,
    create_packshot,
    enhance_prompt,
    generative_fill,
    generate_hd_image,
    erase_foreground,
    parse_intent,
    execute_plan,
)
from services.memory import (
    save_preference,
    get_preferences,
    clear_preference,
    clear_all_preferences,
    merge_with_preferences,
)
from PIL import Image
import io
import requests
import json
import time
import base64
from streamlit_drawable_canvas import st_canvas
import numpy as np
from services.erase_foreground import erase_foreground

# Configure Streamlit page
st.set_page_config(
    page_title="AdSnap Studio",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load environment variables
print("Loading environment variables...")
load_dotenv(verbose=True)  # Add verbose=True to see loading details

# Debug: Print environment variable status
api_key = os.getenv("BRIA_API_KEY")
print(f"API Key present: {bool(api_key)}")
print(f"API Key value: {api_key if api_key else 'Not found'}")
print(f"Current working directory: {os.getcwd()}")
print(f".env file exists: {os.path.exists('.env')}")

def initialize_session_state():
    """Initialize session state variables."""
    if 'api_key' not in st.session_state:
        st.session_state.api_key = os.getenv('BRIA_API_KEY')
    if 'generated_images' not in st.session_state:
        st.session_state.generated_images = []
    if 'current_image' not in st.session_state:
        st.session_state.current_image = None
    if 'pending_urls' not in st.session_state:
        st.session_state.pending_urls = []
    if 'edited_image' not in st.session_state:
        st.session_state.edited_image = None
    if 'original_prompt' not in st.session_state:
        st.session_state.original_prompt = ""
    if 'enhanced_prompt' not in st.session_state:
        st.session_state.enhanced_prompt = None
    if 'session_gallery' not in st.session_state:
        st.session_state.session_gallery = []  # list of {url, label, timestamp}
    if 'show_welcome' not in st.session_state:
        st.session_state.show_welcome = True
    if 'agent_memory' not in st.session_state:
        st.session_state.agent_memory = {}
    if 'agent_history' not in st.session_state:
        st.session_state.agent_history = []  # list of {role, content, images}
    if 'agent_pending_plan' not in st.session_state:
        st.session_state.agent_pending_plan = None
    if 'agent_uploaded_image' not in st.session_state:
        st.session_state.agent_uploaded_image = None
    if 'ollama_model' not in st.session_state:
        st.session_state.ollama_model = 'llama3'
    if 'ollama_url' not in st.session_state:
        st.session_state.ollama_url = 'http://localhost:11434'

def download_image(url):
    """Download image from URL and return as bytes."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.content
    except Exception as e:
        st.error(f"Error downloading image: {str(e)}")
        return None

def add_to_gallery(url: str, label: str = "Generated"):
    """Add an image URL to the session gallery (avoid duplicates)."""
    if url and not any(item["url"] == url for item in st.session_state.session_gallery):
        st.session_state.session_gallery.append({
            "url": url,
            "label": label,
            "index": len(st.session_state.session_gallery) + 1,
        })

def apply_image_filter(image, filter_type):
    """Apply various filters to the image."""
    try:
        img = Image.open(io.BytesIO(image)) if isinstance(image, bytes) else Image.open(image)
        
        if filter_type == "Grayscale":
            return img.convert('L')
        elif filter_type == "Sepia":
            width, height = img.size
            pixels = img.load()
            for x in range(width):
                for y in range(height):
                    r, g, b = img.getpixel((x, y))[:3]
                    tr = int(0.393 * r + 0.769 * g + 0.189 * b)
                    tg = int(0.349 * r + 0.686 * g + 0.168 * b)
                    tb = int(0.272 * r + 0.534 * g + 0.131 * b)
                    img.putpixel((x, y), (min(tr, 255), min(tg, 255), min(tb, 255)))
            return img
        elif filter_type == "High Contrast":
            return img.point(lambda x: x * 1.5)
        elif filter_type == "Blur":
            return img.filter(Image.BLUR)
        else:
            return img
    except Exception as e:
        st.error(f"Error applying filter: {str(e)}")
        return None

def check_generated_images():
    """Check if pending images are ready and update the display."""
    if st.session_state.pending_urls:
        ready_images = []
        still_pending = []
        
        for url in st.session_state.pending_urls:
            try:
                response = requests.head(url)
                # Consider an image ready if we get a 200 response with any content length
                if response.status_code == 200:
                    ready_images.append(url)
                else:
                    still_pending.append(url)
            except Exception as e:
                still_pending.append(url)
        
        # Update the pending URLs list
        st.session_state.pending_urls = still_pending
        
        # If we found any ready images, update the display
        if ready_images:
            st.session_state.edited_image = ready_images[0]  # Display the first ready image
            if len(ready_images) > 1:
                st.session_state.generated_images = ready_images  # Store all ready images
            return True
            
    return False

def auto_check_images(status_container):
    """Automatically check for image completion a few times."""
    max_attempts = 3
    attempt = 0
    while attempt < max_attempts and st.session_state.pending_urls:
        time.sleep(2)  # Wait 2 seconds between checks
        if check_generated_images():
            status_container.success("✨ Image ready!")
            return True
        attempt += 1
    return False

def main():
    st.title("AdSnap Studio")
    initialize_session_state()

    # ── Welcome Banner (first-time only) ──────────────────────────────
    if st.session_state.show_welcome:
        with st.container(border=True):
            col_icon, col_text, col_close = st.columns([0.5, 8.5, 1])
            with col_icon:
                st.markdown("## 🌟")
            with col_text:
                st.markdown("### Welcome to **AdSnap Studio**!")
                st.markdown(
                    "AdSnap Studio uses **Bria AI** to generate and edit product images. "
                    "Here's how to get started:"
                )
                st.markdown(
                    """
| Step | What to do |
|------|------------|
| 1️⃣  | Paste your **Bria API key** in the sidebar → |
| 2️⃣  | Pick a tab: **Generate Image**, **Lifestyle Shot**, **Generative Fill**, or **Erase Elements** |
| 3️⃣  | Enter a prompt or upload a product image and hit the action button |
| 4️⃣  | Your results appear inline — and are saved to the **Session Gallery** at the bottom |
| 5️⃣  | Try the **🤖 AI Agent** tab — describe what you want in plain English and the agent plans & runs the right steps automatically! |
"""
                )
            with col_close:
                if st.button("❌ Dismiss", key="dismiss_welcome"):
                    st.session_state.show_welcome = False
                    st.rerun()

    # Sidebar for API key + Ollama settings + Agent Memory
    with st.sidebar:
        st.header("Settings")
        api_key = st.text_input("Enter your API key:", value=st.session_state.api_key if st.session_state.api_key else "", type="password")
        if api_key:
            st.session_state.api_key = api_key

        st.divider()
        st.subheader("🤖 AI Agent — Ollama")
        st.session_state.ollama_model = st.selectbox(
            "Ollama Model",
            ["llama3", "mistral", "phi3", "gemma3"],
            index=["llama3", "mistral", "phi3", "gemma3"].index(st.session_state.ollama_model),
        )
        st.session_state.ollama_url = st.text_input(
            "Ollama URL", value=st.session_state.ollama_url
        )

        # Agent memory panel
        prefs = get_preferences()
        if prefs:
            st.divider()
            st.subheader("🧠 Agent Memory")
            for k, v in list(prefs.items()):
                cols = st.columns([4, 1])
                cols[0].markdown(f"**{k}:** `{v}`")
                if cols[1].button("✕", key=f"mem_del_{k}"):
                    clear_preference(k)
                    st.rerun()
            if st.button("🗑️ Clear All Memory"):
                clear_all_preferences()
                st.rerun()

    # Main tabs
    tabs = st.tabs([
        "🎨 Generate Image",
        "🖼️ Lifestyle Shot",
        "🎨 Generative Fill",
        "🎨 Erase Elements",
        "🤖 AI Agent",
    ])
    
    # Generate Images Tab
    with tabs[0]:
        st.header("Generate Images")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            # Prompt input
            prompt = st.text_area("Enter your prompt", 
                                value="",
                                height=100,
                                key="prompt_input")
            
            # Store original prompt in session state when it changes
            if "original_prompt" not in st.session_state:
                st.session_state.original_prompt = prompt
            elif prompt != st.session_state.original_prompt:
                st.session_state.original_prompt = prompt
                st.session_state.enhanced_prompt = None  # Reset enhanced prompt when original changes
            
            # Enhanced prompt display
            if st.session_state.get('enhanced_prompt'):
                st.markdown("**Enhanced Prompt:**")
                st.markdown(f"*{st.session_state.enhanced_prompt}*")
            
            # Enhance Prompt button
            if st.button("✨ Enhance Prompt", key="enhance_button"):
                if not prompt:
                    st.warning("Please enter a prompt to enhance.")
                else:
                    with st.spinner("Enhancing prompt..."):
                        try:
                            result = enhance_prompt(st.session_state.api_key, prompt)
                            if result:
                                st.session_state.enhanced_prompt = result
                                st.success("Prompt enhanced!")
                                st.rerun()  # Rerun to update the display
                        except Exception as e:
                            st.error(f"Error enhancing prompt: {str(e)}")
                            

        
        with col2:
            num_images = st.slider("Number of images", 1, 4, 1)
            aspect_ratio = st.selectbox("Aspect ratio", ["1:1", "16:9", "9:16", "4:3", "3:4"])
            enhance_img = st.checkbox("Enhance image quality", value=True)
            
            # Style options
            st.subheader("Style Options")
            style = st.selectbox("Image Style", [
                "Realistic", "Artistic", "Cartoon", "Sketch", 
                "Watercolor", "Oil Painting", "Digital Art"
            ])
            
            # Add style to prompt
            if style and style != "Realistic":
                prompt = f"{prompt}, in {style.lower()} style"
        
        # Generate button
        if st.button("🎨 Generate Images", type="primary"):
            if not st.session_state.api_key:
                st.error("Please enter your API key in the sidebar.")
                return
                
            with st.spinner("🎨 Generating your masterpiece..."):
                try:
                    # Convert aspect ratio to proper format
                    result = generate_hd_image(
                        prompt=st.session_state.enhanced_prompt or prompt,
                        api_key=st.session_state.api_key,
                        num_results=num_images,
                        aspect_ratio=aspect_ratio,  # Already in correct format (e.g. "1:1")
                        sync=True,  # Wait for results
                        enhance_image=enhance_img,
                        medium="art" if style != "Realistic" else "photography",
                        prompt_enhancement=False,  # We're already using our own prompt enhancement
                        content_moderation=True  # Enable content moderation by default
                    )
                    
                    if result:
                        
                        if isinstance(result, dict):
                            if "result_url" in result:
                                st.session_state.edited_image = result["result_url"]
                                add_to_gallery(result["result_url"], "Generate")
                                st.success("✨ Image generated successfully!")
                            elif "result_urls" in result:
                                st.session_state.edited_image = result["result_urls"][0]
                                add_to_gallery(result["result_urls"][0], "Generate")
                                st.success("✨ Image generated successfully!")
                            elif "result" in result and isinstance(result["result"], list):
                                for item in result["result"]:
                                    if isinstance(item, dict) and "urls" in item:
                                        st.session_state.edited_image = item["urls"][0]
                                        add_to_gallery(item["urls"][0], "Generate")
                                        st.success("✨ Image generated successfully!")
                                        break
                                    elif isinstance(item, list) and len(item) > 0:
                                        st.session_state.edited_image = item[0]
                                        add_to_gallery(item[0], "Generate")
                                        st.success("✨ Image generated successfully!")
                                        break
                        else:
                            st.error("No valid result format found in the API response.")
                            
                except Exception as e:
                    st.error(f"Error generating images: {str(e)}")
    
    # Product Photography Tab
    with tabs[1]:
        st.header("Product Photography")
        
        uploaded_file = st.file_uploader("Upload Product Image", type=["png", "jpg", "jpeg"], key="product_upload")
        if uploaded_file:
            col1, col2 = st.columns(2)
            
            with col1:
                st.image(uploaded_file, caption="Original Image", use_column_width=True)
                
                # Product editing options
                edit_option = st.selectbox("Select Edit Option", [
                    "Create Packshot",
                    "Add Shadow",
                    "Lifestyle Shot"
                ])
                
                if edit_option == "Create Packshot":
                    col_a, col_b = st.columns(2)
                    with col_a:
                        bg_color = st.color_picker("Background Color", "#FFFFFF")
                        sku = st.text_input("SKU (optional)", "")
                    with col_b:
                        force_rmbg = st.checkbox("Force Background Removal", False)
                        content_moderation = st.checkbox("Enable Content Moderation", False)
                    
                    if st.button("Create Packshot"):
                        with st.spinner("Creating professional packshot..."):
                            try:
                                # First remove background if needed
                                if force_rmbg:
                                    from services.background_service import remove_background
                                    bg_result = remove_background(
                                        st.session_state.api_key,
                                        uploaded_file.getvalue(),
                                        content_moderation=content_moderation
                                    )
                                    if bg_result and "result_url" in bg_result:
                                        # Download the background-removed image
                                        response = requests.get(bg_result["result_url"])
                                        if response.status_code == 200:
                                            image_data = response.content
                                        else:
                                            st.error("Failed to download background-removed image")
                                            return
                                    else:
                                        st.error("Background removal failed")
                                        return
                                else:
                                    image_data = uploaded_file.getvalue()
                                
                                # Now create packshot
                                result = create_packshot(
                                    st.session_state.api_key,
                                    image_data,
                                    background_color=bg_color,
                                    sku=sku if sku else None,
                                    force_rmbg=force_rmbg,
                                    content_moderation=content_moderation
                                )
                                
                                if result and "result_url" in result:
                                    st.success("✨ Packshot created successfully!")
                                    st.session_state.edited_image = result["result_url"]
                                    add_to_gallery(result["result_url"], "Packshot")
                                else:
                                    st.error("No result URL in the API response. Please try again.")
                            except Exception as e:
                                st.error(f"Error creating packshot: {str(e)}")
                                if "422" in str(e):
                                    st.warning("Content moderation failed. Please ensure the image is appropriate.")
                
                elif edit_option == "Add Shadow":
                    col_a, col_b = st.columns(2)
                    with col_a:
                        shadow_type = st.selectbox("Shadow Type", ["Natural", "Drop"])
                        bg_color = st.color_picker("Background Color (optional)", "#FFFFFF")
                        use_transparent_bg = st.checkbox("Use Transparent Background", True)
                        shadow_color = st.color_picker("Shadow Color", "#000000")
                        sku = st.text_input("SKU (optional)", "")
                        
                        # Shadow offset
                        st.subheader("Shadow Offset")
                        offset_x = st.slider("X Offset", -50, 50, 0)
                        offset_y = st.slider("Y Offset", -50, 50, 15)
                    
                    with col_b:
                        shadow_intensity = st.slider("Shadow Intensity", 0, 100, 60)
                        shadow_blur = st.slider("Shadow Blur", 0, 50, 15 if shadow_type.lower() == "regular" else 20)
                        
                        # Float shadow specific controls
                        if shadow_type == "Float":
                            st.subheader("Float Shadow Settings")
                            shadow_width = st.slider("Shadow Width", -100, 100, 0)
                            shadow_height = st.slider("Shadow Height", -100, 100, 70)
                        
                        force_rmbg = st.checkbox("Force Background Removal", False)
                        content_moderation = st.checkbox("Enable Content Moderation", False)
                    
                    if st.button("Add Shadow"):
                        with st.spinner("Adding shadow effect..."):
                            try:
                                result = add_shadow(
                                    api_key=st.session_state.api_key,
                                    image_data=uploaded_file.getvalue(),
                                    shadow_type=shadow_type.lower(),
                                    background_color=None if use_transparent_bg else bg_color,
                                    shadow_color=shadow_color,
                                    shadow_offset=[offset_x, offset_y],
                                    shadow_intensity=shadow_intensity,
                                    shadow_blur=shadow_blur,
                                    shadow_width=shadow_width if shadow_type == "Float" else None,
                                    shadow_height=shadow_height if shadow_type == "Float" else 70,
                                    sku=sku if sku else None,
                                    force_rmbg=force_rmbg,
                                    content_moderation=content_moderation
                                )
                                
                                if result and "result_url" in result:
                                    st.success("✨ Shadow added successfully!")
                                    st.session_state.edited_image = result["result_url"]
                                    add_to_gallery(result["result_url"], "Shadow")
                                else:
                                    st.error("No result URL in the API response. Please try again.")
                            except Exception as e:
                                st.error(f"Error adding shadow: {str(e)}")
                                if "422" in str(e):
                                    st.warning("Content moderation failed. Please ensure the image is appropriate.")
                
                elif edit_option == "Lifestyle Shot":
                    shot_type = st.radio("Shot Type", ["Text Prompt", "Reference Image"])
                    
                    # Common settings for both types
                    col1, col2 = st.columns(2)
                    with col1:
                        placement_type = st.selectbox("Placement Type", [
                            "Original", "Automatic", "Manual Placement",
                            "Manual Padding", "Custom Coordinates"
                        ])
                        num_results = st.slider("Number of Results", 1, 8, 4)
                        sync_mode = st.checkbox("Synchronous Mode", False,
                            help="Wait for results instead of getting URLs immediately")
                        original_quality = st.checkbox("Original Quality", False,
                            help="Maintain original image quality")
                        
                        if placement_type == "Manual Placement":
                            positions = st.multiselect("Select Positions", [
                                "Upper Left", "Upper Right", "Bottom Left", "Bottom Right",
                                "Right Center", "Left Center", "Upper Center",
                                "Bottom Center", "Center Vertical", "Center Horizontal"
                            ], ["Upper Left"])
                        
                        elif placement_type == "Manual Padding":
                            st.subheader("Padding Values (pixels)")
                            pad_left = st.number_input("Left Padding", 0, 1000, 0)
                            pad_right = st.number_input("Right Padding", 0, 1000, 0)
                            pad_top = st.number_input("Top Padding", 0, 1000, 0)
                            pad_bottom = st.number_input("Bottom Padding", 0, 1000, 0)
                        
                        elif placement_type in ["Automatic", "Manual Placement", "Custom Coordinates"]:
                            st.subheader("Shot Size")
                            shot_width = st.number_input("Width", 100, 2000, 1000)
                            shot_height = st.number_input("Height", 100, 2000, 1000)
                    
                    with col2:
                        if placement_type == "Custom Coordinates":
                            st.subheader("Product Position")
                            fg_width = st.number_input("Product Width", 50, 1000, 500)
                            fg_height = st.number_input("Product Height", 50, 1000, 500)
                            fg_x = st.number_input("X Position", -500, 1500, 0)
                            fg_y = st.number_input("Y Position", -500, 1500, 0)
                        
                        sku = st.text_input("SKU (optional)")
                        force_rmbg = st.checkbox("Force Background Removal", False)
                        content_moderation = st.checkbox("Enable Content Moderation", False)
                        
                        if shot_type == "Text Prompt":
                            fast_mode = st.checkbox("Fast Mode", True,
                                help="Balance between speed and quality")
                            optimize_desc = st.checkbox("Optimize Description", True,
                                help="Enhance scene description using AI")
                            if not fast_mode:
                                exclude_elements = st.text_area("Exclude Elements (optional)",
                                    help="Elements to exclude from the generated scene")
                        else:  # Reference Image
                            enhance_ref = st.checkbox("Enhance Reference Image", True,
                                help="Improve lighting, shadows, and texture")
                            ref_influence = st.slider("Reference Influence", 0.0, 1.0, 1.0,
                                help="Control similarity to reference image")
                    
                    if shot_type == "Text Prompt":
                        prompt = st.text_area("Describe the environment")
                        if st.button("Generate Lifestyle Shot") and prompt:
                            with st.spinner("Generating lifestyle shot..."):
                                try:
                                    # Convert placement selections to API format
                                    if placement_type == "Manual Placement":
                                        manual_placements = [p.lower().replace(" ", "_") for p in positions]
                                    else:
                                        manual_placements = ["upper_left"]
                                    
                                    result = lifestyle_shot_by_text(
                                        api_key=st.session_state.api_key,
                                        image_data=uploaded_file.getvalue(),
                                        scene_description=prompt,
                                        placement_type=placement_type.lower().replace(" ", "_"),
                                        num_results=num_results,
                                        sync=sync_mode,
                                        fast=fast_mode,
                                        optimize_description=optimize_desc,
                                        shot_size=[shot_width, shot_height] if placement_type != "Original" else [1000, 1000],
                                        original_quality=original_quality,
                                        exclude_elements=exclude_elements if not fast_mode else None,
                                        manual_placement_selection=manual_placements,
                                        padding_values=[pad_left, pad_right, pad_top, pad_bottom] if placement_type == "Manual Padding" else [0, 0, 0, 0],
                                        foreground_image_size=[fg_width, fg_height] if placement_type == "Custom Coordinates" else None,
                                        foreground_image_location=[fg_x, fg_y] if placement_type == "Custom Coordinates" else None,
                                        force_rmbg=force_rmbg,
                                        content_moderation=content_moderation,
                                        sku=sku if sku else None
                                    )
                                    
                                    if result:
                                        if sync_mode:
                                            if isinstance(result, dict):
                                                if "result_url" in result:
                                                    st.session_state.edited_image = result["result_url"]
                                                    add_to_gallery(result["result_url"], "Lifestyle Shot")
                                                    st.success("✨ Image generated successfully!")
                                                elif "result_urls" in result:
                                                    st.session_state.edited_image = result["result_urls"][0]
                                                    add_to_gallery(result["result_urls"][0], "Lifestyle Shot")
                                                    st.success("✨ Image generated successfully!")
                                                elif "result" in result and isinstance(result["result"], list):
                                                    for item in result["result"]:
                                                        if isinstance(item, dict) and "urls" in item:
                                                            st.session_state.edited_image = item["urls"][0]
                                                            add_to_gallery(item["urls"][0], "Lifestyle Shot")
                                                            st.success("✨ Image generated successfully!")
                                                            break
                                                        elif isinstance(item, list) and len(item) > 0:
                                                            st.session_state.edited_image = item[0]
                                                            add_to_gallery(item[0], "Lifestyle Shot")
                                                            st.success("✨ Image generated successfully!")
                                                            break
                                                elif "urls" in result:
                                                    st.session_state.edited_image = result["urls"][0]
                                                    add_to_gallery(result["urls"][0], "Lifestyle Shot")
                                                    st.success("✨ Image generated successfully!")
                                        else:
                                            urls = []
                                            if isinstance(result, dict):
                                                if "urls" in result:
                                                    urls.extend(result["urls"][:num_results])  # Limit to requested number
                                                elif "result" in result and isinstance(result["result"], list):
                                                    # Process each result item
                                                    for item in result["result"]:
                                                        if isinstance(item, dict) and "urls" in item:
                                                            urls.extend(item["urls"])
                                                        elif isinstance(item, list):
                                                            urls.extend(item)
                                                        # Break if we have enough URLs
                                                        if len(urls) >= num_results:
                                                            break
                                                    
                                                    # Trim to requested number
                                                    urls = urls[:num_results]
                                            
                                            if urls:
                                                st.session_state.pending_urls = urls
                                                
                                                # Create a container for status messages
                                                status_container = st.empty()
                                                refresh_container = st.empty()
                                                
                                                # Show initial status
                                                status_container.info(f"🎨 Generation started! Waiting for {len(urls)} image{'s' if len(urls) > 1 else ''}...")
                                                
                                                # Try automatic checking first
                                                if auto_check_images(status_container):
                                                    st.rerun()
                                                
                                                # Add refresh button for manual checking
                                                if refresh_container.button("🔄 Check for Generated Images"):
                                                    with st.spinner("Checking for completed images..."):
                                                        if check_generated_images():
                                                            status_container.success("✨ Image ready!")
                                                            st.rerun()
                                                        else:
                                                            status_container.warning(f"⏳ Still generating your image{'s' if len(urls) > 1 else ''}... Please check again in a moment.")
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
                                    if "422" in str(e):
                                        st.warning("Content moderation failed. Please ensure the content is appropriate.")
                    else:
                        ref_image = st.file_uploader("Upload Reference Image", type=["png", "jpg", "jpeg"], key="ref_upload")
                        if st.button("Generate Lifestyle Shot") and ref_image:
                            with st.spinner("Generating lifestyle shot..."):
                                try:
                                    # Convert placement selections to API format
                                    if placement_type == "Manual Placement":
                                        manual_placements = [p.lower().replace(" ", "_") for p in positions]
                                    else:
                                        manual_placements = ["upper_left"]
                                    
                                    result = lifestyle_shot_by_image(
                                        api_key=st.session_state.api_key,
                                        image_data=uploaded_file.getvalue(),
                                        reference_image=ref_image.getvalue(),
                                        placement_type=placement_type.lower().replace(" ", "_"),
                                        num_results=num_results,
                                        sync=sync_mode,
                                        shot_size=[shot_width, shot_height] if placement_type != "Original" else [1000, 1000],
                                        original_quality=original_quality,
                                        manual_placement_selection=manual_placements,
                                        padding_values=[pad_left, pad_right, pad_top, pad_bottom] if placement_type == "Manual Padding" else [0, 0, 0, 0],
                                        foreground_image_size=[fg_width, fg_height] if placement_type == "Custom Coordinates" else None,
                                        foreground_image_location=[fg_x, fg_y] if placement_type == "Custom Coordinates" else None,
                                        force_rmbg=force_rmbg,
                                        content_moderation=content_moderation,
                                        sku=sku if sku else None,
                                        enhance_ref_image=enhance_ref,
                                        ref_image_influence=ref_influence
                                    )
                                    
                                    if result:
                                        if sync_mode:
                                            if isinstance(result, dict):
                                                if "result_url" in result:
                                                    st.session_state.edited_image = result["result_url"]
                                                    add_to_gallery(result["result_url"], "Lifestyle Shot")
                                                    st.success("✨ Image generated successfully!")
                                                elif "result_urls" in result:
                                                    st.session_state.edited_image = result["result_urls"][0]
                                                    add_to_gallery(result["result_urls"][0], "Lifestyle Shot")
                                                    st.success("✨ Image generated successfully!")
                                                elif "result" in result and isinstance(result["result"], list):
                                                    for item in result["result"]:
                                                        if isinstance(item, dict) and "urls" in item:
                                                            st.session_state.edited_image = item["urls"][0]
                                                            add_to_gallery(item["urls"][0], "Lifestyle Shot")
                                                            st.success("✨ Image generated successfully!")
                                                            break
                                                        elif isinstance(item, list) and len(item) > 0:
                                                            st.session_state.edited_image = item[0]
                                                            add_to_gallery(item[0], "Lifestyle Shot")
                                                            st.success("✨ Image generated successfully!")
                                                            break
                                                elif "urls" in result:
                                                    st.session_state.edited_image = result["urls"][0]
                                                    add_to_gallery(result["urls"][0], "Lifestyle Shot")
                                                    st.success("✨ Image generated successfully!")
                                        else:
                                            urls = []
                                            if isinstance(result, dict):
                                                if "urls" in result:
                                                    urls.extend(result["urls"][:num_results])  # Limit to requested number
                                                elif "result" in result and isinstance(result["result"], list):
                                                    # Process each result item
                                                    for item in result["result"]:
                                                        if isinstance(item, dict) and "urls" in item:
                                                            urls.extend(item["urls"])
                                                        elif isinstance(item, list):
                                                            urls.extend(item)
                                                        # Break if we have enough URLs
                                                        if len(urls) >= num_results:
                                                            break
                                                    
                                                    # Trim to requested number
                                                    urls = urls[:num_results]
                                            
                                            if urls:
                                                st.session_state.pending_urls = urls
                                                
                                                # Create a container for status messages
                                                status_container = st.empty()
                                                refresh_container = st.empty()
                                                
                                                # Show initial status
                                                status_container.info(f"🎨 Generation started! Waiting for {len(urls)} image{'s' if len(urls) > 1 else ''}...")
                                                
                                                # Try automatic checking first
                                                if auto_check_images(status_container):
                                                    st.rerun()
                                                
                                                # Add refresh button for manual checking
                                                if refresh_container.button("🔄 Check for Generated Images"):
                                                    with st.spinner("Checking for completed images..."):
                                                        if check_generated_images():
                                                            status_container.success("✨ Image ready!")
                                                            st.rerun()
                                                        else:
                                                            status_container.warning(f"⏳ Still generating your image{'s' if len(urls) > 1 else ''}... Please check again in a moment.")
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
                                    if "422" in str(e):
                                        st.warning("Content moderation failed. Please ensure the content is appropriate.")
            
            with col2:
                if st.session_state.edited_image:
                    st.image(st.session_state.edited_image, caption="Edited Image", use_column_width=True)
                    image_data = download_image(st.session_state.edited_image)
                    if image_data:
                        st.download_button(
                            "⬇️ Download Result",
                            image_data,
                            "edited_product.png",
                            "image/png"
                        )
                elif st.session_state.pending_urls:
                    st.info("Images are being generated. Click the refresh button above to check if they're ready.")

    # Generative Fill Tab
    with tabs[2]:
        st.header("🎨 Generative Fill")
        st.markdown("Draw a mask on the image and describe what you want to generate in that area.")
        
        uploaded_file = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg"], key="fill_upload")
        if uploaded_file:
            # Create columns for original image and canvas
            col1, col2 = st.columns(2)
            
            with col1:
                # Display original image
                st.image(uploaded_file, caption="Original Image", use_column_width=True)
                
                # Get image dimensions for canvas
                img = Image.open(uploaded_file)
                img_width, img_height = img.size
                
                # Calculate aspect ratio and set canvas height
                aspect_ratio = img_height / img_width
                canvas_width = min(img_width, 800)  # Max width of 800px
                canvas_height = int(canvas_width * aspect_ratio)
                
                # Resize image to match canvas dimensions
                img = img.resize((canvas_width, canvas_height))
                
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Convert to numpy array with proper shape and type
                img_array = np.array(img).astype(np.uint8)
                
                # Add drawing canvas using Streamlit's drawing canvas component
                stroke_width = st.slider("Brush width", 1, 50, 20)
                stroke_color = st.color_picker("Brush color", "#fff")
                drawing_mode = "freedraw"
                
                # Create canvas with background image
                canvas_result = st_canvas(
                    fill_color="rgba(255, 255, 255, 0.0)",  # Transparent fill
                    stroke_width=stroke_width,
                    stroke_color=stroke_color,
                    drawing_mode=drawing_mode,
                    background_color="",  # Transparent background
                    background_image=img if img_array.shape[-1] == 3 else None,  # Only pass RGB images
                    height=canvas_height,
                    width=canvas_width,
                    key="canvas",
                )
                
                # Options for generation
                st.subheader("Generation Options")
                prompt = st.text_area("Describe what to generate in the masked area")
                negative_prompt = st.text_area("Describe what to avoid (optional)")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    num_results = st.slider("Number of variations", 1, 4, 1)
                    sync_mode = st.checkbox("Synchronous Mode", False,
                        help="Wait for results instead of getting URLs immediately",
                        key="gen_fill_sync_mode")
                
                with col_b:
                    seed = st.number_input("Seed (optional)", min_value=0, value=0,
                        help="Use same seed to reproduce results")
                    content_moderation = st.checkbox("Enable Content Moderation", False,
                        key="gen_fill_content_mod")
                
                if st.button("🎨 Generate", type="primary"):
                    if not prompt:
                        st.error("Please enter a prompt describing what to generate.")
                        return
                    
                    if canvas_result.image_data is None:
                        st.error("Please draw a mask on the image first.")
                        return
                    
                    # Convert canvas result to mask
                    mask_img = Image.fromarray(canvas_result.image_data.astype('uint8'), mode='RGBA')
                    mask_img = mask_img.convert('L')
                    
                    # Convert mask to bytes
                    mask_bytes = io.BytesIO()
                    mask_img.save(mask_bytes, format='PNG')
                    mask_bytes = mask_bytes.getvalue()
                    
                    # Convert uploaded image to bytes
                    image_bytes = uploaded_file.getvalue()
                    
                    with st.spinner("🎨 Generating..."):
                        try:
                            result = generative_fill(
                                st.session_state.api_key,
                                image_bytes,
                                mask_bytes,
                                prompt,
                                negative_prompt=negative_prompt if negative_prompt else None,
                                num_results=num_results,
                                sync=sync_mode,
                                seed=seed if seed != 0 else None,
                                content_moderation=content_moderation
                            )
                            
                            if result:
                                if sync_mode:
                                    if "urls" in result and result["urls"]:
                                        st.session_state.edited_image = result["urls"][0]
                                        add_to_gallery(result["urls"][0], "Gen Fill")
                                        if len(result["urls"]) > 1:
                                            st.session_state.generated_images = result["urls"]
                                        st.success("✨ Generation complete!")
                                    elif "result_url" in result:
                                        st.session_state.edited_image = result["result_url"]
                                        add_to_gallery(result["result_url"], "Gen Fill")
                                        st.success("✨ Generation complete!")
                                else:
                                    if "urls" in result:
                                        st.session_state.pending_urls = result["urls"][:num_results]
                                        
                                        # Create containers for status
                                        status_container = st.empty()
                                        refresh_container = st.empty()
                                        
                                        # Show initial status
                                        status_container.info(f"🎨 Generation started! Waiting for {len(st.session_state.pending_urls)} image{'s' if len(st.session_state.pending_urls) > 1 else ''}...")
                                        
                                        # Try automatic checking
                                        if auto_check_images(status_container):
                                            st.rerun()
                                        
                                        # Add refresh button
                                        if refresh_container.button("🔄 Check for Generated Images"):
                                            if check_generated_images():
                                                status_container.success("✨ Images ready!")
                                                st.rerun()
                                            else:
                                                status_container.warning("⏳ Still generating... Please check again in a moment.")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
            
            with col2:
                if st.session_state.edited_image:
                    st.image(st.session_state.edited_image, caption="Generated Result", use_column_width=True)
                    image_data = download_image(st.session_state.edited_image)
                    if image_data:
                        st.download_button(
                            "⬇️ Download Result",
                            image_data,
                            "generated_fill.png",
                            "image/png"
                        )
                elif st.session_state.pending_urls:
                    st.info("Generation in progress. Click the refresh button above to check status.")

    # Erase Elements Tab
    with tabs[3]:
        st.header("🎨 Erase Elements")
        st.markdown("Upload an image and select the area you want to erase.")
        
        uploaded_file = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg"], key="erase_upload")
        if uploaded_file:
            col1, col2 = st.columns(2)
            
            with col1:
                # Display original image
                st.image(uploaded_file, caption="Original Image", use_column_width=True)
                
                # Get image dimensions for canvas
                img = Image.open(uploaded_file)
                img_width, img_height = img.size
                
                # Calculate aspect ratio and set canvas height
                aspect_ratio = img_height / img_width
                canvas_width = min(img_width, 800)  # Max width of 800px
                canvas_height = int(canvas_width * aspect_ratio)
                
                # Resize image to match canvas dimensions
                img = img.resize((canvas_width, canvas_height))
                
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Add drawing canvas using Streamlit's drawing canvas component
                stroke_width = st.slider("Brush width", 1, 50, 20, key="erase_brush_width")
                stroke_color = st.color_picker("Brush color", "#fff", key="erase_brush_color")
                
                # Create canvas with background image
                canvas_result = st_canvas(
                    fill_color="rgba(255, 255, 255, 0.0)",  # Transparent fill
                    stroke_width=stroke_width,
                    stroke_color=stroke_color,
                    background_color="",  # Transparent background
                    background_image=img,  # Pass PIL Image directly
                    drawing_mode="freedraw",
                    height=canvas_height,
                    width=canvas_width,
                    key="erase_canvas",
                )
                
                # Options for erasing
                st.subheader("Erase Options")
                content_moderation = st.checkbox("Enable Content Moderation", False, key="erase_content_mod")
                
                if st.button("🎨 Erase Selected Area", key="erase_btn"):
                    if not canvas_result.image_data is None:
                        with st.spinner("Erasing selected area..."):
                            try:
                                # Convert canvas result to mask
                                mask_img = Image.fromarray(canvas_result.image_data.astype('uint8'), mode='RGBA')
                                mask_img = mask_img.convert('L')
                                
                                # Convert uploaded image to bytes
                                image_bytes = uploaded_file.getvalue()
                                
                                result = erase_foreground(
                                    st.session_state.api_key,
                                    image_data=image_bytes,
                                    content_moderation=content_moderation
                                )
                                
                                if result:
                                    if "result_url" in result:
                                        st.session_state.edited_image = result["result_url"]
                                        add_to_gallery(result["result_url"], "Erase")
                                        st.success("✨ Area erased successfully!")
                                    else:
                                        st.error("No result URL in the API response. Please try again.")
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                                if "422" in str(e):
                                    st.warning("Content moderation failed. Please ensure the image is appropriate.")
                    else:
                        st.warning("Please draw on the image to select the area to erase.")
            
            with col2:
                if st.session_state.edited_image:
                    st.image(st.session_state.edited_image, caption="Result", use_column_width=True)
                    image_data = download_image(st.session_state.edited_image)
                    if image_data:
                        st.download_button(
                            "⬇️ Download Result",
                            image_data,
                            "erased_image.png",
                            "image/png",
                            key="erase_download"
                        )

    # ── AI Agent Tab ───────────────────────────────────────────────────────────
    with tabs[4]:
        st.header("🤖 AI Agent")
        st.markdown(
            "Describe what you want in plain English. The agent plans and runs the right "
            "Bria API calls automatically, chaining outputs between steps."
        )

        # ── Quick Action Presets ──────────────────────────────────────────────
        st.subheader("⚡ Quick Presets")
        preset_cols = st.columns(3)
        PRESETS = {
            "🛍️ Amazon Ready": "Create a white-background packshot then add a natural shadow",
            "📱 Social Media Kit": "Generate 4 lifestyle shots in different scene placements",
            "🎯 Ad Creative":      "Create a lifestyle shot with a coffee shop background",
        }
        for col, (label, prompt_text) in zip(preset_cols, PRESETS.items()):
            if col.button(label, use_container_width=True):
                st.session_state["agent_preset_prompt"] = prompt_text

        # ── Image uploader ────────────────────────────────────────────────────
        st.subheader("📸 Product Image (optional for text-only generation)")
        agent_file = st.file_uploader(
            "Upload product image",
            type=["png", "jpg", "jpeg"],
            key="agent_upload",
        )
        if agent_file:
            st.session_state.agent_uploaded_image = agent_file.getvalue()
            st.image(agent_file, caption="Uploaded product", width=260)

        # ── Conversation history ──────────────────────────────────────────────
        for turn in st.session_state.agent_history:
            with st.chat_message(turn["role"]):
                st.markdown(turn["content"])
                if turn.get("images"):
                    img_cols = st.columns(min(len(turn["images"]), 4))
                    for icol, url in zip(img_cols, turn["images"]):
                        icol.image(url, use_column_width=True)

        # ── Visual Plan Preview (pending plan waiting for confirmation) ───────
        if st.session_state.agent_pending_plan is not None:
            plan = st.session_state.agent_pending_plan
            with st.expander("📋 Planned Steps — review before running", expanded=True):
                SERVICE_LABELS = {
                    "generate_image":        "🎨 Generate Image",
                    "lifestyle_shot_by_text": "🌄 Lifestyle Shot (text)",
                    "lifestyle_shot_by_image": "🌄 Lifestyle Shot (image)",
                    "add_shadow":            "🌑 Add Shadow",
                    "create_packshot":       "📦 Create Packshot",
                    "generative_fill":       "🖌️ Generative Fill",
                    "erase_foreground":      "🧹 Erase Foreground",
                }
                for idx, step in enumerate(plan.steps):
                    label = SERVICE_LABELS.get(step.service_name, step.service_name)
                    chain = " *(chains from previous step)*" if step.use_previous_output else ""
                    params_str = ", ".join(f"{k}: `{v}`" for k, v in step.params.items())
                    st.markdown(f"**Step {idx + 1}** → {label}{chain}  \n{params_str}")

                confirm_col, cancel_col = st.columns([2, 1])
                if confirm_col.button("✅ Confirm & Run", type="primary"):
                    if not st.session_state.api_key:
                        st.error("Please enter your Bria API key in the sidebar.")
                    else:
                        result_urls: list[str] = []
                        progress_bar = st.progress(0, text="Starting…")

                        def _progress(idx, total, svc):
                            pct = int((idx / total) * 100)
                            SERVICE_LABELS_LOCAL = {
                                "generate_image":        "Generate Image",
                                "lifestyle_shot_by_text": "Lifestyle Shot",
                                "lifestyle_shot_by_image": "Lifestyle Shot (image)",
                                "add_shadow":            "Add Shadow",
                                "create_packshot":       "Packshot",
                                "generative_fill":       "Generative Fill",
                                "erase_foreground":      "Erase",
                            }
                            progress_bar.progress(
                                pct,
                                text=f"Step {idx + 1}/{total}: {SERVICE_LABELS_LOCAL.get(svc, svc)}…",
                            )

                        with st.spinner("Running agent plan…"):
                            try:
                                result_urls = execute_plan(
                                    plan=plan,
                                    initial_image_data=st.session_state.agent_uploaded_image,
                                    api_key=st.session_state.api_key,
                                    progress_callback=_progress,
                                )
                            except Exception as e:
                                st.error(f"Agent execution error: {e}")

                        progress_bar.empty()

                        if result_urls:
                            # Save to conversation history
                            st.session_state.agent_history.append({
                                "role": "assistant",
                                "content": f"✅ Done! Generated {len(result_urls)} image(s).",
                                "images": result_urls,
                            })
                            # Save to session gallery
                            for url in result_urls:
                                add_to_gallery(url, "AI Agent")
                            st.success(f"✨ Agent finished — {len(result_urls)} image(s) added to Session Gallery.")
                        else:
                            st.warning("The agent ran but produced no results. Check your API key and try a simpler request.")

                        st.session_state.agent_pending_plan = None
                        st.rerun()

                if cancel_col.button("❌ Cancel"):
                    st.session_state.agent_pending_plan = None
                    st.rerun()

        # ── Chat input ────────────────────────────────────────────────────────
        # Pre-fill from preset if one was clicked
        default_chat = st.session_state.pop("agent_preset_prompt", "")
        user_input = st.chat_input(
            "Describe what you want…  e.g. 'Put this product on a white background with a drop shadow'",
        )
        # Accept both typed input and preset selection
        if default_chat and not user_input:
            user_input = default_chat

        if user_input:
            # Show user message immediately
            st.session_state.agent_history.append(
                {"role": "user", "content": user_input, "images": []}
            )

            with st.spinner("🤔 Thinking…"):
                plan, used_llm = parse_intent(
                    user_text=user_input,
                    image_provided=st.session_state.agent_uploaded_image is not None,
                    preferences=get_preferences(),
                    model=st.session_state.ollama_model,
                    ollama_url=st.session_state.ollama_url,
                )

            # ── Conversational question → answer with helpful text, no image plan ──
            if plan is None:
                q = user_input.lower()

                # ── Detect follow-up / elaboration requests ──────────────────
                FOLLOWUP_PHRASES = [
                    "describe it more", "describe more", "tell me more", "more detail",
                    "more info", "explain more", "explain further", "elaborate",
                    "can you explain", "what do you mean", "and then what", "go on",
                    "in more detail", "expand on", "give me more", "say more",
                ]
                is_followup = any(p in q for p in FOLLOWUP_PHRASES) or (
                    len(user_input.split()) <= 5 and any(
                        w in q for w in ["more", "further", "again", "continue", "detail"]
                    )
                )

                # ── Find the last assistant message to get conversation topic ─
                last_topic = None
                if is_followup:
                    for turn in reversed(st.session_state.agent_history):
                        if turn["role"] == "assistant" and turn.get("content"):
                            c = turn["content"].lower()
                            if "api key" in c or "bria.ai" in c:
                                last_topic = "api_key"
                            elif "preset" in c or "amazon ready" in c or "social media kit" in c:
                                last_topic = "presets"
                            elif "lifestyle" in c or "packshot" in c or "shadow" in c or "erase" in c:
                                last_topic = "agent_usage"
                            elif "image generation agent" in c or "can help you" in c:
                                last_topic = "capabilities"
                            if last_topic:
                                break

                # ── Build answer ─────────────────────────────────────────────
                # Follow-up: elaborate on the previous topic
                if is_followup and last_topic == "api_key":
                    answer = (
                        "**More detail on the Bria API key:**\n\n"
                        "- **What it is:** A secret token that identifies your Bria account. "
                        "Every API call to Bria's image services (generate, lifestyle shot, packshot, etc.) "
                        "requires this key.\n"
                        "- **Where to get it:** Sign up at **[bria.ai](https://bria.ai)** → go to your "
                        "dashboard → click **API Keys** → copy the key shown there.\n"
                        "- **How to use it here:** Paste it into the **Enter your API key** password box "
                        "in the **sidebar on the left**. It's treated as a password (hidden by default).\n"
                        "- **Is it free?** Bria offers a free trial with limited credits. "
                        "After that, paid plans are available on their website.\n"
                        "- **Is it safe?** Yes — the key is only held in your browser session memory "
                        "and is never saved to disk or sent anywhere except directly to Bria's API."
                    )
                elif is_followup and last_topic == "presets":
                    answer = (
                        "**More detail on Quick Presets:**\n\n"
                        "**🛍️ Amazon Ready** — runs two steps automatically:\n"
                        "1. Removes the background and places your product on a clean **white background** (packshot)\n"
                        "2. Adds a **natural shadow** underneath the product for depth\n"
                        "Perfect for Amazon, Flipkart, or any e-commerce listing.\n\n"
                        "**📱 Social Media Kit** — generates **4 lifestyle shots** of your product placed in "
                        "different positions (upper left, upper right, bottom left, bottom right). "
                        "Great for Instagram carousels or Facebook ads.\n\n"
                        "**🎯 Ad Creative** — places your product in a **coffee shop scene** as a lifestyle "
                        "background. Good for aspirational ad creatives.\n\n"
                        "> **Tip:** Upload your product image first, then click the preset. "
                        "The agent automatically chains the steps — you don't need to do anything else."
                    )
                elif is_followup and last_topic in ("agent_usage", "capabilities"):
                    answer = (
                        "**More detail on what the AI Agent can do:**\n\n"
                        "**🖼️ Generate Image** — creates an image purely from text. "
                        "Example: *'A red sneaker on a marble surface'*\n\n"
                        "**🌄 Lifestyle Shot** — takes your uploaded product and places it into a scene. "
                        "Example: *'Put this bottle on a kitchen counter with soft morning light'*\n\n"
                        "**📦 Packshot** — removes the background and creates a clean studio-style photo "
                        "with a solid color background. Example: *'White background packshot'*\n\n"
                        "**🌑 Add Shadow** — adds a realistic shadow beneath your product. "
                        "Example: *'Add a natural shadow'* or *'Add a drop shadow'*\n\n"
                        "**🧹 Erase Foreground** — removes unwanted elements from your image.\n\n"
                        "**Chaining steps:** You can combine them: "
                        "*'Make a packshot then add a shadow'* — the agent runs both steps "
                        "automatically, passing the packshot result into the shadow step."
                    )
                elif is_followup and last_topic is None:
                    answer = (
                        "Could you clarify what you'd like me to describe more? For example:\n\n"
                        "- *'Describe the API key setup more'*\n"
                        "- *'Describe the presets more'*\n"
                        "- *'Describe what the agent can do'*"
                    )
                # Fresh question — match by keyword
                elif any(k in q for k in ["api key", "bira key", "bria key", "get key", "find key", "where key", "which key", "which api"]):
                    answer = (
                        "**How to get your Bria API key:**\n\n"
                        "1. Go to **[bria.ai](https://bria.ai)** and sign up / log in\n"
                        "2. Open your account dashboard → **API Keys**\n"
                        "3. Copy your key and paste it into the **Enter your API key** box in the sidebar on the left\n\n"
                        "> The key is only stored for your current browser session — it's never saved to disk."
                    )
                elif any(k in q for k in ["preset", "amazon ready", "social media kit", "ad creative"]):
                    answer = (
                        "**⚡ Quick Presets** are one-click shortcuts:\n\n"
                        "| Preset | What it does |\n|---|---|\n"
                        "| 🛍️ Amazon Ready | White-background packshot → natural shadow |\n"
                        "| 📱 Social Media Kit | 4 lifestyle shots in different placements |\n"
                        "| 🎯 Ad Creative | Lifestyle shot in a coffee-shop scene |\n\n"
                        "Upload a product image first, then click a preset."
                    )
                elif any(k in q for k in ["how", "what", "where", "use", "work", "start", "begin", "tab"]):
                    answer = (
                        "**How to use the AI Agent:**\n\n"
                        "1. **Upload** your product image (optional for text-only generation)\n"
                        "2. **Type** what you want — e.g. *'Put this on a white background with a drop shadow'*\n"
                        "3. Review the **plan preview** and click **✅ Confirm & Run**\n"
                        "4. Results appear here and are saved to the **Session Gallery**\n\n"
                        "Or click one of the **⚡ Quick Presets** above for a one-click workflow."
                    )
                else:
                    answer = (
                        "I'm an **image generation agent** — I can help you:\n\n"
                        "- 🖼️ Generate product images from a description\n"
                        "- 🌄 Create lifestyle shots with custom scenes\n"
                        "- 📦 Make packshots (clean white-background photos)\n"
                        "- 🌑 Add shadows to product images\n"
                        "- 🧹 Erase or fill parts of an image\n\n"
                        "Try typing something like: *'Put this product in a kitchen with soft lighting'*"
                    )

                st.session_state.agent_history.append({
                    "role": "assistant",
                    "content": answer,
                    "images": [],
                })
                st.rerun()


            # ── Image plan → show plan preview ──────────────────────────────────
            else:
                parser_note = "*(via Ollama LLM)*" if used_llm else "*(keyword fallback — Ollama not running)*"
                st.session_state.agent_history.append({
                    "role": "assistant",
                    "content": f"🗺️ Planned **{len(plan.steps)} step(s)** {parser_note}. Review the plan below, then confirm to run.",
                    "images": [],
                })
                st.session_state.agent_pending_plan = plan
                st.rerun()


    # ── Session Gallery ────────────────────────────────────────────────────────
    st.divider()
    gallery = st.session_state.session_gallery
    col_title, col_clear = st.columns([6, 1])
    with col_title:
        st.subheader(f"🖼️ Session Gallery  ({len(gallery)} image{'s' if len(gallery) != 1 else ''})")
    with col_clear:
        if gallery and st.button("🗑️ Clear", help="Clear all gallery images"):
            st.session_state.session_gallery = []
            st.rerun()

    if not gallery:
        st.info("No images generated yet in this session. Generate an image above to see it here.")
    else:
        cols_per_row = 4
        rows = [gallery[i:i + cols_per_row] for i in range(0, len(gallery), cols_per_row)]
        for row in rows:
            cols = st.columns(cols_per_row)
            for col, item in zip(cols, row):
                with col:
                    st.image(item["url"], caption=f"#{item['index']} — {item['label']}", use_column_width=True)
                    img_bytes = download_image(item["url"])
                    if img_bytes:
                        st.download_button(
                            "⬇️ Download",
                            img_bytes,
                            file_name=f"adsnap_{item['index']}.png",
                            mime="image/png",
                            key=f"gallery_dl_{item['index']}"
                        )

if __name__ == "__main__":
    main()