import streamlit as st
from services.persistence.exercise_repository import get_or_create_user


def render_login_wall():
    if st.session_state.get("user_id") is not None:
        return True
    
    st.title("🏋️‍♂️ AI Real-time GYM Coach")
    st.markdown("### Welcome! Please enter a username to start.")
    st.markdown("""
    <style>
    @keyframes shiny-slide {
        0%   { background-position: -200% center; }
        100% { background-position: 200% center; }
    }
    .shiny-credit {
        font-size: 0.85rem;
        font-weight: 600;
        letter-spacing: 2px;
        text-transform: uppercase;
        background: linear-gradient(
            90deg,
            #b97a18 0%,
            #f5a623 20%,
            #ffd06b 35%,
            #fff8e7 50%,
            #ffd06b 65%,
            #f5a623 80%,
            #b97a18 100%
        );
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: shiny-slide 3s linear infinite;
        margin-top: -8px;
        padding: 4px 0;
        text-shadow: 0 0 20px rgba(245,166,35,0.3);
    }
    </style>
    <p class="shiny-credit">✦ Built by NIKHIL MALI — Powered by MediaPipe & Groq AI ✦</p>
    """, unsafe_allow_html=True)

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Name (unique)", placeholder="unique name e.g. nikhil_mali")
        submit_button = st.form_submit_button("Start Session", width="stretch")

    if submit_button:
        if not username:
            st.error("Name cannot be empty.")
            return False
        
        user = get_or_create_user(username)
    
        st.session_state["user_id"] = user["id"]
        st.session_state["username"] = user["username"]

        st.rerun()

    return False