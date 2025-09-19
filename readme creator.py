"""
📄 GUI README Generator
Author: aaryan
Generates professional GitHub README using OpenRouter or OpenAI ChatGPT API.
Fully desktop app using CustomTkinter, no terminal or browser required.
"""

import json
import time
import threading
import requests
import customtkinter as ctk
from tkinter import messagebox, filedialog

try:
    import openai
except ImportError:
    openai = None

# -------------------------
# GUI Application
# -------------------------
class ReadmeGeneratorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("📄 README Generator — Desktop AI")
        self.geometry("720x600")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        # ---------------------
        # Input Fields
        # ---------------------
        self.inputs = {}
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
            ctk.CTkLabel(self, text=label).grid(row=row, column=0, padx=12, pady=6, sticky="w")
            entry = ctk.CTkEntry(self, width=500)
            entry.grid(row=row, column=1, padx=12, pady=6)
            self.inputs[key] = entry
            row += 1

        # API Key
        ctk.CTkLabel(self, text="API Key (OpenRouter/OpenAI)").grid(row=row, column=0, padx=12, pady=6, sticky="w")
        self.entry_api = ctk.CTkEntry(self, width=500, show="*")
        self.entry_api.grid(row=row, column=1, padx=12, pady=6)
        row += 1

        # API Choice
        ctk.CTkLabel(self, text="Select API").grid(row=row, column=0, padx=12, pady=6, sticky="w")
        self.api_choice = ctk.StringVar(value="openrouter")
        ctk.CTkOptionMenu(self, variable=self.api_choice, values=["openrouter", "chatgpt"]).grid(row=row, column=1, padx=12, pady=6, sticky="w")
        row += 1

        # Generate Button
        self.btn_generate = ctk.CTkButton(self, text="Generate README", command=self.start_generation)
        self.btn_generate.grid(row=row, column=0, columnspan=2, pady=12)
        row += 1

        # Output Box
        self.txt_output = ctk.CTkTextbox(self, width=680, height=200)
        self.txt_output.grid(row=row, column=0, columnspan=2, padx=12, pady=6)

    # ---------------------
    # Collect Inputs
    # ---------------------
    def collect_inputs(self):
        data = {key: entry.get() for key, entry in self.inputs.items()}
        data["api_key"] = self.entry_api.get().strip()
        data["api_choice"] = self.api_choice.get()
        return data

    # ---------------------
    # Generate README Thread
    # ---------------------
    def start_generation(self):
        data = self.collect_inputs()
        if not data["api_key"]:
            messagebox.showwarning("API Key Missing", "Please enter your API key")
            return
        self.txt_output.delete("0.0", "end")
        self.txt_output.insert("0.0", "Generating README...")
        threading.Thread(target=self.generate_readme, args=(data,), daemon=True).start()

    # ---------------------
    # Generate README
    # ---------------------
    def generate_readme(self, data):
        prompt = f"""
Generate a professional GitHub README in Markdown format.

Project Name: {data['project_name']}
Tagline: {data['tagline']}
Purpose: {data['purpose']}
Features: {data['features']}
Installation: {data['installation']}
Usage: {data['usage']}
Dependencies: {data['dependencies']}
License: {data['license_info']}

Include sections: Title & Tagline, Features, Installation, Usage, Dependencies, License.
Make it professional, GitHub-ready, and well-formatted.
"""
        readme_text = None

        if data["api_choice"] == "openrouter":
            headers = {
                "Authorization": f"Bearer {data['api_key']}",
                "Content-Type": "application/json"
            }
            body = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1200,
                "temperature": 0.7
            }
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
                    resp = openai.ChatCompletion.create(
                        model="gpt-4",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=1200,
                        temperature=0.7
                    )
                    readme_text = resp.choices[0].message.content
                except Exception as e:
                    readme_text = f"ChatGPT API Exception: {e}"

        self.txt_output.delete("0.0", "end")
        self.txt_output.insert("0.0", readme_text or "Failed to generate README")

        # Save to file
        try:
            filename = filedialog.asksaveasfilename(defaultextension=".md", filetypes=[("Markdown", "*.md")])
            if filename:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(readme_text)
        except Exception:
            pass

# -------------------------
# Run App
# -------------------------
if __name__ == "__main__":
    app = ReadmeGeneratorApp()
    app.mainloop()
