# 📄 ReadMe Maestro — AI-Powered Desktop App

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg) ![CustomTkinter](https://img.shields.io/badge/CustomTkinter-GUI-green.svg) ![MIT License](https://img.shields.io/badge/License-MIT-yellow.svg) ![OpenAI](https://img.shields.io/badge/OpenAI-AI-purple.svg)

**ReadMe Maestro** — *Transform your project ideas into professional GitHub READMEs instantly.*
Generate, preview, and export Markdown or PDF READMEs using AI — all from a **desktop application**.

---

## ✨ Features

* 🖥 **Modern Desktop GUI** — Built with CustomTkinter for a responsive, visually appealing interface.
* 🤖 **AI-Powered Generation** — Supports OpenAI/OpenRouter models to craft professional README content.
* 🗝 **API Key Management** — Store your API key locally for seamless future use.
* 📄 **Dynamic Project Info** — Input project name, description, and features.
* 🛠 **Badge Selection** — Add relevant badges (Python, GitHub Actions, License, OpenAI, etc.) with dropdowns.
* ⌨ **User-Friendly Input** — Add features and badges easily with interactive buttons.
* 🌟 **Animated Preview** — Typing animation and emoji spinner while generating README.
* 💾 **Export Options** — Save your README as Markdown (.md) or PDF (.pdf) files.
* 📊 **History Panel** — View your recent README generations and revisit them quickly.
* 🔄 **Session Management** — Autosave project data and restore previous session.
* 🎨 **Themes & Visual Customization** — Switch between dark, light, and gradient themes.
* 🕒 **Undo & Edit** — Modify features or badges and update README instantly.
* 💡 **Fallback Template** — Generates a local README if AI API is unavailable.
* 🔧 **Offline Usable** — Heuristic fallback ensures the app works without internet.
* 📂 **Organized Exports** — All exported files stored in a dedicated folder.
* 📝 **Sectioned Content** — README includes Title, Description, Features, Badges, Installation, Usage, License.
* ⚡ **Smooth Performance** — Threaded processing keeps the UI responsive.
* 🔢 **Feature Limit & Validation** — Prevents duplicate badges or features.
* 💫 **Animated Progress Bar** — Tracks README generation in real-time.
* 🏆 **Professional Output** — README follows GitHub best practices.
* 🛡 **Error Handling** — Friendly messages for API or export issues.
* 🖼 **Visual Enhancements** — Color-coded sections, font styling, and spacing for readability.
* 🧩 **Custom Section Reordering** — Reorder features or badges interactively.
* 📑 **Preview Markdown** — Optional live Markdown view (planned in future updates).
* 🏷 **Multiple Badge Support** — Select multiple badges for a polished project header.
* 📊 **Quick Analytics** — Word count and section metrics in history panel.

---

## 🛠 Installation

1. Ensure **Python 3.9+** is installed.
2. Clone the repository:

```bash
git clone https://github.com/yourusername/readme-maestro.git
cd readme-maestro
```

3. Install required dependencies:

```bash
pip install -r requirements.txt
```

> `requirements.txt` includes: `customtkinter`, `pillow`, `openai`, `reportlab`

---

## 🚀 Usage

1. Run the app:

```bash
python app.py
```

2. Enter your **OpenAI API key** (optional for AI features).
3. Fill in your project **name**, **description**, **features**, and **badges**.
4. Click **Generate README** — watch the animated preview!
5. Export your README as **Markdown** or **PDF**.
6. Revisit recent generations in the **History Panel**.

---

## 💡 Notes

* If **no API key** is provided, the app uses a local fallback template.
* **API key** is stored securely in local storage for future sessions.
* All exported files are saved in the `readme_exports` folder.
* Supports multiple badges, animated preview, and undo functionality.

---

## 📦 Future Features

* Live Markdown preview panel
* Multi-tabbed badge selection
* Customizable themes & fonts
* Advanced AI templates and styles
* Collaborative README generation

---

## 📄 License

This project is licensed under the **MIT License**. See `LICENSE` for details.

---

## 🔗 Links

* [GitHub Repository](https://github.com/Aaryanbanskota/readme-maestro)
* [OpenAI API](https://platform.openai.com/)
* [CustomTkinter Documentation](https://github.com/TomSchimansky/CustomTkinter)
