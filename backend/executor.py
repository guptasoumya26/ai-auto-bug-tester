import sys
import json
import base64
import re
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import requests

LM_API_URL = "http://localhost:1234/v1/completions"
MODEL_NAME = "phi-3-mini-128k-instruct-imatrix-smashed"

used_selectors = set()

def clean_selector(text: str) -> str:
    text = text.strip().replace("```css", "").replace("```", "")
    text = re.sub(r"(?i)<!--.*?-->", "", text)
    text = re.sub(r"(?i)explanation.*?:", "", text)
    text = re.sub(r"(?i)^.*?selector could be:", "", text)
    matches = re.findall(
        r"(input\[.*?\]|button\[.*?\]|button\.\S+|input\.\S+|div\.\S+|span\.\S+|a\.\S+|#\S+)",
        text
    )
    if matches:
        sel = matches[0].strip().strip('`"')
        print("Extracted fallback selector:", sel)
        return sel
    print("No valid CSS selector extracted from fallback.")
    return ""

def run(test_steps, browser="chromium", headless=False):
    pw = sync_playwright().start()
    br = getattr(pw, browser).launch(headless=headless)
    page = br.new_page()

    report = []
    screenshots = []
    md_lines = ["# Test Execution Report", ""]

    for idx, step in enumerate(test_steps, 1):
        action = step.get("action")
        target = step.get("target", "")
        value  = step.get("value", "")
        text   = step.get("text", "")
        log = {"step": action, "target": target, "value": value, "text": text}

        try:
            print(f"Step {idx}: {action} -> {target or text or value}")
            if action == "go_to":
                page.goto(target)
                page.wait_for_load_state("networkidle", timeout=10000)
                print("  Navigated to", target)
                log["result"] = f"Navigated to `{target}`"

            elif action == "type":
                page.fill(target, value)
                page.wait_for_timeout(300)
                print(f"  Typed \"{value}\"")
                log["result"] = f"Typed \"{value}\""

            elif action == "click":
                if text:
                    try:
                        page.get_by_role("button", name=text).click()
                    except:
                        page.click(target)
                else:
                    page.click(target)
                try:
                    page.wait_for_load_state("networkidle", timeout=8000)
                except:
                    page.wait_for_timeout(500)
                print(f"  Clicked \"{text or target}\"")
                log["result"] = f"Clicked \"{text or target}\""

            elif action == "expect":
                page.get_by_text(value).wait_for(timeout=10000)
                print(f"  Found expected text \"{value}\"")
                log["result"] = f"Found expected text `{value}`"

            else:
                raise ValueError("Unknown action: " + action)

        except Exception as e:
            print("  Error:", e)
            log["error"] = str(e)

        # Take screenshot
        img_bytes = page.screenshot()
        b64 = base64.b64encode(img_bytes).decode()
        screenshots.append("data:image/png;base64," + b64)

        # Build Markdown
        detail = log.get("result", log.get("error", ""))
        md_lines.append(f"### Step {idx}: `{action}`")
        md_lines.append(f"- Detail: {detail}")
        md_lines.append(f"![step-{idx}](data:image/png;base64,{b64})")
        md_lines.append("")

        report.append(log)

    print("All steps done, closing browser")
    br.close()
    pw.stop()

    return {
        "report": report,
        "screenshots": screenshots,
        "report_md": "\n".join(md_lines)
    }

if __name__ == "__main__":
    steps_file  = sys.argv[1]
    result_file = sys.argv[2]

    with open(steps_file, "r") as f:
        steps = json.load(f)

    outcome = run(steps, headless=False)

    with open(result_file, "w") as f:
        json.dump(outcome, f)

    print("Result written to", result_file)
