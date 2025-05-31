import streamlit as st
import json, uuid, subprocess, sys, os, re, time
from concurrent.futures import ThreadPoolExecutor
import requests
from requests.auth import HTTPBasicAuth


ROOT    = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND = os.path.join(ROOT, "backend")
sys.path.insert(0, BACKEND)
from gpt_parser import parse_bug_with_lmstudio


st.set_page_config(page_title="AI Auto Bug Tester", layout="wide")
st.markdown(
    """
    <style>
      /* Container width */
      .block-container {
        max-width: 1000px;
        padding-top: 1rem;
        padding-bottom: 1rem;
      }
      /* Base font size */
      html, body, .streamlit-expanderHeader, .css-1d391kg {
        font-size: 14px !important;
      }
      /* Shrink input and button text */
      .stTextArea textarea, .stTextInput input, .stButton>button {
        font-size: 14px !important;
      }
      /* Tighter spacing on columns */
      .column {
        padding: 0.5rem !important;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🛠️ AI Auto Bug Tester with Jira Integration")


col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("🔗 Fetch from Jira")
    jira_base  = st.text_input("Jira Base URL", value="https://your-domain.atlassian.net")
    jira_user  = st.text_input("Email / Username")
    jira_token = st.text_input("API Token (or App Password)", type="password")
    issue_key  = st.text_input("Issue Key (e.g. PROJ-123)")

    if st.button("Fetch Issue Description"):
        if not (jira_base and jira_user and jira_token and issue_key):
            st.error("Fill in all Jira fields.")
        else:
            api_url = f"{jira_base.rstrip('/')}/rest/api/3/issue/{issue_key}?fields=description"
            try:
                resp = requests.get(
                    api_url,
                    auth=HTTPBasicAuth(jira_user, jira_token),
                    headers={"Accept": "application/json"},
                )
                resp.raise_for_status()
                adf = resp.json()["fields"]["description"]

                def extract_text(node):
                    t = node.get("type")
                    txt = ""
                    if t in ("paragraph", "heading"):
                        for c in node.get("content", []):
                            txt += extract_text(c)
                        txt += "\n\n"
                    elif t == "text":
                        txt += node.get("text", "")
                    elif t in ("bulletList", "orderedList"):
                        for li in node.get("content", []):
                            for c in li.get("content", []):
                                line = extract_text(c).strip().splitlines()[0]
                                txt += "- " + line + "\n"
                        txt += "\n"
                    else:
                        for c in node.get("content", []):
                            txt += extract_text(c)
                    return txt

                bug_desc = extract_text(adf) if isinstance(adf, dict) else str(adf)
                st.success(f"Fetched {issue_key}")
                st.session_state.bug_text = bug_desc
            except Exception as e:
                st.error(f"Jira fetch failed: {e}")

with col2:
    st.subheader("📝 Bug Report & Reproduce")
    bug_text = st.text_area(
        "Bug Report (or fetched)",
        value=st.session_state.get("bug_text", ""),
        height=200
    )

    if st.button("Reproduce Bug"):
        if not bug_text.strip():
            st.warning("Provide a bug report or fetch from Jira first.")
        else:
            log_box      = st.empty()
            progress_bar = st.progress(0)
            status_text  = st.empty()
            status_text.text("Parsing… 0%")

            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(parse_bug_with_lmstudio, bug_text)
                fake = 0
                while not future.done():
                    time.sleep(0.5)
                    fake = min(fake + 10, 90)
                    progress_bar.progress(fake)
                    status_text.text(f"Parsing… {fake}%")
                steps = future.result()
                progress_bar.progress(100)
                status_text.text("Parsing done — launching browser…")

            for s in steps:
                if s.get("action") == "click" and "text" not in s:
                    s["text"] = "Login" if "login" in bug_text.lower() else ""

            os.makedirs(os.path.join(BACKEND, "outputs"), exist_ok=True)
            rid         = str(uuid.uuid4())
            steps_path  = os.path.join(BACKEND, f"outputs/steps_{rid}.json")
            result_path = os.path.join(BACKEND, f"outputs/result_{rid}.json")
            with open(steps_path, "w") as f:
                json.dump(steps, f, indent=2)

            status_text.text("Starting browser…")
            progress_bar.progress(0)
            browser_launched = False
            fake = 0

            cmd = [
                sys.executable,
                os.path.join(BACKEND, "executor.py"),
                steps_path,
                result_path
            ]
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )

            logs = ""
            while True:
                line = proc.stdout.readline()
                if not line and proc.poll() is not None:
                    break
                if line:
                    logs += line
                    log_box.text("\n".join(logs.splitlines()[-50:]))

                    if "Playwright started (headed)" in line and not browser_launched:
                        browser_launched = True
                        progress_bar.progress(100)
                        status_text.text("Browser launched — executing…")
                        continue
                    if not browser_launched and fake < 90:
                        fake += 10
                        progress_bar.progress(fake)
                        status_text.text(f"Launching… {fake}%")
                        time.sleep(0.1)

            proc.wait()
            if not browser_launched:
                progress_bar.progress(100)
                status_text.text("Browser launched — executing…")

            status_text.text("Execution complete!")

            if os.path.exists(result_path):
                with open(result_path) as f:
                    result = json.load(f)

                st.markdown(result["report_md"], unsafe_allow_html=True)
                st.markdown("### Step-by-Step Screenshots")
                for i, img in enumerate(result["screenshots"], 1):
                    st.image(img, caption=f"Step {i}")

                st.download_button(
                    "📥 Download Markdown Report",
                    result["report_md"],
                    "bug_report.md",
                    "text/markdown"
                )
            else:
                st.error("Execution failed.")
