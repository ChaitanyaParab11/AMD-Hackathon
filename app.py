import streamlit as st
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import time
import random
import difflib
import re

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Secure Java AI",
    layout="wide",
    initial_sidebar_state="collapsed"
)

MODEL_PATH = "../qwen_security_merged"


# -------------------------------------------------
# SESSION STATE
# -------------------------------------------------
if "history" not in st.session_state:
    st.session_state.history = []

if "last_original" not in st.session_state:
    st.session_state.last_original = ""

if "last_secure_code" not in st.session_state:
    st.session_state.last_secure_code = ""

if "last_vulnerability" not in st.session_state:
    st.session_state.last_vulnerability = ""


# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------
def sidebar():
    st.sidebar.title("🕘 History")

    if not st.session_state.history:
        st.sidebar.caption("No scans yet.")
    else:
        with st.sidebar.expander("View Previous Scans", expanded=False):
            for idx, item in enumerate(st.session_state.history[::-1], start=1):
                with st.expander(f"Scan {idx}", expanded=False):
                    st.code(item[:500], language="java")

    if st.sidebar.button("Clear History", use_container_width=True):
        st.session_state.history = []
        st.session_state.last_original = ""
        st.session_state.last_secure_code = ""
        st.session_state.last_vulnerability = ""
        st.rerun()


# -------------------------------------------------
# THEME CSS
# -------------------------------------------------
def apply_theme():
    bg_color = "#f8fafc"
    sidebar_bg = "#ffffff"
    card_bg = "#ffffff"
    card_bg_2 = "#f1f5f9"
    text_color = "#0f172a"
    muted_color = "#64748b"
    border_color = "rgba(15, 23, 42, 0.14)"
    input_bg = "#ffffff"
    input_border = "rgba(15, 23, 42, 0.22)"
    code_bg = "#f8fafc"
    tab_bg = "#e2e8f0"
    shadow = "0 12px 28px rgba(15,23,42,0.08)"
    header_bg = "#f8fafc"

    st.markdown(f"""
    <style>

    .stApp {{
        background: {bg_color};
        color: {text_color};
    }}

    header[data-testid="stHeader"] {{
        background: {header_bg};
    }}

    .block-container {{
        padding-top: 4.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 100% !important;
    }}

    [data-testid="stSidebar"] {{
        background-color: {sidebar_bg};
        border-right: 1px solid {border_color};
    }}

    [data-testid="stSidebar"] * {{
        color: {text_color};
    }}

    .main-title {{
        font-size: 2.55rem;
        font-weight: 850;
        letter-spacing: -0.04em;
        margin-bottom: 0.2rem;
        color: {text_color};
    }}

    .sub-title {{
        color: {muted_color};
        font-size: 1rem;
        margin-bottom: 1.6rem;
    }}

    [data-testid="stVerticalBlockBorderWrapper"] {{
        background: linear-gradient(180deg, {card_bg}, {card_bg_2});
        border: 1px solid {border_color};
        border-radius: 22px;
        box-shadow: {shadow};
    }}

    .empty-box {{
        border: 1px dashed {border_color};
        border-radius: 18px;
        padding: 2.3rem;
        text-align: center;
        color: {muted_color};
        background: {card_bg_2};
    }}

    .empty-box h3 {{
        color: {text_color};
        margin-bottom: 0.4rem;
    }}

    .stButton > button {{
        background: linear-gradient(90deg, #38bdf8, #22c55e);
        color: #020617;
        font-weight: 850;
        border-radius: 15px;
        height: 3.2rem;
        border: none;
        box-shadow: 0 8px 22px rgba(34,197,94,0.22);
    }}

    .stButton > button:hover {{
        color: #020617;
        border: none;
        transform: translateY(-1px);
        box-shadow: 0 12px 28px rgba(56,189,248,0.25);
    }}

    textarea {{
        font-family: Consolas, Monaco, monospace !important;
        font-size: 14px !important;
        background-color: {input_bg} !important;
        color: {text_color} !important;
        border: 1px solid {input_border} !important;
        border-radius: 14px !important;
    }}

    textarea::placeholder {{
        color: {muted_color} !important;
    }}

    [data-testid="stFileUploader"] {{
        background-color: {card_bg_2};
        border-radius: 14px;
        padding: 0.6rem;
        border: 1px solid {border_color};
    }}

    [data-testid="stMetric"] {{
        background-color: {card_bg_2};
        border: 1px solid {border_color};
        padding: 0.7rem 0.9rem;
        border-radius: 14px;
    }}

    [data-testid="stMetricValue"] {{
        font-size: 1.35rem;
        color: {text_color};
    }}

    [data-testid="stMetricLabel"] {{
        color: {muted_color};
    }}

    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background-color: transparent;
    }}

    .stTabs [data-baseweb="tab"] {{
        border-radius: 12px;
        padding: 8px 15px;
        background-color: {tab_bg};
        color: {text_color};
    }}

    .stTabs [aria-selected="true"] {{
        background: linear-gradient(90deg, #38bdf8, #22c55e) !important;
        color: #020617 !important;
        font-weight: 800;
    }}

    pre {{
        background-color: {code_bg} !important;
        border: 1px solid {border_color};
        border-radius: 16px !important;
    }}

    code {{
        color: {text_color} !important;
        font-size: 13.5px !important;
    }}

    h1, h2, h3, h4, h5, h6, p, label {{
        color: {text_color};
    }}

    [data-testid="stAlert"] {{
        border-radius: 15px;
    }}

    .stDownloadButton > button {{
        border-radius: 14px;
        font-weight: 800;
    }}

    </style>
    """, unsafe_allow_html=True)


# -------------------------------------------------
# MODEL CACHE
# -------------------------------------------------
@st.cache_resource
def load_model():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        torch_dtype=torch.bfloat16,
        device_map="auto"
    )

    return tokenizer, model


# -------------------------------------------------
# JAVA VALIDATION
# -------------------------------------------------
def is_java_code(code: str) -> bool:
    if not code or len(code.strip()) < 20:
        return False

    code_lower = code.lower()

    obvious_non_java_patterns = [
        r"\bdef\s+\w+\s*\(",
        r"\bprint\s*\(",
        r"\bfunction\s+\w+\s*\(",
        r"\bconsole\.log\s*\(",
        r"#include\s*<",
        r"\busing\s+namespace\s+std\b",
        r"<html",
        r"<!doctype html",
    ]

    for pattern in obvious_non_java_patterns:
        if re.search(pattern, code_lower):
            return False

    java_signals = [
        r"\bpublic\s+class\s+\w+",
        r"\bclass\s+\w+",
        r"\binterface\s+\w+",
        r"\benum\s+\w+",
        r"\brecord\s+\w+",
        r"\bimport\s+java\.",
        r"\bpackage\s+[\w.]+;",
        r"\bpublic\s+static\s+void\s+main\s*\(",
        r"\bSystem\.out\.print",
        r"\bnew\s+\w+\s*\(",
        r"\bString\s+\w+",
        r"\bint\s+\w+",
        r"\bboolean\s+\w+",
        r"\bprivate\s+\w+",
        r"\bprotected\s+\w+",
        r"\bpublic\s+\w+",
        r";",
        r"\{",
        r"\}",
    ]

    score = 0

    for pattern in java_signals:
        if re.search(pattern, code):
            score += 1

    has_braces = "{" in code and "}" in code
    has_semicolon = ";" in code
    has_java_structure = bool(
        re.search(r"\b(class|interface|enum|record)\s+\w+", code)
    )

    return score >= 4 and has_braces and (has_semicolon or has_java_structure)


# -------------------------------------------------
# PROMPT
# -------------------------------------------------
def build_prompt(code_text: str) -> str:
    return f"""
### Task
Analyze the given Java code.
Identify the vulnerability.
Then provide the fixed secure Java code.

Return output strictly in this format:

### Vulnerability
<name of vulnerability>

### Secure Code
<fixed secure Java code only>

### Java Code
{code_text}

### Vulnerability
"""


# -------------------------------------------------
# MODEL GENERATION
# -------------------------------------------------
def generate_secure_code(code_text, tokenizer, model):
    prompt = build_prompt(code_text)

    inputs = tokenizer(
        prompt,
        return_tensors="pt"
    ).to(model.device)

    outputs = model.generate(
        **inputs,
        max_new_tokens=768,
        do_sample=False,
        pad_token_id=tokenizer.eos_token_id
    )

    result = tokenizer.decode(
        outputs[0],
        skip_special_tokens=True
    )

    vulnerability, secure_code = parse_model_output(result)

    return vulnerability, secure_code


# -------------------------------------------------
# PARSING OUTPUT
# -------------------------------------------------
def parse_model_output(result: str):
    vulnerability = ""
    secure_code = ""

    if "### Vulnerability" in result:
        result_part = result.split("### Vulnerability")[-1].strip()
    else:
        result_part = result.strip()

    if "### Secure Code" in result_part:
        v_part, c_part = result_part.split("### Secure Code", 1)
        vulnerability = v_part.strip()
        secure_code = c_part.strip()
    else:
        vulnerability = result_part.strip()
        secure_code = ""

    secure_code = clean_secure_code(secure_code)

    return vulnerability, secure_code


def clean_secure_code(code: str):
    code = code.strip()

    if code.startswith("```java"):
        code = code.replace("```java", "", 1).strip()

    if code.startswith("```"):
        code = code.replace("```", "", 1).strip()

    if code.endswith("```"):
        code = code[:-3].strip()

    return code


# -------------------------------------------------
# CHATGPT STYLE STREAMING - SCROLLABLE OUTPUT
# -------------------------------------------------
def stream_code(text: str):
    placeholder = st.empty()
    displayed = ""

    if not text:
        placeholder.warning("No secure code was generated.")
        return

    chunk_size = 2
    typing_speed = 0.010

    for i in range(0, len(text), chunk_size):
        displayed += text[i:i + chunk_size]

        placeholder.code(
            displayed + "▌",
            language="java",
            height=360
        )

        time.sleep(random.uniform(typing_speed * 0.5, typing_speed * 1.5))

    placeholder.code(
        displayed,
        language="java",
        height=360
    )


# -------------------------------------------------
# DIFF VIEWER - SCROLLABLE OUTPUT
# -------------------------------------------------
def show_diff(original: str, modified: str):
    if not modified:
        st.warning("No secure code available for diff.")
        return

    diff = difflib.unified_diff(
        original.splitlines(),
        modified.splitlines(),
        fromfile="Original.java",
        tofile="Secure.java",
        lineterm=""
    )

    diff_text = "\n".join(diff)

    if not diff_text.strip():
        st.info("No differences found.")
    else:
        st.code(
            diff_text,
            language="diff",
            height=360
        )


# -------------------------------------------------
# INPUT PANEL
# -------------------------------------------------
def input_panel():
    st.markdown("### 🧠 Java Code Editor")

    uploaded_file = st.file_uploader(
        "Upload a `.java` file",
        type=["java"],
        accept_multiple_files=False
    )

    code_text = ""

    if uploaded_file is not None:
        code_text = uploaded_file.read().decode("utf-8")
        st.success(f"Uploaded: {uploaded_file.name}")

        code_text = st.text_area(
            "Edit uploaded code if needed",
            value=code_text,
            height=360
        )
    else:
        code_text = st.text_area(
            "Paste Java code here",
            height=360,
            placeholder="""public class UserLogin {
    public void loginUser(Connection connection, String username, String password) {
        String query = "SELECT * FROM users WHERE username = '" + username + "'";
    }
}"""
        )

    col_a, col_b = st.columns(2)

    with col_a:
        st.metric("Characters", len(code_text))

    with col_b:
        st.metric("Lines", len(code_text.splitlines()) if code_text else 0)

    return code_text


# -------------------------------------------------
# RESULT PANEL
# -------------------------------------------------
def result_panel(stream=False):
    vulnerability = st.session_state.last_vulnerability
    secure_code = st.session_state.last_secure_code
    original = st.session_state.last_original

    if not secure_code and not vulnerability:
        st.markdown("""
        <div class="empty-box">
            <h3>🛡️ Results will appear here</h3>
            <p>Paste Java code, click <b>Analyze & Secure</b>, and the fixed code will appear here.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    st.markdown("### 🚨 Vulnerability")

    if vulnerability:
        st.error(vulnerability)
    else:
        st.warning("No vulnerability information found.")

    tab_secure, tab_diff, tab_details = st.tabs(
        ["💬 Secure Code", "🔍 Diff", "📊 Details"]
    )

    with tab_secure:
        if stream:
            stream_code(secure_code)
        else:
            st.code(
                secure_code,
                language="java",
                height=360
            )

        st.download_button(
            label="📥 Download Secure Code",
            data=secure_code,
            file_name="SecureCode.java",
            mime="text/plain",
            use_container_width=True
        )

    with tab_diff:
        show_diff(original, secure_code)

    with tab_details:
        col_1, col_2, col_3 = st.columns(3)

        with col_1:
            st.metric("Original Length", len(original))

        with col_2:
            st.metric("Secure Length", len(secure_code))

        with col_3:
            original_lines = len(original.splitlines()) if original else 0
            secure_lines = len(secure_code.splitlines()) if secure_code else 0
            diff_count = abs(secure_lines - original_lines)
            st.metric("Line Difference", diff_count)


# -------------------------------------------------
# MAIN APP
# -------------------------------------------------
def main():
    sidebar()
    apply_theme()

    st.markdown(
        '<div class="main-title">🔐 Secure Java AI</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="sub-title">AI-powered Java vulnerability detection and secure code generation.</div>',
        unsafe_allow_html=True
    )

    left_col, right_col = st.columns([1.05, 0.95], gap="large")

    with left_col:
        with st.container(border=True):
            code_text = input_panel()

            st.divider()

            analyze_clicked = st.button(
                "🚀 Analyze & Secure",
                use_container_width=True
            )

    with right_col:
        with st.container(border=True):
            if analyze_clicked:
                if not code_text.strip():
                    st.warning("Please enter Java code first.")

                elif not is_java_code(code_text):
                    st.error("❌ This does not appear to be valid Java code.")
                    st.info(
                        "Please enter Java source code containing Java structure such as "
                        "`class`, `{}`, semicolons, Java methods, or imports."
                    )

                else:
                    with st.spinner("🔍 Loading model and analyzing your Java code..."):
                        tokenizer, model = load_model()
                        vulnerability, secure_code = generate_secure_code(
                            code_text,
                            tokenizer,
                            model
                        )

                    st.session_state.last_original = code_text
                    st.session_state.last_vulnerability = vulnerability
                    st.session_state.last_secure_code = secure_code
                    st.session_state.history.append(code_text)

                    result_panel(stream=True)

            else:
                result_panel(stream=False)


# -------------------------------------------------
# RUN APP
# -------------------------------------------------
if __name__ == "__main__":
    main()