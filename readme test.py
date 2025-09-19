"""
README Generator AI — Desktop App
Author: aaryan
Features: Full-featured, visually appealing, CustomTkinter app for generating project README files.
"""

import os
import json
import threading
import time
import queue
import random
from pathlib import Path
from datetime import datetime
from tkinter import filedialog, messagebox
import webbrowser
import requests

import customtkinter as ctk

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # App works with fallback heuristics

try:
    import markdown
except ImportError:
    markdown = None

try:
    from github import Github
except ImportError:
    Github = None

try:
    import git  # For local git repo if needed
except ImportError:
    git = None

# -----------------------------
# Config / Globals
# -----------------------------
APP_TITLE = "📄 README Generator AI"
SESSION_FILE = "readme_ai_session.json"
HISTORY_FILE = "readme_ai_history.json"
EXPORT_DIR = "readme_exports"
BADGES = [
    "Python", "OpenAI", "CustomTkinter", "MIT", "GPLv3", "GitHub Actions",
    "Docker", "VS Code", "Pypi", "Build Status"
]
TEMPLATES = ["Standard", "Minimal", "Modern"]
BADGE_STYLES = ["flat", "plastic", "for-the-badge"]
MODELS = ["openai/gpt-4o-mini", "anthropic/claude-3-haiku", "google/gemini-flash-1.5", "meta-llama/llama-3.1-8b-instruct"]

history = []

# -----------------------------
# Helper Functions
# -----------------------------
def save_session(session_data):
    try:
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2)
    except Exception:
        pass

def load_session():
    if not os.path.exists(SESSION_FILE):
        return None
    try:
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def save_history_file():
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
    except Exception:
        pass

def ensure_export_dir():
    Path(EXPORT_DIR).mkdir(exist_ok=True)

def animated_typing(text_widget, content, root, delay=0.02, spinner=False):
    """Type out content with optional spinner animation in main thread"""
    spinner_chars = ["🌀", "🌟", "✨", "💫", "⚡"]
    text_widget.delete("1.0", "end")
    i = 0
    def type_char():
        nonlocal i
        if i < len(content):
            ch = content[i]
            text_widget.insert("end", ch)
            text_widget.see("end")
            if spinner and i % 10 == 0 and i > 0:
                spinner_ch = random.choice(spinner_chars)
                text_widget.insert("end", spinner_ch)
                text_widget.update()
                text_widget.delete("end-2c", "end")  # Remove spinner immediately
            i += 1
            root.after(int(delay * 1000), type_char)
        else:
            text_widget.update()
    type_char()

def generate_toc(content):
    """Generate Table of Contents from Markdown headers"""
    toc = "## Table of Contents\n"
    lines = content.splitlines()
    for line in lines:
        if line.startswith("#"):
            level = len(line.split()[0])
            title = line.lstrip("#").strip()
            anchor = title.lower().replace(" ", "-")
            toc += "  " * (level - 1) + f"- [{title}](#{anchor})\n"
    return toc + "\n"

def generate_dir_tree(dir_path, max_depth=3):
    """Generate directory tree as Markdown code block"""
    tree = "```\n"
    for root, dirs, files in os.walk(dir_path):
        level = root.replace(dir_path, '').count(os.sep)
        if level > max_depth:
            continue
        indent = ' ' * 4 * level
        tree += f"{indent}{os.path.basename(root)}/\n"
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            tree += f"{subindent}{f}\n"
    tree += "```\n"
    return tree

def analyze_local_dir(path, project_info):
    """Analyze local directory for auto-fill"""
    project_info['name'] = project_info.get('name') or os.path.basename(path)
    # Languages
    languages = set()
    for root, _, files in os.walk(path):
        for f in files:
            ext = os.path.splitext(f)[1].lstrip('.')
            if ext:
                languages.add(ext.capitalize())
    project_info['languages'] = list(languages)
    # Dependencies from requirements.txt
    req_path = os.path.join(path, 'requirements.txt')
    if os.path.exists(req_path):
        with open(req_path, 'r') as f:
            deps = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        project_info['dependencies'] = deps
    # Suggest badges
    suggested_badges = []
    for lang in languages:
        if lang.lower() in ['python', 'js', 'java']:
            suggested_badges.extend([lang, "GitHub Actions"])
    for b in suggested_badges:
        if b not in project_info['badges']:
            project_info['badges'].append(b)
    # Dir tree
    project_info['dir_tree'] = generate_dir_tree(path)

def analyze_github_url(url, project_info):
    """Analyze GitHub repo via API for auto-fill"""
    if not url.startswith("https://github.com/"):
        return
    parts = url.split("https://github.com/")[1].split("/")
    if len(parts) < 2:
        return
    user, repo = parts[:2]
    api_url = f"https://api.github.com/repos/{user}/{repo}"
    try:
        resp = requests.get(api_url).json()
        project_info['name'] = resp.get('name', project_info.get('name'))
        project_info['description'] = resp.get('description', project_info.get('description'))
        project_info['languages'] = [resp.get('language')] if resp.get('language') else []
        suggested_badges = ["GitHub Stars", "GitHub Forks"]
        for b in suggested_badges:
            if b not in project_info['badges']:
                project_info['badges'].append(b)
    except Exception:
        pass

# -----------------------------
# AI Analysis / README Generation
# -----------------------------
def generate_readme_ai(project_info: dict, client, model="openai/gpt-4o-mini", temperature=0.3, template="Standard", use_emojis=False, profile_mode=False):
    """Generate README content using OpenRouter"""
    if client is None:
        # Fallback: simple template
        content = f"# {project_info.get('name', 'My Project')}\n\n{project_info.get('description', 'Description')}\n\n## Features\n"
        for f in project_info.get("features", []):
            content += f"- {f}\n"
        badges = project_info.get("badges", [])
        badge_style = project_info.get('badge_style', 'flat')
        if badges:
            content += "\n" + " ".join([f"![{b}](https://img.shields.io/badge/{b}-blue?style={badge_style})" for b in badges])
        # Add other sections simply
        if project_info.get("installation"):
            content += "\n\n## Installation\n" + project_info["installation"]
        if project_info.get("usage"):
            content += "\n\n## Usage\n" + project_info["usage"]
        if project_info.get("roadmap"):
            content += "\n\n## Roadmap\n" + project_info["roadmap"]
        if project_info.get("contributing"):
            content += "\n\n## Contributing\n" + project_info["contributing"]
        if project_info.get("license"):
            content += "\n\n## License\n" + project_info["license"]
        if project_info.get("dir_tree"):
            content += "\n\n## Project Structure\n" + project_info["dir_tree"]
        for img in project_info.get("images", []):
            content += f"\n![{img['alt']}]({img['path']})\n"
        return content
    try:
        prompt = f"""
        You are an expert developer and technical writer.
        Generate a professional GitHub {'Profile ' if profile_mode else ''}README in Markdown format using {template} template.
        {'Add emojis to section headers. ' if use_emojis else ''}
        Project info: {json.dumps(project_info)}
        Include sections: Title, {'Bio, Skills, Stats, ' if profile_mode else ''}Description, Features, Badges, Installation, Usage, Roadmap, Contributing, License, {'Project Structure, ' if project_info.get('dir_tree') else ''}Support.
        Embed images if provided.
        """
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=temperature,
            extra_headers={
                "HTTP-Referer": "https://readme-generator-ai.com",  # Placeholder
                "X-Title": "README Generator AI",
            }
        )
        text = resp.choices[0].message.content.strip()
        if project_info.get('add_toc', True):
            text = generate_toc(text) + text
        return text
    except Exception as e:
        return f"# {project_info.get('name', 'My Project')}\n\nFallback README due to error: {str(e)} (no details)"

# -----------------------------
# GUI Application
# -----------------------------
class ReadmeAIApp:
    def __init__(self, root):
        self.root = root
        root.title(APP_TITLE)
        root.geometry("1200x800")
        root.minsize(1000, 700)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        self.openai_client = None
        self.last_readme = None
        self.ui_queue = queue.Queue()

        self.project_info = {
            "name": "",
            "description": "",
            "features": [],
            "badges": [],
            "installation": "",
            "usage": "",
            "roadmap": "",
            "contributing": "",
            "license": "MIT",
            "images": [],
            "dir_tree": "",
            "languages": [],
            "dependencies": [],
        }

        # Tabview for organization
        self.tabview = ctk.CTkTabview(root)
        self.tabview.pack(fill="x", padx=12, pady=(12,6))

        # Tab 1: Basic Inputs
        basic_tab = self.tabview.add("Basic")
        self.setup_basic_tab(basic_tab)

        # Tab 2: Additional Sections
        additional_tab = self.tabview.add("Additional")
        self.setup_additional_tab(additional_tab)

        # Tab 3: Customizations
        custom_tab = self.tabview.add("Custom")
        self.setup_custom_tab(custom_tab)

        # Tab 4: AI Settings
        ai_tab = self.tabview.add("AI")
        self.setup_ai_tab(ai_tab)

        # Tab 5: Analysis & Git
        analysis_tab = self.tabview.add("Analysis & Git")
        self.setup_analysis_tab(analysis_tab)

        # Bottom frame for preview and history
        bottom_frame = ctk.CTkFrame(root)
        bottom_frame.pack(fill="both", expand=True, padx=12, pady=6)

        # Left: README Editor/Preview
        leftf = ctk.CTkFrame(bottom_frame)
        leftf.pack(side="left", fill="both", expand=True, padx=(0,6))
        ctk.CTkLabel(leftf, text="README Editor", font=("Arial",16,"bold")).pack(anchor="nw", padx=8, pady=(8,4))
        self.text_preview = ctk.CTkTextbox(leftf, width=640, height=400)
        self.text_preview.pack(fill="both", expand=True, padx=8, pady=6)

        self.btn_browser_preview = ctk.CTkButton(leftf, text="Preview in Browser", command=self.browser_preview)
        self.btn_browser_preview.pack(pady=6)

        # Right: History & Exports
        rightf = ctk.CTkFrame(bottom_frame, width=360)
        rightf.pack(side="right", fill="both")
        ctk.CTkLabel(rightf, text="History & Options", font=("Arial",16,"bold")).pack(anchor="nw", padx=6, pady=(6,0))

        self.history_scroll = ctk.CTkScrollableFrame(rightf, width=340, height=200)
        self.history_scroll.pack(fill="x", padx=6, pady=6)
        self.history_items = []

        self.btn_export_md = ctk.CTkButton(rightf, text="Export Markdown", command=self.export_md)
        self.btn_export_md.pack(padx=6, pady=6)
        self.btn_export_pdf = ctk.CTkButton(rightf, text="Export PDF", command=self.export_pdf)
        self.btn_export_pdf.pack(padx=6, pady=6)
        self.btn_export_html = ctk.CTkButton(rightf, text="Export HTML", command=self.export_html)
        self.btn_export_html.pack(padx=6, pady=6)
        self.btn_clear_hist = ctk.CTkButton(rightf, text="Clear History", command=self.clear_history)
        self.btn_clear_hist.pack(padx=6, pady=6)

        # Process UI queue
        self.process_ui_queue()

        # Load session and history
        self.load_session_and_history()

    def setup_basic_tab(self, tab):
        # Project Name, Desc
        ctk.CTkLabel(tab, text="Project Name").grid(row=0, column=0, padx=6, pady=6)
        self.entry_name = ctk.CTkEntry(tab, placeholder_text="Project Name", width=400)
        self.entry_name.grid(row=0, column=1, padx=6, pady=6)

        ctk.CTkLabel(tab, text="Description").grid(row=1, column=0, padx=6, pady=6)
        self.entry_desc = ctk.CTkEntry(tab, placeholder_text="Short Description", width=600)
        self.entry_desc.grid(row=1, column=1, padx=6, pady=6)

        # Features
        ctk.CTkLabel(tab, text="Add Feature").grid(row=2, column=0, padx=6, pady=6)
        self.entry_feature = ctk.CTkEntry(tab, placeholder_text="Add Feature", width=300)
        self.entry_feature.grid(row=2, column=1, padx=6, pady=6)
        self.btn_add_feature = ctk.CTkButton(tab, text="Add", command=self.add_feature)
        self.btn_add_feature.grid(row=2, column=2, padx=6, pady=6)
        self.btn_clear_features = ctk.CTkButton(tab, text="Clear", command=self.clear_features)
        self.btn_clear_features.grid(row=2, column=3, padx=6, pady=6)

        # Badges
        ctk.CTkLabel(tab, text="Add Badge").grid(row=3, column=0, padx=6, pady=6)
        self.badge_var = ctk.StringVar(value=BADGES[0])
        self.combo_badge = ctk.CTkComboBox(tab, values=BADGES, variable=self.badge_var, width=200)
        self.combo_badge.grid(row=3, column=1, padx=6, pady=6)
        self.btn_add_badge = ctk.CTkButton(tab, text="Add", command=self.add_badge)
        self.btn_add_badge.grid(row=3, column=2, padx=6, pady=6)
        self.btn_clear_badges = ctk.CTkButton(tab, text="Clear", command=self.clear_badges)
        self.btn_clear_badges.grid(row=3, column=3, padx=6, pady=6)

        # Images
        ctk.CTkLabel(tab, text="Upload Image").grid(row=4, column=0, padx=6, pady=6)
        self.entry_image_alt = ctk.CTkEntry(tab, placeholder_text="Alt Text", width=300)
        self.entry_image_alt.grid(row=4, column=1, padx=6, pady=6)
        self.btn_upload_image = ctk.CTkButton(tab, text="Upload", command=self.upload_image)
        self.btn_upload_image.grid(row=4, column=2, padx=6, pady=6)
        self.btn_clear_images = ctk.CTkButton(tab, text="Clear Images", command=self.clear_images)
        self.btn_clear_images.grid(row=4, column=3, padx=6, pady=6)

        # Labels
        self.label_features = ctk.CTkLabel(tab, text="Features: None", wraplength=600)
        self.label_features.grid(row=5, column=0, columnspan=4, padx=6, pady=6, sticky="w")
        self.label_badges = ctk.CTkLabel(tab, text="Badges: None", wraplength=600)
        self.label_badges.grid(row=6, column=0, columnspan=4, padx=6, pady=6, sticky="w")
        self.label_images = ctk.CTkLabel(tab, text="Images: None", wraplength=600)
        self.label_images.grid(row=7, column=0, columnspan=4, padx=6, pady=6, sticky="w")

    def setup_additional_tab(self, tab):
        # Installation
        ctk.CTkLabel(tab, text="Installation").grid(row=0, column=0, padx=6, pady=6)
        self.text_install = ctk.CTkTextbox(tab, width=600, height=100)
        self.text_install.grid(row=0, column=1, padx=6, pady=6)

        # Usage
        ctk.CTkLabel(tab, text="Usage").grid(row=1, column=0, padx=6, pady=6)
        self.text_usage = ctk.CTkTextbox(tab, width=600, height=100)
        self.text_usage.grid(row=1, column=1, padx=6, pady=6)

        # Roadmap
        ctk.CTkLabel(tab, text="Roadmap").grid(row=2, column=0, padx=6, pady=6)
        self.text_roadmap = ctk.CTkTextbox(tab, width=600, height=100)
        self.text_roadmap.grid(row=2, column=1, padx=6, pady=6)

        # Contributing
        ctk.CTkLabel(tab, text="Contributing").grid(row=3, column=0, padx=6, pady=6)
        self.text_contributing = ctk.CTkTextbox(tab, width=600, height=100)
        self.text_contributing.grid(row=3, column=1, padx=6, pady=6)

        # License
        ctk.CTkLabel(tab, text="License").grid(row=4, column=0, padx=6, pady=6)
        self.combo_license = ctk.CTkComboBox(tab, values=["MIT", "GPLv3", "Apache 2.0", "BSD"])
        self.combo_license.grid(row=4, column=1, padx=6, pady=6)

    def setup_custom_tab(self, tab):
        # Template
        ctk.CTkLabel(tab, text="Template").grid(row=0, column=0, padx=6, pady=6)
        self.combo_template = ctk.CTkComboBox(tab, values=TEMPLATES, width=200)
        self.combo_template.grid(row=0, column=1, padx=6, pady=6)

        # Badge Style
        ctk.CTkLabel(tab, text="Badge Style").grid(row=1, column=0, padx=6, pady=6)
        self.combo_badge_style = ctk.CTkComboBox(tab, values=BADGE_STYLES, width=200)
        self.combo_badge_style.grid(row=1, column=1, padx=6, pady=6)

        # Use Emojis
        self.var_emojis = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(tab, text="Add Emojis to Sections", variable=self.var_emojis).grid(row=2, column=0, columnspan=2, padx=6, pady=6)

        # Add TOC
        self.var_toc = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(tab, text="Add Table of Contents", variable=self.var_toc).grid(row=3, column=0, columnspan=2, padx=6, pady=6)

        # Profile Mode
        self.var_profile = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(tab, text="Profile README Mode", variable=self.var_profile).grid(row=4, column=0, columnspan=2, padx=6, pady=6)

    def setup_ai_tab(self, tab):
        # API Key
        ctk.CTkLabel(tab, text="OpenRouter API Key").grid(row=0, column=0, padx=6, pady=6)
        self.entry_api = ctk.CTkEntry(tab, placeholder_text="OpenRouter API Key (sk-...)", show="*", width=400)
        self.entry_api.grid(row=0, column=1, padx=6, pady=6)
        self.btn_set_api = ctk.CTkButton(tab, text="Set Key", command=self.set_api_key)
        self.btn_set_api.grid(row=0, column=2, padx=6, pady=6)

        # Model
        ctk.CTkLabel(tab, text="AI Model").grid(row=1, column=0, padx=6, pady=6)
        self.combo_model = ctk.CTkComboBox(tab, values=MODELS, width=300)
        self.combo_model.grid(row=1, column=1, padx=6, pady=6)

        # Temperature
        ctk.CTkLabel(tab, text="Creativity (Temperature)").grid(row=2, column=0, padx=6, pady=6)
        self.slider_temp = ctk.CTkSlider(tab, from_=0.1, to=1.0, number_of_steps=9)
        self.slider_temp.set(0.3)
        self.slider_temp.grid(row=2, column=1, padx=6, pady=6)

        self.btn_generate = ctk.CTkButton(tab, text="Generate README", command=self.start_generation, width=200)
        self.btn_generate.grid(row=3, column=0, columnspan=2, padx=6, pady=12)

        self.progress = ctk.CTkProgressBar(tab, width=400)
        self.progress.grid(row=4, column=0, columnspan=3, padx=6, pady=6)
        self.progress.set(0.0)

    def setup_analysis_tab(self, tab):
        # Local Dir
        ctk.CTkLabel(tab, text="Local Directory").grid(row=0, column=0, padx=6, pady=6)
        self.entry_dir = ctk.CTkEntry(tab, placeholder_text="Path to project dir", width=400)
        self.entry_dir.grid(row=0, column=1, padx=6, pady=6)
        self.btn_browse_dir = ctk.CTkButton(tab, text="Browse", command=self.browse_dir)
        self.btn_browse_dir.grid(row=0, column=2, padx=6, pady=6)
        self.btn_analyze_dir = ctk.CTkButton(tab, text="Analyze", command=self.analyze_dir)
        self.btn_analyze_dir.grid(row=0, column=3, padx=6, pady=6)

        # GitHub URL
        ctk.CTkLabel(tab, text="GitHub URL").grid(row=1, column=0, padx=6, pady=6)
        self.entry_github = ctk.CTkEntry(tab, placeholder_text="https://github.com/user/repo", width=400)
        self.entry_github.grid(row=1, column=1, padx=6, pady=6)
        self.btn_analyze_github = ctk.CTkButton(tab, text="Analyze", command=self.analyze_github)
        self.btn_analyze_github.grid(row=1, column=2, padx=6, pady=6)

        # Git Push
        ctk.CTkLabel(tab, text="GitHub Token").grid(row=2, column=0, padx=6, pady=6)
        self.entry_git_token = ctk.CTkEntry(tab, placeholder_text="GitHub Personal Token", show="*", width=400)
        self.entry_git_token.grid(row=2, column=1, padx=6, pady=6)

        ctk.CTkLabel(tab, text="Repo (user/repo)").grid(row=3, column=0, padx=6, pady=6)
        self.entry_repo = ctk.CTkEntry(tab, placeholder_text="user/repo", width=400)
        self.entry_repo.grid(row=3, column=1, padx=6, pady=6)

        self.btn_push_git = ctk.CTkButton(tab, text="Push README to GitHub", command=self.push_to_github)
        self.btn_push_git.grid(row=4, column=0, columnspan=2, padx=6, pady=12)

    # ----------------- UI Queue for Thread Safety -----------------
    def process_ui_queue(self):
        try:
            while not self.ui_queue.empty():
                task = self.ui_queue.get_nowait()
                task()
        except queue.Empty:
            pass
        self.root.after(100, self.process_ui_queue)

    # ----------------- Actions -----------------
    def set_api_key(self):
        key = self.entry_api.get().strip()
        if not key:
            messagebox.showwarning("API Key", "Please enter a valid key.")
            return
        if OpenAI is not None:
            self.openai_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=key)
        messagebox.showinfo("API Key", "API key set for session.")
        self.save_session_state()

    def add_feature(self):
        f = self.entry_feature.get().strip()
        if f:
            self.project_info["features"].append(f)
            self.entry_feature.delete(0, "end")
            self.update_labels()
            messagebox.showinfo("Feature Added", f"Feature '{f}' added.")
        else:
            messagebox.showwarning("Feature", "Enter a feature.")

    def clear_features(self):
        self.project_info["features"] = []
        self.update_labels()

    def add_badge(self):
        b = self.badge_var.get()
        if b and b not in self.project_info["badges"]:
            self.project_info["badges"].append(b)
            self.update_labels()
            messagebox.showinfo("Badge Added", f"Badge '{b}' added.")
        elif b in self.project_info["badges"]:
            messagebox.showwarning("Badge", "Badge already added.")

    def clear_badges(self):
        self.project_info["badges"] = []
        self.update_labels()

    def upload_image(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.gif")])
        if path:
            alt = self.entry_image_alt.get().strip() or os.path.basename(path)
            self.project_info["images"].append({"path": path, "alt": alt})
            self.entry_image_alt.delete(0, "end")
            self.update_labels()
            messagebox.showinfo("Image Added", f"Image '{alt}' added.")

    def clear_images(self):
        self.project_info["images"] = []
        self.update_labels()

    def update_labels(self):
        self.label_features.configure(text=f"Features: {', '.join(self.project_info['features']) or 'None'}")
        self.label_badges.configure(text=f"Badges: {', '.join(self.project_info['badges']) or 'None'}")
        images_str = ', '.join([img['alt'] for img in self.project_info['images']]) or 'None'
        self.label_images.configure(text=f"Images: {images_str}")

    def browse_dir(self):
        path = filedialog.askdirectory()
        if path:
            self.entry_dir.insert(0, path)

    def analyze_dir(self):
        path = self.entry_dir.get().strip()
        if path and os.path.isdir(path):
            analyze_local_dir(path, self.project_info)
            self.entry_name.insert(0, self.project_info['name'])
            self.update_labels()
            messagebox.showinfo("Analysis", "Local directory analyzed.")

    def analyze_github(self):
        url = self.entry_github.get().strip()
        if url:
            analyze_github_url(url, self.project_info)
            self.entry_name.insert(0, self.project_info['name'])
            self.entry_desc.insert(0, self.project_info['description'])
            self.update_labels()
            messagebox.showinfo("Analysis", "GitHub repo analyzed.")

    def start_generation(self):
        name = self.entry_name.get().strip()
        desc = self.entry_desc.get().strip()
        if not name or not desc:
            messagebox.showwarning("Input", "Please provide project name and description.")
            return
        self.project_info["name"] = name
        self.project_info["description"] = desc
        self.project_info["installation"] = self.text_install.get("1.0", "end").strip()
        self.project_info["usage"] = self.text_usage.get("1.0", "end").strip()
        self.project_info["roadmap"] = self.text_roadmap.get("1.0", "end").strip()
        self.project_info["contributing"] = self.text_contributing.get("1.0", "end").strip()
        self.project_info["license"] = self.combo_license.get()
        self.project_info["template"] = self.combo_template.get()
        self.project_info["badge_style"] = self.combo_badge_style.get()
        self.project_info["use_emojis"] = self.var_emojis.get()
        self.project_info["add_toc"] = self.var_toc.get()
        self.project_info["profile_mode"] = self.var_profile.get()
        self.project_info["model"] = self.combo_model.get()
        self.project_info["temperature"] = self.slider_temp.get()
        self.btn_generate.configure(state="disabled")
        t = threading.Thread(target=self._generate_thread)
        t.start()

    def _generate_thread(self):
        def ui_update_progress(value):
            self.progress.set(value)

        self.ui_queue.put(lambda: ui_update_progress(0.1))
        content = generate_readme_ai(self.project_info, client=self.openai_client, model=self.project_info.get("model", "openai/gpt-4o-mini"), 
                                     temperature=self.project_info.get("temperature", 0.3),
                                     template=self.project_info.get("template", "Standard"),
                                     use_emojis=self.project_info.get("use_emojis", False),
                                     profile_mode=self.project_info.get("profile_mode", False))
        self.ui_queue.put(lambda: ui_update_progress(0.7))
        self.ui_queue.put(lambda: animated_typing(self.text_preview, content, self.root))
        self.ui_queue.put(lambda: ui_update_progress(1.0))
        time.sleep(0.2)
        self.ui_queue.put(lambda: ui_update_progress(0.0))
        self.last_readme = content
        # Add to history
        entry = {"timestamp": datetime.now().isoformat(), "content": content}
        history.append(entry)
        save_history_file()
        self.ui_queue.put(self.refresh_history_ui)
        self.ui_queue.put(lambda: self.btn_generate.configure(state="normal"))

    def browser_preview(self):
        if not self.last_readme:
            messagebox.showinfo("Preview", "No README generated.")
            return
        temp_path = "temp_readme.md"
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(self.last_readme)
        webbrowser.open(f"file://{os.path.abspath(temp_path)}")

    # ----------------- Export -----------------
    def export_md(self):
        if not self.last_readme:
            messagebox.showinfo("Export", "No README generated.")
            return
        ensure_export_dir()
        default_name = f"{self.project_info['name'].replace(' ', '_')}_README.md" if self.project_info['name'] else "README.md"
        p = filedialog.asksaveasfilename(initialfile=default_name, defaultextension=".md", filetypes=[("Markdown", "*.md")])
        if not p:
            return
        with open(p, "w", encoding="utf-8") as f:
            f.write(self.last_readme)
        messagebox.showinfo("Export", "README exported successfully.")

    def export_pdf(self):
        if not self.last_readme:
            messagebox.showinfo("Export", "No README generated.")
            return
        ensure_export_dir()
        default_name = f"{self.project_info['name'].replace(' ', '_')}_README.pdf" if self.project_info['name'] else "README.pdf"
        p = filedialog.asksaveasfilename(initialfile=default_name, defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if not p:
            return
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import SimpleDocTemplate, Paragraph
            doc = SimpleDocTemplate(p, pagesize=letter)
            styles = getSampleStyleSheet()
            flowables = []
            for line in self.last_readme.splitlines():
                style = "Normal"
                if line.startswith("#"):
                    level = len(line.split()[0])
                    style = f"Heading{min(level, 6)}"
                p = Paragraph(line, styles[style])
                flowables.append(p)
            doc.build(flowables)
            messagebox.showinfo("Export", "PDF exported successfully.")
        except ImportError:
            messagebox.showerror("Export", "reportlab library not installed. Install it with pip install reportlab.")
        except Exception as e:
            messagebox.showerror("Export", f"Failed: {e}")

    def export_html(self):
        if not self.last_readme:
            messagebox.showinfo("Export", "No README generated.")
            return
        if markdown is None:
            messagebox.showerror("Export", "markdown library not installed. Install with pip install markdown.")
            return
        html_content = markdown.markdown(self.last_readme)
        html_full = f"<html><body>{html_content}</body></html>"
        ensure_export_dir()
        default_name = f"{self.project_info['name'].replace(' ', '_')}_README.html" if self.project_info['name'] else "README.html"
        p = filedialog.asksaveasfilename(initialfile=default_name, defaultextension=".html", filetypes=[("HTML", "*.html")])
        if not p:
            return
        with open(p, "w", encoding="utf-8") as f:
            f.write(html_full)
        messagebox.showinfo("Export", "HTML exported successfully.")

    def push_to_github(self):
        if not self.last_readme:
            messagebox.showinfo("Push", "No README generated.")
            return
        if Github is None:
            messagebox.showerror("Push", "PyGithub not installed. Install with pip install PyGithub.")
            return
        token = self.entry_git_token.get().strip()
        repo_str = self.entry_repo.get().strip()
        if not token or not repo_str:
            messagebox.showwarning("Push", "Provide GitHub token and repo.")
            return
        try:
            g = Github(token)
            repo = g.get_repo(repo_str)
            try:
                contents = repo.get_contents("README.md")
                repo.update_file(contents.path, "Update README.md via README Generator AI", self.last_readme, contents.sha, branch="main")
            except:
                repo.create_file("README.md", "Create README.md via README Generator AI", self.last_readme, branch="main")
            messagebox.showinfo("Push", "README pushed to GitHub successfully.")
        except Exception as e:
            messagebox.showerror("Push", f"Failed: {str(e)}")

    # ----------------- History -----------------
    def refresh_history_ui(self):
        for w in self.history_items:
            w.destroy()
        self.history_items.clear()
        for idx, entry in enumerate(reversed(history[-20:])):
            btn = ctk.CTkButton(self.history_scroll, text=entry["timestamp"][:19], command=lambda c=entry["content"]: self.load_history_item(c))
            btn.pack(fill="x", padx=6, pady=4)
            self.history_items.append(btn)

    def load_history_item(self, content):
        self.text_preview.delete("1.0", "end")
        self.text_preview.insert("1.0", content)
        self.last_readme = content

    def clear_history(self):
        if not messagebox.askyesno("Clear", "Clear all history?"):
            return
        history.clear()
        save_history_file()
        self.refresh_history_ui()

    # ----------------- Session -----------------
    def save_session_state(self):
        data = {
            # Do not save API key for security
        }
        save_session(data)

    def load_session_and_history(self):
        sess = load_session()
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, list):
                        history.extend([item for item in loaded if item not in history])
            except:
                pass
        self.refresh_history_ui()
        self.update_labels()

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    ensure_export_dir()
    root = ctk.CTk()
    app = ReadmeAIApp(root)
    root.mainloop()