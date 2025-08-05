# Prompt-Based Website Builder

This app generates a complete website based on a user's prompt using Gradio, Unsplash API, and Wikipedia or AI-generated content.

## Features
- Generates responsive HTML & JSX websites
- Auto-populates images from Unsplash
- About section from Wikipedia or local Mistral model
- Supports Bootstrap, Material-UI, and Ant Design
- Light and Dark themes with smart text contrast

## Run Locally
1. Clone this repo
2. Install requirements:
   \\\
   pip install -r requirements.txt
   \\\
3. Run the app:
   \\\
   python app.py
   \\\

## GitHub Pages
Live site (from last generated HTML): [Click here](https://eb01067a1e01e14b3d.gradio.live)

## Outputs
The app generates:
- \generated_website/index.html\ → Previewable website
- \generated_website/index.jsx\ → React component
- Zipped download via Gradio UI

## Tech Stack
- Python
- Gradio
- BeautifulSoup
- Unsplash API
- Ollama + Mistral








