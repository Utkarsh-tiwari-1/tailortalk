import streamlit as st
import requests
from datetime import datetime
import time

st.set_page_config(page_title="TailorTalk Chatbot", page_icon="🤖", layout="wide")

# --- THEME & MODE TOGGLE ---
if "dark_mode" not in st.session_state:
    st.session_state["dark_mode"] = True

def get_theme():
    return {
        "background": "#181c24" if st.session_state["dark_mode"] else "#f5f6fa",
        "card": "rgba(24,28,36,0.7)" if st.session_state["dark_mode"] else "rgba(255,255,255,0.7)",
        "bubble_user": "linear-gradient(90deg, #3a8dde 0%, #6dd5ed 100%)" if st.session_state["dark_mode"] else "#e3f2fd",
        "bubble_bot": "#23272f" if st.session_state["dark_mode"] else "#e0e0e0",
        "text_user": "#fff" if st.session_state["dark_mode"] else "#222",
        "text_bot": "#e0e0e0" if st.session_state["dark_mode"] else "#222",
        "sidebar_bg": "#15181e" if st.session_state["dark_mode"] else "#fff",
        "sidebar_text": "#fff" if st.session_state["dark_mode"] else "#222",
    }

THEME = get_theme()

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png", width=80)
    st.title("TailorTalk")
    st.markdown("""
    **AI Booking Assistant**
    
    Book and manage your Google Calendar appointments via chat.
    
    [Open Google Calendar](https://calendar.google.com)
    """)
    st.markdown("---")
    st.markdown("**User:** <span style='color:#3a8dde'>Guest</span>", unsafe_allow_html=True)
    st.markdown("---")
    mode = st.toggle("🌗 Dark mode", value=st.session_state["dark_mode"])
    st.session_state["dark_mode"] = mode
    st.markdown("Made with ❤️ using FastAPI, LangChain, and Streamlit.")
    st.markdown("<small>v1.0</small>", unsafe_allow_html=True)

# --- PWA MANIFEST ---
st.markdown(
    """
    <link rel=\"manifest\" href=\"/manifest.json\">
    <meta name=\"theme-color\" content=\"#3a8dde\">
    """,
    unsafe_allow_html=True,
)

# --- GLASSMORPHIC CHAT CARD ---
st.markdown(f"""
    <style>
    body {{ background: {THEME['background']} !important; }}
    .chat-card {{
        background: {THEME['card']};
        border-radius: 24px;
        padding: 2.5rem 2rem 1.5rem 2rem;
        max-width: 650px;
        margin: 2rem auto 1rem auto;
        box-shadow: 0 8px 32px 0 #00000033;
        backdrop-filter: blur(8px);
        border: 1.5px solid rgba(255,255,255,0.08);
    }}
    .chat-bubble-user {{
        background: {THEME['bubble_user']};
        color: {THEME['text_user']};
        border-radius: 16px 16px 4px 16px;
        padding: 0.8rem 1.2rem;
        margin-bottom: 0.5rem;
        align-self: flex-end;
        max-width: 80%;
        box-shadow: 0 2px 8px #0002;
        font-size: 1.08rem;
        animation: fadeIn 0.4s;
    }}
    .chat-bubble-bot {{
        background: {THEME['bubble_bot']};
        color: {THEME['text_bot']};
        border-radius: 16px 16px 16px 4px;
        padding: 0.8rem 1.2rem;
        margin-bottom: 0.5rem;
        align-self: flex-start;
        max-width: 80%;
        box-shadow: 0 2px 8px #0002;
        font-size: 1.08rem;
        animation: fadeIn 0.4s;
    }}
    .chat-avatar {{
        width: 36px; height: 36px; border-radius: 50%; display: inline-block; vertical-align: middle; margin-right: 0.5rem;
        border: 2px solid #3a8dde; box-shadow: 0 0 0 2px #fff2;
    }}
    .chat-row {{ display: flex; align-items: flex-end; margin-bottom: 0.2rem; }}
    .chat-row.user {{ justify-content: flex-end; }}
    .chat-row.bot {{ justify-content: flex-start; }}
    .timestamp {{ font-size: 0.75rem; color: #888; margin: 0 0.5rem; }}
    .input-row {{ display: flex; gap: 0.5rem; }}
    .send-btn {{ background: linear-gradient(90deg, #3a8dde 0%, #6dd5ed 100%); color: white; border: none; border-radius: 8px; padding: 0.6rem 1.5rem; font-weight: bold; cursor: pointer; transition: 0.2s; }}
    .send-btn:hover {{ background: linear-gradient(90deg, #6dd5ed 0%, #3a8dde 100%); }}
    .clear-btn {{ background: #23272f; color: #e0e0e0; border: none; border-radius: 8px; padding: 0.5rem 1.2rem; margin-left: 0.5rem; cursor: pointer; }}
    @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: none; }} }}
    .typing-indicator {{ color: #3a8dde; font-style: italic; margin: 0.5rem 0 0.5rem 2.5rem; }}
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="chat-card">', unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "loading" not in st.session_state:
    st.session_state["loading"] = False
if "show_typing" not in st.session_state:
    st.session_state["show_typing"] = False

# --- CLEAR CHAT BUTTON ---
col1, col2 = st.columns([1, 5])
with col1:
    if st.button("🗑️ Clear chat", key="clear"):
        st.session_state["messages"] = []
        st.rerun()

# --- CHAT HISTORY ---
for msg in st.session_state["messages"]:
    timestamp = msg.get("timestamp") or datetime.now().strftime("%I:%M %p")
    if msg["role"] == "user":
        st.markdown(f'<div class="chat-row user"><div class="chat-bubble-user">'
                    f'<img src="https://cdn-icons-png.flaticon.com/512/3135/3135715.png" class="chat-avatar">'
                    f'{msg["content"]}<span class="timestamp">{timestamp}</span></div></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chat-row bot"><div class="chat-bubble-bot">'
                    f'<img src="https://cdn-icons-png.flaticon.com/512/4712/4712035.png" class="chat-avatar">'
                    f'{msg["content"]}<span class="timestamp">{timestamp}</span></div></div>', unsafe_allow_html=True)

st.write("")  # Add vertical space

# --- TYPING INDICATOR ---
if st.session_state.get("show_typing"):
    st.markdown('<div class="typing-indicator">TailorTalk is typing...</div>', unsafe_allow_html=True)
    time.sleep(1)

# --- MULTILINE INPUT AREA ---
with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_area(
        "Type your message",
        "",
        key="user_input",
        placeholder="Type your message and press Enter...",
        label_visibility="collapsed",
        height=68,
        max_chars=500,
    )
    submitted = st.form_submit_button("Send", use_container_width=True)
    if submitted and user_input.strip():
        st.session_state["messages"].append({"role": "user", "content": user_input, "timestamp": datetime.now().strftime("%I:%M %p")})
        st.session_state["loading"] = True
        st.session_state["show_typing"] = True
        st.rerun()

# --- LOADING SPINNER AND BACKEND CALL ---
if st.session_state.get("loading") and st.session_state["messages"] and st.session_state["messages"][-1]["role"] == "user":
    with st.spinner("TailorTalk is thinking..."):
        try:
            response = requests.post(
                "https://tailortalk-backend-xxxx.onrender.com/chat",
                json={"message": st.session_state["messages"][-1]["content"]},
                timeout=30
            )
            if response.status_code == 200:
                bot_reply = response.json().get("response") or response.json().get("error", "(No response)")
            else:
                bot_reply = f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            bot_reply = f"Error: {e}"
        st.session_state["show_typing"] = False
        st.session_state["messages"].append({"role": "bot", "content": bot_reply, "timestamp": datetime.now().strftime("%I:%M %p")})
        st.session_state["loading"] = False
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True) 
