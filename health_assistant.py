import streamlit as st
import httpx
import base64
import os
from langchain_openai import ChatOpenAI
from openai import OpenAI
from dotenv import load_dotenv

# ---------------- LOAD ENV ---------------- #
load_dotenv()
API_KEY = os.getenv("API_KEY") or st.secrets.get("API_KEY", "")

if not API_KEY:
    st.error("⚠️ API key not found. Please set API_KEY in your .env file or Streamlit secrets.")
    st.stop()

# ---------------- PAGE CONFIG ---------------- #
st.set_page_config(page_title="AI Health Assistant", page_icon="🩺")
st.title("🩺 AI Health Assistant")

# ---------------- LLM SETUP ---------------- #
http_client = httpx.Client(verify=False)

llm = ChatOpenAI(
    base_url="https://genailab.tcs.in",
    model="azure/genailab-maas-gpt-4o",
    api_key=API_KEY,
    http_client=http_client
)

vision_client = OpenAI(
    base_url="https://genailab.tcs.in",
    api_key=API_KEY,
    http_client=http_client
)

# ---------------- CONVERSATION STEPS ---------------- #
STEPS = [
    {
        "key": "name",
        "question": "Hello! I'm your AI Health Assistant 🩺\n\nWhat's your **full name**? *(required)*",
        "type": "text",
        "placeholder": "e.g. Rahul Sharma",
        "required": True,
        "validate": lambda v: (
            "Name cannot be empty." if not v.strip() else
            "Name must be at least 2 characters." if len(v.strip()) < 2 else
            "Name should only contain letters and spaces." if not all(c.isalpha() or c.isspace() for c in v.strip()) else None
        )
    },
    {
        "key": "age",
        "question": "How old are you? *(required, 1–120)*",
        "type": "number",
        "min": 1, "max": 120,
        "required": True,
        "validate": lambda v: "Please enter a valid age between 1 and 120." if not (1 <= int(float(v)) <= 120) else None
    },
    {
        "key": "weight",
        "question": "What is your current weight in kilograms? *(required, 1–500)*",
        "type": "float",
        "min": 1.0, "max": 500.0,
        "required": True,
        "validate": lambda v: "Please enter a valid weight between 1 and 500 kg." if not (1.0 <= float(v) <= 500.0) else None
    },
    {
        "key": "blood_group",
        "question": "What is your blood group?",
        "type": "select",
        "options": ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-", "Don't know"],
        "required": False
    },
    {
        "key": "gender",
        "question": "What is your gender?",
        "type": "select",
        "options": ["Male", "Female", "Other", "Prefer not to say"],
        "required": False
    },
    {
        "key": "med_history_dropdown",
        "question": "Do you have any known medical conditions? *(Select all that apply)*",
        "type": "multiselect",
        "options": ["Diabetes", "Hypertension", "Asthma", "Heart Disease", "Thyroid", "None"],
        "required": False
    },
    {
        "key": "med_history_text",
        "question": "Can you describe your medical history in more detail?\n*(Type your history or click Skip)*",
        "type": "textarea",
        "placeholder": "e.g. Diagnosed with Type 2 Diabetes in 2019...",
        "required": False
    },
    {
        "key": "symptoms",
        "question": "What symptoms are you experiencing right now? *(required)*",
        "type": "textarea",
        "placeholder": "e.g. Fever for 2 days, headache, mild chest pain...",
        "required": True,
        "validate": lambda v: (
            "Please describe your symptoms before continuing." if not v.strip() else
            "Please provide more detail (at least 5 characters)." if len(v.strip()) < 5 else None
        )
    },
    {
        "key": "medical_images",
        "question": "You can optionally upload medical images for AI analysis 📷\n*(X-rays, skin conditions, lab reports, prescriptions — JPG, PNG, WEBP)*\n\nClick **Skip** if you have none.",
        "type": "image_upload",
        "required": False
    },
    {
        "key": "consult_doctor",
        "question": "Would you like to consult a doctor based on this analysis?",
        "type": "select",
        "options": ["Yes", "No"],
        "required": False
    },
]

# ---------------- SESSION STATE ---------------- #
defaults = {
    "chat_history": [],
    "current_step": 0,
    "patient_data": {},
    "analysis_done": False,
    "feedback_done": False,
    "uploaded_images": [],
    "image_step_done": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------------- HELPERS ---------------- #
def get_question(idx):
    q = STEPS[idx]["question"]
    if idx == 1 and "name" in st.session_state.patient_data:
        q = f"Nice to meet you, **{st.session_state.patient_data['name']}**! 😊\n\n" + q
    return q

def add_to_chat(role, msg):
    st.session_state.chat_history.append({"role": role, "content": msg})

def validate_field(step, value):
    if step.get("required") and (value is None or str(value).strip() == ""):
        return "⚠️ This field is required."
    if "validate" in step and value is not None:
        return step["validate"](str(value))
    return None

def encode_image(f):
    f.seek(0)
    return base64.b64encode(f.read()).decode("utf-8")

def advance(step_key, display_val, store_val=None):
    add_to_chat("user", display_val)
    st.session_state.patient_data[step_key] = store_val if store_val is not None else display_val
    st.session_state.current_step += 1
    nxt = st.session_state.current_step
    if nxt < len(STEPS):
        add_to_chat("assistant", get_question(nxt))
    st.rerun()

# ---------------- IMAGE RELEVANCE CHECK ---------------- #
def check_images_relevance(images):
    content = [
        {
            "type": "text",
            "text": """You are a strict medical image gatekeeper.

Look at the uploaded image(s) carefully.

Determine if EACH image is medically relevant — meaning it could be:
- An X-ray, MRI, CT scan, ultrasound
- A photo of a skin condition, rash, wound, swelling, or body part showing symptoms
- A lab report, prescription, medical document, or health test result
- A photo clearly showing a medical concern

If ALL images are medically relevant, respond ONLY with:
RELEVANT

If ANY image is NOT medically relevant (e.g. selfie, food, animal, nature, meme, random object, screenshot, etc.), respond ONLY with:
NOT_RELEVANT: <short friendly reason, max 1 sentence>

Do not explain further. Do not add anything else."""
        }
    ]
    for b64, mime in images:
        content.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}})

    try:
        resp = vision_client.chat.completions.create(
            model="azure/genailab-maas-gpt-4o",
            messages=[{"role": "user", "content": content}],
            max_tokens=100
        )
        result = resp.choices[0].message.content.strip()
        if result.startswith("NOT_RELEVANT"):
            reason = result.replace("NOT_RELEVANT:", "").strip()
            return False, reason
        return True, ""
    except Exception:
        return True, ""

# ---------------- IMAGE ANALYSIS ---------------- #
def analyze_images(images, d):
    content = [{
        "type": "text",
        "text": f"""You are a medical AI assistant. Analyze these medical image(s).

Patient context:
- Name: {d.get('name')}, Age: {d.get('age')}, Gender: {d.get('gender')}
- Symptoms: {d.get('symptoms')}
- Medical History: {d.get('med_history_dropdown')} — {d.get('med_history_text')}

Please:
1. Describe what you observe in the image(s)
2. Note any visible abnormalities or areas of concern
3. Relate findings to the patient's symptoms
4. Provide preliminary suggestions (NOT a diagnosis)
5. Strongly recommend professional medical review

Be empathetic, clear, and cautious. This is not a clinical diagnosis."""
    }]
    for b64, mime in images:
        content.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}})

    resp = vision_client.chat.completions.create(
        model="azure/genailab-maas-gpt-4o",
        messages=[{"role": "user", "content": content}],
        max_tokens=1000
    )
    return resp.choices[0].message.content

# ---------------- TEXT RELEVANCE CHECK ---------------- #
def check_text_relevance(field_key, value):
    prompts = {
        "symptoms": f"""A user typed this as their symptoms in a health assistant app: "{value}"

Is this a genuine health-related symptom description?
Valid: fever, pain, cough, fatigue, rash, nausea, etc.
Invalid: jokes, random words, unrelated text like "hello", "pizza", "test 123", politics, sports, etc.

Reply ONLY with:
RELEVANT
or
NOT_RELEVANT: <one short sentence saying this doesn't look like a health symptom>""",

        "med_history_text": f"""A user typed this as their medical history: "{value}"

Is this a genuine medical history description or has the user typed something irrelevant?
Valid: disease names, treatments, surgeries, medications, health conditions.
Invalid: random text, jokes, unrelated topics.

Reply ONLY with:
RELEVANT
or
NOT_RELEVANT: <one short sentence>"""
    }

    if field_key not in prompts or not value.strip() or value.strip().lower() in ("skip", "(skipped)", "none", "na", "n/a", "-"):
        return True, ""

    try:
        resp = llm.invoke(prompts[field_key])
        result = resp.content.strip()
        if result.startswith("NOT_RELEVANT"):
            reason = result.replace("NOT_RELEVANT:", "").strip()
            return False, reason
        return True, ""
    except Exception:
        return True, ""

# ---------------- MAIN PROMPT ---------------- #
def build_prompt():
    d = st.session_state.patient_data
    img_note = "\n- Medical Images: analyzed separately." if st.session_state.get("image_step_done") and d.get("medical_images") != "None" else ""
    return f"""You are a safe, empathetic medical assistant AI. You do NOT provide final diagnoses.

Patient Details:
- Name: {d.get('name')}
- Age: {d.get('age')}
- Weight: {d.get('weight')} kg
- Blood Group: {d.get('blood_group')}
- Gender: {d.get('gender')}
- Medical History (conditions): {d.get('med_history_dropdown')}
- Medical History (details): {d.get('med_history_text')}
- Symptoms: {d.get('symptoms')}
- Wants doctor consultation: {d.get('consult_doctor')}{img_note}

Respond warmly and conversationally. Cover:
1. Brief empathetic acknowledgment by name
2. Top 3 possible conditions with reasoning
3. Risk level: Low / Medium / High with reason
4. Key observations
5. Practical suggestions
6. Whether to consult a doctor and why

Be clear, reassuring, and advise professional consultation for serious concerns."""

def reset_all():
    for k in defaults:
        if k in st.session_state:
            del st.session_state[k]
    st.rerun()

# ---------------- RENDER HISTORY ---------------- #
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"], avatar="🩺" if msg["role"] == "assistant" else "🧑"):
        st.markdown(msg["content"])

# ---------------- FIRST MESSAGE ---------------- #
if not st.session_state.chat_history and st.session_state.current_step == 0:
    add_to_chat("assistant", get_question(0))
    st.rerun()

# ---------------- ANALYSIS PHASE ---------------- #
if st.session_state.current_step >= len(STEPS) and not st.session_state.analysis_done:

    if st.session_state.uploaded_images:
        with st.chat_message("assistant", avatar="🩺"):
            with st.spinner("Analyzing your medical images..."):
                try:
                    result = analyze_images(st.session_state.uploaded_images, st.session_state.patient_data)
                    add_to_chat("assistant", f"**📷 Image Analysis:**\n\n{result}")
                except Exception as e:
                    add_to_chat("assistant", f"⚠️ Image analysis failed: {e}")
        st.session_state.uploaded_images = []
        st.rerun()

    with st.chat_message("assistant", avatar="🩺"):
        with st.spinner("Analyzing your health details..."):
            try:
                resp = llm.invoke(build_prompt())
                add_to_chat("assistant", f"**🧠 Health Analysis:**\n\n{resp.content}")
            except Exception as e:
                add_to_chat("assistant", f"⚠️ Analysis failed: {e}")

    st.session_state.analysis_done = True
    st.rerun()

# ---------------- FEEDBACK PHASE ---------------- #
if st.session_state.analysis_done and not st.session_state.feedback_done:
    if not any(m["content"] == "Was this analysis helpful?" for m in st.session_state.chat_history):
        add_to_chat("assistant", "Was this analysis helpful?")
        st.rerun()

    with st.chat_message("assistant", avatar="🩺"):
        feedback = st.radio("Feedback", ["Yes, very helpful!", "Partially helpful", "Not really"],
                            label_visibility="collapsed", key="feedback_radio")
        if st.button("Submit Feedback"):
            add_to_chat("user", feedback)
            name = st.session_state.patient_data.get("name", "")
            add_to_chat("assistant", f"Thank you for your feedback, **{name}**! 💙\n\nStay well and always consult a certified doctor for medical decisions.")
            st.session_state.feedback_done = True
            st.rerun()

# ---------------- INPUT PHASE ---------------- #
if st.session_state.current_step < len(STEPS) and not st.session_state.analysis_done:
    step = STEPS[st.session_state.current_step]
    step_key = step["key"]

    with st.chat_message("assistant", avatar="🩺"):

        if step["type"] == "text":
            val = st.text_input("Answer", key=f"inp_{step_key}",
                                placeholder=step.get("placeholder", ""), label_visibility="collapsed")
            if st.button("Send ➤", key=f"btn_{step_key}"):
                err = validate_field(step, val)
                if err: st.error(err)
                else: advance(step_key, val.strip())

        elif step["type"] == "number":
            val = st.number_input("Answer", min_value=step["min"], max_value=step["max"],
                                  step=1, key=f"inp_{step_key}", label_visibility="collapsed")
            if st.button("Send ➤", key=f"btn_{step_key}"):
                err = validate_field(step, val)
                if err: st.error(err)
                else: advance(step_key, str(int(val)), int(val))

        elif step["type"] == "float":
            val = st.number_input("Answer", min_value=step["min"], max_value=step["max"],
                                  step=0.1, format="%.1f", key=f"inp_{step_key}", label_visibility="collapsed")
            if st.button("Send ➤", key=f"btn_{step_key}"):
                err = validate_field(step, val)
                if err: st.error(err)
                else: advance(step_key, f"{val:.1f} kg", float(val))

        elif step["type"] == "select":
            val = st.selectbox("Answer", step["options"], key=f"inp_{step_key}", label_visibility="collapsed")
            if st.button("Send ➤", key=f"btn_{step_key}"):
                advance(step_key, val)

        elif step["type"] == "multiselect":
            val = st.multiselect("Answer", step["options"], key=f"inp_{step_key}", label_visibility="collapsed")
            if st.button("Send ➤", key=f"btn_{step_key}"):
                selected = val if val else ["None"]
                advance(step_key, ", ".join(selected))

        elif step["type"] == "textarea":
            val = st.text_area("Answer", key=f"inp_{step_key}",
                               placeholder=step.get("placeholder", ""), label_visibility="collapsed")
            c1, c2, _ = st.columns([1, 1, 4])
            send = c1.button("Send ➤", key=f"btn_{step_key}")
            skip = c2.button("Skip", key=f"skip_{step_key}") if not step.get("required") else False
            if send:
                err = validate_field(step, val)
                if err:
                    st.error(err)
                else:
                    if step_key in ("symptoms", "med_history_text") and val.strip():
                        with st.spinner("Checking your input..."):
                            is_rel, reason = check_text_relevance(step_key, val)
                        if not is_rel:
                            st.error(
                                f"⚠️ **This doesn't look like a health-related response.**\n\n"
                                f"{reason}\n\n"
                                f"Please describe your actual {step_key.replace('_', ' ')} to continue."
                            )
                        else:
                            advance(step_key, val.strip())
                    else:
                        advance(step_key, val.strip())
            if skip:
                advance(step_key, "(skipped)", "")

        elif step["type"] == "image_upload":
            if not st.session_state.image_step_done:
                uploaded = st.file_uploader(
                    "Upload images",
                    type=["jpg", "jpeg", "png", "webp", "bmp"],
                    accept_multiple_files=True,
                    key="image_uploader",
                    label_visibility="collapsed"
                )
                if uploaded:
                    st.caption(f"📎 {len(uploaded)} image(s) selected")
                    cols = st.columns(min(len(uploaded), 3))
                    for i, f in enumerate(uploaded):
                        cols[i % 3].image(f, use_container_width=True, caption=f.name)

                c1, c2, _ = st.columns([1, 1, 4])
                upload_btn = c1.button("Upload ➤", key="img_upload_btn")
                skip_btn   = c2.button("Skip",     key="img_skip_btn")

                if upload_btn:
                    if not uploaded:
                        st.error("Please select at least one image, or click Skip.")
                    else:
                        imgs = [(encode_image(f), f.type or "image/jpeg") for f in uploaded]
                        with st.spinner("Checking if images are medically relevant..."):
                            is_rel, reason = check_images_relevance(imgs)
                        if not is_rel:
                            st.error(
                                f"⚠️ **This doesn't appear to be a medical image.**\n\n"
                                f"{reason}\n\n"
                                f"Please upload a medically relevant image such as an X-ray, skin condition photo, "
                                f"lab report, or prescription. Or click **Skip** to proceed without an image."
                            )
                        else:
                            st.session_state.uploaded_images = imgs
                            st.session_state.image_step_done = True
                            add_to_chat("user", f"📷 {len(uploaded)} medical image(s) uploaded for analysis")
                            st.session_state.patient_data[step_key] = f"{len(uploaded)} image(s)"
                            st.session_state.current_step += 1
                            nxt = st.session_state.current_step
                            if nxt < len(STEPS):
                                add_to_chat("assistant", get_question(nxt))
                            st.rerun()

                if skip_btn:
                    st.session_state.uploaded_images = []
                    st.session_state.image_step_done = True
                    add_to_chat("user", "No images uploaded")
                    st.session_state.patient_data[step_key] = "None"
                    st.session_state.current_step += 1
                    nxt = st.session_state.current_step
                    if nxt < len(STEPS):
                        add_to_chat("assistant", get_question(nxt))
                    st.rerun()

# ---------------- RESET ---------------- #
if st.session_state.feedback_done:
    st.divider()
    if st.button("🔄 Start New Consultation"):
        reset_all()
