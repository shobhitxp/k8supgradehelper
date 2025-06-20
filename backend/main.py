from fastapi import FastAPI, UploadFile, Form
from pluto_analysis import run_pluto
from ai_module import analyze_deprecated_apis
import os

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Using system environment variables.")

app = FastAPI()

@app.post("/analyze/")
async def analyze(file: UploadFile, version: str = Form(...)):
    try:
        content = await file.read()
        with open("kubeconfig.yaml", "wb") as f:
            f.write(content)
        
        deprecated = run_pluto(".")
        ai_response = analyze_deprecated_apis(deprecated)
        return {"ai_response": ai_response, "pluto_output": deprecated}
    except Exception as e:
        return {"error": f"Internal server error: {str(e)}"}

