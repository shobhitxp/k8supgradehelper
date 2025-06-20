# KubeSmartUp: Kubernetes API Upgrade Automation Tool

KubeSmartUp automates the detection and migration of deprecated Kubernetes APIs using AI-powered analysis and Git automation.

---

## 🚀 Quick Start: Run from a New Terminal

### 1. **Clone the Repository**
```sh
git clone <your-repo-url>
cd k8supgradeai-infraaicode
```

### 2. **Install Pluto CLI**
Pluto is required for deprecated API detection.
```sh
go install github.com/fairwindsops/pluto@latest
# Make sure $HOME/go/bin is in your $PATH
```

### 3. **Set Up Python Environment**
```sh
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install python-dotenv
```

### 4. **Set Up OpenAI API Key**
Create a `.env` file in the `backend/` directory:
```sh
echo "OPENAI_API_KEY=sk-..." > .env
```
Or export it in your terminal before running the backend:
```sh
export OPENAI_API_KEY=sk-...
```

### 5. **Start the FastAPI Backend**
```sh
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 6. **Test the CLI Tool**
Open a new terminal, activate the venv, and run:
```sh
cd backend
source venv/bin/activate
python cli/main_cli.py sample-deprecated.yaml --version 1.25
```
Replace `sample-deprecated.yaml` with your own manifest if desired.

### 7. **Test the API Directly**
```sh
curl -F "file=@sample-deprecated.yaml" -F "version=1.25" http://localhost:8000/analyze/
```

### 8. **Use the Web UI**
Open `frontend/ui_pluto.html` in your browser for a graphical interface.

---

## 🛠️ Project Structure
- `backend/` - FastAPI backend, CLI, AI, and Git integration
- `frontend/` - Web UI (open `ui_pluto.html` in browser)
- `sample-deprecated.yaml` - Example manifest with deprecated APIs

## 🧩 Features
- Detects deprecated Kubernetes APIs using Pluto
- AI-powered migration suggestions (OpenAI)
- CLI, API, and Web UI interfaces
- Git automation for PRs (see `backend/git_ops.py`)

## 📝 Prerequisites
- Python 3.9+
- Go (for Pluto)
- OpenAI API key
- (Optional) GitHub/GitLab token for PR automation

## 🧑‍💻 Troubleshooting
- **Pluto not found?** Make sure it's in your `$PATH`.
- **OpenAI key not found?** Set it in `.env` or export before running backend.
- **CLI file not found?** Use correct path: `python cli/main_cli.py ...` from inside `backend/`.
- **API errors?** Check backend logs for details.

## 📚 More
- For advanced usage, see `backend/ai_module.py` to customize AI prompts.
- For Git automation, see `backend/git_ops.py`.

---

**Backup of the original README is in `README.old.md`.**
