import gradio as gr
import requests
import re
import os
import zipfile
import subprocess
import tempfile
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO

UNSPLASH_ACCESS_KEY = "SXnZu0z3lPzsLOdippu4LUtPk7Ip0-eN6I39MqHfWgo"

def extract_best_keyword(prompt):
    exclude = {'on', 'in', 'the', 'a', 'an', 'and', 'of', 'with', 'to', 'is', 'was'}
    words = re.findall(r'\w+', prompt.lower())
    keywords = [w for w in words if w not in exclude]
    return " ".join(keywords[:2]) if keywords else prompt.strip()

def fetch_text_from_wikipedia(prompt):
    try:
        url = f"https://en.wikipedia.org/wiki/{prompt.replace(' ', '_')}"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.select('p')
        text = ""
        for p in paragraphs[:3]:
            para = p.get_text()
            if not any(x in para for x in ["may refer to", "disambiguation", "message may be displayed"]):
                text += para
        clean_text = re.sub(r'\[\d+\]', '', text.strip())
        if clean_text and len(clean_text.split()) > 40:
            return ". ".join(clean_text.split(".")[:3]) + "."
    except:
        return None

def generate_about_with_mistral(prompt):
    try:
        full_prompt = f"Write a short informative paragraph about {prompt}."
        result = subprocess.run(
            ['ollama', 'run', 'mistral'],
            input=full_prompt.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=180
        )
        output = result.stdout.decode(errors="ignore").strip()
        return output if len(output.split()) > 20 else f"{prompt.title()} is an interesting topic worth exploring."
    except Exception as e:
        return f"(AI generation failed: {str(e)})"

def smart_generate_about(prompt):
    wiki_text = fetch_text_from_wikipedia(prompt)

    if (
        wiki_text
        and len(wiki_text.split()) > 20
        and not wiki_text.lower().strip().startswith(("may refer to", "cut.", "this article", "this message"))
    ):
        return wiki_text
    else:
        return generate_about_with_mistral(prompt)

def fetch_unsplash_images(keyword, count=6):
    try:
        headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}
        url = f"https://api.unsplash.com/search/photos?query={keyword}&per_page=10&orientation=landscape"
        response = requests.get(url, headers=headers)
        data = response.json()
        results = [(img['urls']['regular'], img['alt_description'] or keyword) for img in data['results']]
        return results[:count] if results else [("https://via.placeholder.com/800x600.png?text=No+Image", keyword)] * count
    except:
        return [("https://via.placeholder.com/800x600.png?text=Image+Error", keyword)] * count

def is_image_dark(img_url):
    try:
        response = requests.get(img_url, timeout=5)
        img = Image.open(BytesIO(response.content)).convert("L")
        resized = img.resize((50, 50))
        pixels = list(resized.getdata())
        avg_brightness = sum(pixels) / len(pixels)
        return avg_brightness < 130
    except:
        return False

def is_color_dark(hex_color):
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    brightness = 0.299*r + 0.587*g + 0.114*b
    return brightness < 150

def title_case(text):
    return text.title()

material_css = """
body { font-family: 'Roboto', sans-serif; letter-spacing: 0.5px; }
.btn-primary { background-color: #1976d2; border: none; }
"""

antdesign_css = """
body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; letter-spacing: 0.3px; }
.btn-primary { background-color: #1890ff; border: none; border-radius: 4px; }
"""

bootstrap_css = ""

def generate_react_component(prompt, keyword, description, ui_library):
    if ui_library == "Material-UI":
        import_line = "import { Button, Container, Typography } from '@mui/material';"
    elif ui_library == "Ant Design":
        import_line = "import { Button, Layout, Typography } from 'antd';"
    else:
        import_line = ""
    return f"""
import React from 'react';
{import_line}

const App = () => {{
  return (
    <div style={{{{ padding: '2rem' }}}}>
      <h1>{title_case(keyword)}</h1>
      <p>{description}</p>
    </div>
  );
}}

export default App;
"""

def generate_html(prompt, theme_color, ui_library):
    keyword = extract_best_keyword(prompt)
    title = title_case(keyword)
    description = smart_generate_about(prompt)
    images = fetch_unsplash_images(keyword)
    hero_url, _ = images[0]

    # Analyze brightness
    is_dark_theme = is_color_dark(theme_color)
    is_dark_image = is_image_dark(hero_url)

    # Set text color based on theme for body and gallery
    body_text_color = "#fff" if is_dark_theme else "#000"
    
    # Set text color for hero based on image
    hero_text_color = "#fff" if is_dark_image else "#000"
    border_color = hero_text_color
    shadow_color = "rgba(0,0,0,0.7)" if hero_text_color == "#fff" else "rgba(255,255,255,0.5)"

    extra_style = bootstrap_css
    if ui_library == "Material-UI":
        extra_style = material_css
    elif ui_library == "Ant Design":
        extra_style = antdesign_css

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset='UTF-8'>
  <meta name='viewport' content='width=device-width, initial-scale=1.0'>
  <title>{title}</title>
  <link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css' rel='stylesheet'>
  <style>
    body {{ background-color: {theme_color}; color: {body_text_color}; }}
    a {{ color: {body_text_color}; text-decoration: underline; }}
    .hero {{ position: relative; height: 400px; overflow: hidden; }}
    .hero img {{ width: 100%; height: 100%; object-fit: cover; }}
    .hero h1 {{
      position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
      background: rgba(0, 0, 0, 0.4); padding: 20px;
      color: {hero_text_color}; border: 2px solid {border_color}; border-radius: 10px;
      text-shadow: 2px 2px 8px {shadow_color};
    }}
    .gallery-caption {{
      font-weight: bold; text-align: center; margin-top: 5px; color: {body_text_color};
    }}
    {extra_style}
  </style>
</head>
<body>
<div class='hero'>
  <a href='{hero_url}' target='_blank'>
    <img src='{hero_url}' alt='{title}'>
    <h1>{title}</h1>
  </a>
</div>
<section class='container py-5'>
  <h2>About {title}</h2>
  <p>{description}</p>
</section>
<section class='container py-5'>
  <h3>Gallery</h3>
  <div class='row g-4'>"""

    for url, alt in images[1:]:
        caption = title_case(alt) if alt else title
        html += f"""
    <div class='col-md-4'>
      <a href='{url}' target='_blank'>
        <img src='{url}' alt='{caption}' class='img-fluid rounded'>
      </a>
      <div class='gallery-caption'>{caption}</div>
    </div>"""

    html += f"""
  </div>
</section>
<section class='container py-5'>
  <h3>Contact</h3>
  <p>Email us at:<br><a href='mailto:guptarakshit016@gmail.com'>guptarakshit016@gmail.com</a></p>
</section>
<footer class='bg-dark text-light text-center p-3'>
  &copy; 2025 {title} Inc.
</footer>
</body>
</html>"""

    folder = os.path.join(os.getcwd(), "generated_website")
    os.makedirs(folder, exist_ok=True)
    html_path = os.path.join(folder, "index.html")
    jsx_path = os.path.join(folder, "index.jsx")
    zip_path = os.path.join(folder, "generated_website.zip")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    with open(jsx_path, "w", encoding="utf-8") as f:
        f.write(generate_react_component(prompt, keyword, description, ui_library))
    with zipfile.ZipFile(zip_path, 'w') as z:
        z.write(html_path, arcname="index.html")
        z.write(jsx_path, arcname="index.jsx")

    return html, zip_path

with gr.Blocks() as demo:
    gr.Markdown("## Prompt-Based Website Builder")
    with gr.Row():
        prompt_input = gr.Textbox(label="Describe your website", placeholder="e.g., A travel site on the Himalayas", lines=2)
        theme_color = gr.Dropdown(
            choices=[
                ("Light Grey", "#fefefe"),
                ("Mint Blue", "#e0f7fa"),
                ("Soft Peach", "#fbe9e7"),
                ("Dark Grey", "#212121"),
                ("Ocean Blue", "#2c3e50"),
                ("Starry Night", "#0d1b2a")
            ],
            value="#fefefe",
            label="Theme Color"
        )
        ui_library = gr.Dropdown(
            choices=["Bootstrap", "Material-UI", "Ant Design"],
            value="Bootstrap",
            label="UI Library"
        )
    generate_btn = gr.Button("Generate Website")
    status_output = gr.Textbox(label="Status", interactive=False)
    html_output = gr.HTML(label="Live Preview")
    file_output = gr.File(label="⬇ Download HTML + JSX", visible=False)

    def generate_and_show(prompt, theme_color, ui_library):
        html, file_path = generate_html(prompt, theme_color, ui_library)
        return "", html, gr.update(value=file_path, visible=True)

    generate_btn.click(
        fn=generate_and_show,
        inputs=[prompt_input, theme_color, ui_library],
        outputs=[status_output, html_output, file_output],
        show_progress=True
    )

    demo.launch(share=True, allowed_paths=[tempfile.gettempdir()])
