from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uuid, os, json, subprocess, sys

from gpt_parser import parse_bug_with_lmstudio

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class BugInput(BaseModel):
    bug_text: str

@app.post("/execute")
def execute_bug(bug: BugInput):
    
    steps = parse_bug_with_lmstudio(bug.bug_text)
    for s in steps:
        if s.get("action") == "click" and "text" not in s:
            s["text"] = s.get("value") or "Click"

    
    test_id = str(uuid.uuid4())
    os.makedirs("outputs", exist_ok=True)
    steps_file  = f"outputs/steps_{test_id}.json"
    result_file = f"outputs/result_{test_id}.json"
    with open(steps_file, "w", encoding="utf-8") as f:
        json.dump(steps, f)

    
    python_exe = sys.executable
    subprocess.run(
        [python_exe, "executor.py", steps_file, result_file],
        check=True
    )

    
    with open(result_file, "r", encoding="utf-8") as f:
        result = json.load(f)

    return JSONResponse(content={
        "status":         "complete",
        "step_reports":   result["report"],
        "step_screenshots": result["screenshots"],
        "report_md":      result["report_md"],
    })
