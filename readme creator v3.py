"""
📄 Advanced GitHub README Generator — Desktop AI
Author: aaryan
Full-featured, desktop-only app with badges, live preview, templates, custom badges, and AI suggestions.
"""

import os
import json
import time
import threading
import requests
import customtkinter as ctk
from tkinter import filedialog, messagebox
import pyperclip

try:
    import openai
except ImportError:
    openai = None

# -------------------------
# Constants / Files
# -------------------------
APP_TITLE = "📄 README Generator — Advanced Desktop AI"
SESSION_FILE = "readme_generator_session.json"

BADGES_OPTIONS = {
    "Python Version": "![Python](https://img.shields.io/badge/python-3.9%2B-blue)",
    "License": "![License](https://img.shields.io/badge/license-MIT-green)",
    "API Usage": "![API](https://img.shields.io/badge/API-OpenRouter-orange)",
    "CI/CD": "![CI/CD](https://img.shields.io/badge/CI/CD-passing-brightgreen)",
    "Stars": "![Stars](https://img.shields.io/badge/stars-⭐-yellow)"
}

TEMPLATES = {
    "Basic": "# {name}\n\n{tagline}\n\n## Features\n{features}\n\n## Installation\n{installation}\n\n## Usage\n{usage}\n\n## License\n{license}\n",
    "Professional": "# {name}\n\n{tagline}\n\n{badges}\n\n## Purpose\n{purpose}\n\n## Features\n{features}\n\n## Installation\n{installation}\n\n## Usage\n{usage}\n\n## Dependencies\n{dependencies}\n\n## License\n{license}\n"
}

# -------------------------
# Helpers: local storage
# -------------------------
def save_session(data):
    try:
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

def load_session():
    if not os.path.exists(SESSION_FILE):
        return {}
    try:
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

# -------------------------
# GUI Application
# -------------------------
class AdvancedReadmeApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1000x900")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")
        self.session = load_session()
        self.inputs = {}
        self.logo_path = self.session.get("logo_path", "")

        # --- Input Fields ---
        fields = [
            ("Project Name", "project_name"),
            ("Tagline / Short Description", "tagline"),
            ("Purpose / What it does", "purpose"),
            ("Features (comma-separated)", "features"),
            ("Installation instructions", "installation"),
            ("Usage instructions", "usage"),
            ("Dependencies (comma-separated)", "dependencies"),
            ("License", "license_info")
        ]

        row = 0
        for label, key in fields:
            ctk.CTkLabel(self, text=label).grid(row=row, column=0, padx=10, pady=5, sticky="w")
            entry = ctk.CTkEntry(self, width=650)
            entry.grid(row=row, column=1, padx=10, pady=5)
            entry.insert(0, self.session.get(key, ""))
            entry.bind("<KeyRelease>", self.live_preview_update)
            self.inputs[key] = entry
            row += 1

        # --- API Key ---
        ctk.CTkLabel(self, text="API Key (OpenRouter/OpenAI)").grid(row=row, column=0, padx=10, pady=5, sticky="w")
        self.entry_api = ctk.CTkEntry(self, width=650, show="*")
        self.entry_api.grid(row=row, column=1, padx=10, pady=5)
        self.entry_api.insert(0, self.session.get("api_key", ""))
        row += 1

        # --- API Choice ---
        ctk.CTkLabel(self, text="Select API").grid(row=row, column=0, padx=10, pady=5, sticky="w")
        self.api_choice = ctk.StringVar(value=self.session.get("api_choice", "openrouter"))
        ctk.CTkOptionMenu(self, variable=self.api_choice, values=["openrouter", "chatgpt"]).grid(row=row, column=1, padx=10, pady=5, sticky="w")
        row += 1

        # --- Badge Selection ---
        ctk.CTkLabel(self, text="Select Badges to Include").grid(row=row, column=0, padx=10, pady=5, sticky="w")
        self.badge_vars = {}
        badge_frame = ctk.CTkFrame(self)
        badge_frame.grid(row=row, column=1, padx=10, pady=5, sticky="w")
        for idx, badge_name in enumerate(BADGES_OPTIONS.keys()):
            var = ctk.BooleanVar(value=self.session.get("badges", {}).get(badge_name, True))
            cb = ctk.CTkCheckBox(badge_frame, text=badge_name, variable=var)
            cb.grid(row=0, column=idx, padx=5, pady=5)
            self.badge_vars[badge_name] = var
        row += 1

        # --- Logo Upload ---
        ctk.CTkButton(self, text="Upload Logo", command=self.upload_logo).grid(row=row, column=0, padx=10, pady=5)
        self.lbl_logo = ctk.CTkLabel(self, text=os.path.basename(self.logo_path) if self.logo_path else "No Logo Selected")
        self.lbl_logo.grid(row=row, column=1, padx=10, pady=5, sticky="w")
        row += 1

        # --- Template Selection ---
        ctk.CTkLabel(self, text="Select Template").grid(row=row, column=0, padx=10, pady=5, sticky="w")
        self.template_choice = ctk.StringVar(value=self.session.get("template", "Professional"))
        ctk.CTkOptionMenu(self, variable=self.template_choice, values=list(TEMPLATES.keys())).grid(row=row, column=1, padx=10, pady=5, sticky="w")
        row += 1

        # --- Generate Button ---
        self.btn_generate = ctk.CTkButton(self, text="Generate README", command=self.start_generation)
        self.btn_generate.grid(row=row, column=0, columnspan=2, pady=10)
        row += 1

        # --- Progress Bar ---
        self.progress = ctk.CTkProgressBar(self, width=950)
        self.progress.grid(row=row, column=0, columnspan=2, padx=10, pady=5)
        row += 1

        # --- Output Textbox ---
        self.txt_output = ctk.CTkTextbox(self, width=950, height=250)
        self.txt_output.grid(row=row, column=0, columnspan=2, padx=10, pady=5)
        row += 1

        # --- Copy Button ---
        self.btn_copy = ctk.CTkButton(self, text="Copy to Clipboard", command=self.copy_to_clipboard)
        self.btn_copy.grid(row=row, column=0, columnspan=2, pady=5)
        row += 1

        # --- Live Preview Textbox ---
        ctk.CTkLabel(self, text="Live Preview").grid(row=row, column=0, padx=10, pady=5, sticky="w")
        self.txt_preview = ctk.CTkTextbox(self, width=950, height=200)
        self.txt_preview.grid(row=row+1, column=0, columnspan=2, padx=10, pady=5)
        row += 2

        # Start live preview loop
        self.after(500, self.live_preview_update)

    # ---------------------
    # Live Preview
    # ---------------------
    def live_preview_update(self, event=None):
        template = TEMPLATES.get(self.template_choice.get(), TEMPLATES["Professional"])
        selected_badges = " ".join([BADGES_OPTIONS[k] for k,v in self.badge_vars.items() if v.get()])
        text = template.format(
            name=self.inputs["project_name"].get(),
            tagline=self.inputs["tagline"].get(),
            purpose=self.inputs["purpose"].get(),
            features="\n".join([f"- {f.strip()}" for f in self.inputs["features"].get().split(",")]),
            installation=self.inputs["installation"].get(),
            usage=self.inputs["usage"].get(),
            dependencies=self.inputs["dependencies"].get(),
            license=self.inputs["license_info"].get(),
            badges=selected_badges
        )
        if self.logo_path:
            text = f"![Logo]({self.logo_path})\n\n" + text
        self.txt_preview.delete("0.0", "end")
        self.txt_preview.insert("0.0", text)

    # ---------------------
    # Upload Logo
    # ---------------------
    def upload_logo(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg *.gif")])
        if path:
            self.logo_path = path
            self.lbl_logo.configure(text=os.path.basename(path))
            self.session["logo_path"] = path
            save_session(self.session)
            self.live_preview_update()

    # ---------------------
    # Collect Inputs
    # ---------------------
    def collect_inputs(self):
        data = {k: e.get() for k,e in self.inputs.items()}
        data["api_key"] = self.entry_api.get().strip()
        data["api_choice"] = self.api_choice.get()
        data["badges"] = {k:v.get() for k,v in self.badge_vars.items()}
        data["template"] = self.template_choice.get()
        data["logo_path"] = self.logo_path
        save_session(data)
        return data

    # ---------------------
    # Copy to Clipboard
    # ---------------------
    def copy_to_clipboard(self):
        content = self.txt_preview.get("0.0", "end").strip()
        if content:
            pyperclip.copy(content)
            messagebox.showinfo("Copied", "README copied to clipboard!")

    # ---------------------
    # Start Generation Thread
    # ---------------------
    def start_generation(self):
        data = self.collect_inputs()
        if not data["api_key"]:
            messagebox.showwarning("API Key Missing", "Please enter your API key")
            return
        threading.Thread(target=self.generate_readme, args=(data,), daemon=True).start()

    # ---------------------
    # Generate README
    # ---------------------
    def generate_readme(self, data):
        self.progress.set(0)
        self.txt_output.delete("0.0", "end")
        self.txt_output.insert("0.0", "Generating README... 🎯\n")
        template = TEMPLATES.get(data["template"], TEMPLATES["Professional"])
        selected_badges = " ".join([BADGES_OPTIONS[k] for k,v in data["badges"].items() if v])

        prompt = f"""
Generate a professional GitHub README in Markdown including:
- Project Name: {data['project_name']}
- Tagline: {data['tagline']}
- Purpose: {data['purpose']}
- Features: {data['features']}
- Installation: {data['installation']}
- Usage: {data['usage']}
- Dependencies: {data['dependencies']}
- License: {data['license_info']}
- Badges: {selected_badges}
Include emojis and good GitHub formatting.
"""
        readme_text = None

        for i in range(0, 101, 5):
            time.sleep(0.02)
            self.progress.set(i/100)

        if data["api_choice"] == "openrouter":
            headers = {"Authorization": f"Bearer {data['api_key']}", "Content-Type": "application/json"}
            body = {"model": "gpt-4o-mini", "messages":[{"role":"user","content":prompt}], "max_tokens":1600, "temperature":0.7}
            try:
                response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=body)
                if response.status_code == 200:
                    readme_text = response.json()["choices"][0]["message"]["content"]
                else:
                    readme_text = f"OpenRouter API Error {response.status_code}: {response.text}"
            except Exception as e:
                readme_text = f"OpenRouter API Exception: {e}"
        else:
            if openai is None:
                readme_text = "OpenAI SDK not installed. Install with `pip install openai`"
            else:
                try:
                    openai.api_key = data["api_key"]
                    resp = openai.ChatCompletion.create(model="gpt-4", messages=[{"role":"user","content":prompt}], max_tokens=1600, temperature=0.7)
                    readme_text = resp.choices[0].message.content
                except Exception as e:
                    readme_text = f"ChatGPT API Exception: {e}"

        self.progress.set(1.0)
        time.sleep(0.2)
        self.txt_output.delete("0.0", "end")
        self.txt_output.insert("0.0", readme_text or "Failed to generate README")
        self.txt_preview.delete("0.0", "end")
        self.txt_preview.insert("0.0", readme_text or "Failed to generate README")

        # Save to file
        try:
            filename = filedialog.asksaveasfilename(defaultextension=".md", filetypes=[("Markdown", "*.md"), ("PDF", "*.pdf"), ("HTML", "*.html")])
            if filename:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(readme_text)
        except Exception:
            pass

# -------------------------
# Run App
# -------------------------
if __name__ == "__main__":
    app = AdvancedReadmeApp()
    app.mainloop()
