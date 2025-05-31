import re
import json
import requests

LM_API_URL = "http://localhost:1234/v1/completions"
MODEL_NAME = "phi-3-mini-128k-instruct-imatrix-smashed"

def extract_json_array(text: str):
    match = re.search(r"\[\s*{.*?}\s*\]", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return []
    return []

def parse_bug_with_lmstudio(bug_text: str):
    prompt = f"""
You are a UI automation expert.

Convert the following bug report into a JSON array of test steps.
Use only these action values:
- "go_to"   (navigate to a URL)
- "type"    (enter text into a field)
- "click"   (click a button or link)  **AND** capture its visible label as "text"
- "expect"  (assert that text appears on screen)

Return only the JSON array. Example output:
[
  {{"action":"go_to", "target":"https://example.com", "value":""}},
  {{"action":"type",  "target":"input[name='username']", "value":"admin"}},
  {{"action":"click", "target":"button[type='submit']", "value":"", "text":"Login"}},
  {{"action":"expect","target":"", "value":"Invalid credentials"}}
]
Bug Report:
{bug_text}
"""
    resp = requests.post(
        LM_API_URL,
        headers={"Content-Type": "application/json"},
        json={"model": MODEL_NAME, "prompt": prompt, "max_tokens": 600, "temperature": 0.2},
    )
    return extract_json_array(resp.json()["choices"][0]["text"])
