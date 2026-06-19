# 🚀 Elitea QA Documentation - Local Setup Guide

Welcome! This guide will help you set up and run the Elitea QA Documentation locally on your machine. Follow these simple steps, and you'll be up and running in no time! 

---

## 📋 Prerequisites

Before you begin, make sure you have the following installed on your computer:

### Required Software

1. **Git** - Version control system
   - **macOS**: Install via [Homebrew](https://brew.sh/): `brew install git`
   - **Windows**: Download from [git-scm.com](https://git-scm.com/download/win)
   
2. **Python 3.8 or higher** - Programming language
   - **macOS**: Install via [Homebrew](https://brew.sh/): `brew install python`
   - **Windows**: Download from [python.org](https://www.python.org/downloads/)
   - ⚠️ **Important for Windows**: Check "Add Python to PATH" during installation!

3. **Visual Studio Code (VS Code)** - Code editor (Recommended)
   - Download from [code.visualstudio.com](https://code.visualstudio.com/)

### Verify Installation

Open your terminal (macOS) or Command Prompt/PowerShell (Windows) and run:

```bash
git --version
python --version  # or python3 --version on macOS
```

You should see version numbers for both commands. If not, revisit the installation steps above.

---

## 🔧 Step 1: Clone the Repository

### Option A: Using VS Code (Recommended for Beginners)

1. Open **VS Code**
2. Press `Ctrl+Shift+P` (Windows) or `Cmd+Shift+P` (macOS)
3. Type **"Git: Clone"** and press Enter
4. Paste this URL: `https://github.com/EliteaAI/elitea-testing.git`
5. Choose a folder where you want to save the project
6. Click **"Open"** when prompted

### Option B: Using Terminal/Command Line

1. Open Terminal (macOS) or Command Prompt (Windows)
2. Navigate to where you want to save the project:
   ```bash
   cd ~/Documents  # Example: Navigate to Documents folder
   ```
3. Clone the repository:
   ```bash
   git clone https://github.com/EliteaAI/elitea-testing.git
   ```
4. Navigate into the project folder:
   ```bash
   cd elitea-testing
   ```
5. Open the project in VS Code:
   ```bash
   code .
   ```

---

## 🐍 Step 2: Set Up Python Virtual Environment

A virtual environment keeps your project dependencies isolated from your system Python.

### macOS / Linux

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

### Windows (Command Prompt)

```cmd
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate
```

### Windows (PowerShell)

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\Activate.ps1
```

**⚠️ PowerShell Users**: If you get an error about execution policy, run this first:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**✅ Success Indicator**: You should see `(venv)` at the beginning of your terminal prompt.

---

## 📦 Step 3: Install Dependencies

With your virtual environment activated, install all required Python packages:

```bash
pip install -r requirements.txt
```

This will install:
- **MkDocs** - Documentation generator
- **Material for MkDocs** - Beautiful theme
- **mkdocs-glightbox** - Image gallery plugin
- Other dependencies

**⏱️ Note**: This may take 1-2 minutes depending on your internet connection.

---

## 🚀 Step 4: Run the Documentation Server

Now you're ready to preview the documentation!

### Start the Server

**Standard Mode** (Recommended):
```bash
mkdocs serve
```

**Development Mode** (Faster, skips some checks):
```bash
mkdocs serve --dirty
```

**With Explicit Live Reload** (if auto-reload isn't working):
```bash
mkdocs serve --livereload
```

**✅ Success Indicator**: You should see output like:
```
INFO    -  Building documentation...
INFO    -  Cleaning site directory
INFO    -  Documentation built in 2.34 seconds
INFO    -  [12:34:56] Watching paths for changes: 'docs', 'mkdocs.yml'
INFO    -  [12:34:56] Serving on http://127.0.0.1:8010/
```

**🔄 Auto-Reload**: MkDocs automatically watches for changes to your `.md` files and reloads the browser!

### View the Documentation

Open your web browser and go to:
```
http://127.0.0.1:8010/
```

**🎉 Congratulations!** You should now see the Elitea QA Documentation website running locally!

### Stop the Server

When you're done, press `Ctrl+C` in the terminal to stop the server.

---

## 🔄 Daily Workflow

**✅ Auto-Reload (No Restart Needed)**:
- Edit any `.md` files in the `docs/` folder
- Add new markdown files
- Changes are **automatically detected and reloaded** in your browser within 1-2 seconds
- Just save the file and watch your browser update!

**⚠️ Manual Restart Required**:
- Changes to `mkdocs.yml` configuration
- Changes to CSS files (`docs/extra_css/`)
- Changes to JavaScript files (`docs/extra_js/`)
- Changes to theme overrides (`docs/overrides/`)
- Installing new plugins

**How to Restart**:
1. Press `Ctrl+C` in the terminal to stop the server
2. Run `mkdocs serve` again
2. Open the integrated terminal (`` Ctrl+` `` or `` Cmd+` ``)
3. Activate virtual environment:
   - **macOS/Linux**: `source venv/bin/activate`
   - **Windows (CMD)**: `venv\Scripts\activate`
   - **Windows (PowerShell)**: `venv\Scripts\Activate.ps1`
4. Start the server: `mkdocs serve`
5. Open browser to `http://127.0.0.1:8010/`

### Making Changes

- Edit any `.md` files in the `docs/` folder
- Changes are **automatically reloaded** in your browser
- No need to restart the server!

### Finishing Work

1. Press `Ctrl+C` to stop the server
2. Type `deactivate` to exit the virtual environment (optional)
3. Close VS Code or continue working on other projects

---

## 📁 Project Structure

```
elitea-testing/
├── docs/                      # Documentation markdown files
│   ├── index.md              # Homepage
│   ├── bug-management/       # Bug tracking docs
│   ├── qa-processes/         # QA process docs
│   ├── test-execution/       # Test execution guides
│   ├── reference-templates/  # Templates (including release checklist)
│   ├── assets/               # Images and media
│   ├── extra_css/            # Custom CSS styling
│   └── extra_js/             # Custom JavaScriptwith auto-reload |
| `mkdocs serve --dirty` | Start server with faster builds (skips unchanged files) |
| `mkdocs serve --livereload` | Start server with explicit live reload enabled |
| `mkdocs serve --dev-addr 127.0.0.1:8010` | Start server on specific port |
| `mkdocs serve --watch-theme` | Also watch theme files for changes
├── requirements.txt          # Python dependencies
├── venv/                     # Virtual environment (after setup)
└── LOCAL_SETUP.md           # This file!
```

---

## 🛠️ Useful Commands

| Command | Description |
|---------|-------------|
| `mkdocs serve` | Start local development server |
| `mkdocs serve --dev-addr 127.0.0.1:8010` | Start server on specific port |
| `mkdocs build` | Build static site to `site/` folder |
| `mkdocs build --clean` | Clean build (removes old files) |
| `pip install --upgrade -r requirements.txt` | Update dependencies |
| `pip list` | Show installed packages |

---

## 🎨 Customizing the Port

By default, the server runs on port **8010**. To change it:

### Temporarily (Command Line)
```bash
mkdocs serve --dev-addr 127.0.0.1:8000
```

### Permanently (Edit Configuration)
1. Open `mkdocs.yml`
2. Change the `dev_addr` line:
   ```yaml
   dev_addr: 127.0.0.1:8000  # Change 8010 to your preferred port
   ```

---

## 🐛 Troubleshooting

### Issue: `command not found: python` or `command not found: python3`

**Solution**: 
- **macOS**: Use `python3` instead of `python`
- **Windows**: Make sure Python was added to PATH during installation

### Issue: `No module named 'mkdocs'`

**Solution**: 
- Make sure virtual environment is activated (you should see `(venv)` in terminal)
- Run `pip install -r requirements.txt` again
For Markdown (.md) Files**:
1. Wait 1-2 seconds after saving (auto-reload takes a moment)
2. Check terminal for build errors
3. Hard refresh browser: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (macOS)
4. Try `mkdocs serve --livereload` to force live reload

**For Configuration/Theme Files** (mkdocs.yml, CSS, JS):
1. Stop server with `Ctrl+C`
2. Restart with `mkdocs serve`
3. Hard refresh browser

**For Theme Customizations** (CSS/JS in extra_css or extra_js):
1. Stop server with `Ctrl+C`  
2. Restart with `mkdocs serve --watch-theme` to watch theme files
3. Hard refresh browser to clear cached CSS/JS

**Browser Cache Issues**:
- Press `Ctrl+Shift+Delete` (Windows) or `Cmd+Shift+Delete` (macOS)
- Clear cached images and files
- Or use Incognito/Private browsing mode for testing
- Use Command Prompt instead of PowerShell, OR
- Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` in PowerShell

### Issue: Port 8010 is already in use

**Solution**:
- Check if MkDocs is already running in another terminal
- Use a different port: `mkdocs serve --dev-addr 127.0.0.1:8011`
- Kill the process using port 8010

### Issue: Changes not reflecting in browser

**Solution**:
- Hard refresh the browser: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (macOS)
- Stop and restart `mkdocs serve`
- Clear browser cache

### Issue: Template files not showing

**Solution**:
- The `draft_docs: ""` setting in `mkdocs.yml` is already configured
- Make sure you're viewing files in the `reference-templates/` folder

---

## 📚 Additional Resources

- [MkDocs Documentation](https://www.mkdocs.org/)
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
- [Markdown Guide](https://www.markdownguide.org/)
- [Git Basics](https://git-scm.com/book/en/v2/Getting-Started-Git-Basics)

---

## 🤝 Getting Help

If you encounter any issues not covered in this guide:

1. Check the [Troubleshooting](#-troubleshooting) section above
2. Ask your team lead or mentor
3. Check existing issues in the GitHub repository
4. Create a new issue with detailed error messages

---

## ✅ Quick Reference Checklist

- [ ] Git installed
- [ ] Python 3.8+ installed
- [ ] VS Code installed
- [ ] Repository cloned
- [ ] Virtual environment created
- [ ] Virtual environment activated
- [ ] Dependencies installed via `pip install -r requirements.txt`
- [ ] Server running with `mkdocs serve`
- [ ] Documentation visible at `http://127.0.0.1:8010/`

---

**Happy Documenting! 🎉**

If you found this guide helpful, consider sharing it with your teammates!
