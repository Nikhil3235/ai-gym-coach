import streamlit as st
import os
import time
from dotenv import load_dotenv
load_dotenv()
import pandas as pd
from services.auth.login_wall import render_login_wall
from services.state.session_defaults import initial_session_defaults
from services.config.workout_config import EXERCISE_OPTIONS, LANGUAGE_OPTIONS, PROMPT
from services.ui.style_loader import load_css, inject_local_font, inject_webrtc_styles, inject_voice_commands
from services.persistence.exercise_repository import init_db
from streamlit_webrtc import webrtc_streamer, WebRtcMode
from services.vision.exercise_video_processor import VideoProcessorClass
from services.tracking.metrics import sync_metrics_update
from services.persistence.exercise_repository import get_users_exercises
from groq import Groq
from services.coaching.llm import LLMCoach
from services.coaching.tts import TextToSpeech
from services.coaching.voice_pipeline import VoicePipeline, autoplay_audio

  
def main():
    st.set_page_config(
        page_icon="🏋️‍♀️",
        page_title="AI Real-time GYM Coach — NIKHIL MALI",
        initial_sidebar_state="expanded",
        layout="centered"
    )

    _APP_DIR = os.path.dirname(os.path.abspath(__file__))
    load_css(os.path.join(_APP_DIR, "static", "style.css"))
    inject_local_font(os.path.join(_APP_DIR, "static", "AdobeClean.otf"), "AdobeClean")
    inject_voice_commands()

    init_db()

    if not render_login_wall():
        return 

    initial_session_defaults()

    if "voice_pipeline" not in st.session_state:
        try:
            api_key = os.environ.get("GROQ_API_KEY", "")

            if not api_key and hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
                api_key = st.secrets["GROQ_API_KEY"]
            
            groq_client = Groq(api_key=api_key)
            llm_coach = LLMCoach(groq_client)
            tts = TextToSpeech()
            st.session_state.voice_pipeline = VoicePipeline(llm_coach, tts)
        except Exception as e:
            st.session_state.voice_pipeline = None

    workout_started = st.session_state.get("workout_started", False)
    
    with st.sidebar:
        st.title("🏋️‍♂️ NIKHIL's AI Coach")

        if st.session_state.username:
            st.caption(f"👤 Login as {st.session_state.username}")

        st.divider()

        coach_lang = st.selectbox(
            "🌐 Coach Language",
            options=list(LANGUAGE_OPTIONS.keys()),
            key="coach_language",
            help="Voice coach will speak in this language"
        )
        lang_config = LANGUAGE_OPTIONS[coach_lang]

        # Update LLM prompt and TTS language when language changes
        if st.session_state.voice_pipeline:
            st.session_state.voice_pipeline.llm.system_prompt = PROMPT + lang_config["prompt_suffix"]
            st.session_state.voice_pipeline.tts_lang = lang_config["tts_code"]

        st.subheader("Workout Plan")

        if not workout_started:
            plan_exercise = st.selectbox("Exercise", options=EXERCISE_OPTIONS, key="plan_exercise")

            plan_sets = st.number_input("Sets", min_value=0, max_value=50, key="plan_sets", step=1)

            plan_reps = st.number_input("Reps per Set", min_value=0, max_value=50, key="plan_reps", step=1)

            st.markdown("")

            start_session_button = st.button("Start Workout", width="stretch", key="start_session_button")

            if start_session_button:
                st.session_state.exercise_type = plan_exercise
                st.session_state.target_sets = int(plan_sets)
                st.session_state.reps_per_set = int(plan_reps)
                st.session_state.reps = 0
                st.session_state.workout_started = True
                st.session_state.set_cycle_started_at = time.time()
                st.session_state.last_saved_sets_completed = 0

                if st.session_state.voice_pipeline:
                    result = st.session_state.voice_pipeline.process_event(
                        event="workout_started",
                        exercise=plan_exercise,
                        metrics={}
                    )
                    
                    if result:
                        st.session_state.audio_to_play, st.session_state.coach_feedback = result

                st.session_state.last_notified_sets_completed = 0
                st.session_state.last_notified_workout_complete = False
                st.rerun()
        else:
            exercise = st.session_state.get("exercise_type")
            sets = st.session_state.get("target_sets")
            reps = st.session_state.get("reps_per_set")

            st.info(f"**{exercise}** -- {sets} Sets / {reps} Reps")

            end_session_button = st.button("End Workout", key="end_session_button", width="stretch")

            if end_session_button:
                st.session_state.workout_started = False
                
                if st.session_state.voice_pipeline:
                    result = st.session_state.voice_pipeline.process_event(
                        event="workout_completed",
                        exercise=exercise,
                        metrics={}
                    )
                    if result:
                        st.session_state.audio_to_play, st.session_state.coach_feedback = result

                st.rerun()

        if workout_started:
            st.divider()

            exercise = st.session_state.get("exercise_type")
            total_reps = st.session_state.get("reps")
            current_set_reps = st.session_state.get("current_set_reps")
            reps_per_set = st.session_state.get("reps_per_set")
            sets_completed = st.session_state.get("sets_completed")
            target_sets = st.session_state.get("target_sets")

            st.subheader("Progress")

            st.metric("Total Reps", f"{total_reps}")
            st.metric("Current Set Reps", f"{current_set_reps} / {reps_per_set}")
            st.metric("Sets Completed", f"{sets_completed} / {target_sets}")

            st.divider()

            if exercise == "Squats":
                st.subheader("Squat Metrics")
                st.metric("Knee Angle", f"{st.session_state.knee_angle}°")
                st.metric("Back Angle", f"{st.session_state.back_angle}°")
                st.metric("Depth Status", st.session_state.depth_status)

            elif exercise == "Push-ups":
                st.subheader("Push-up Metrics")
                st.metric("Elbow Angle", f"{st.session_state.elbow_angle}°")
                st.metric("Body Alignment", st.session_state.body_alignment)
                st.metric("Hip Position", st.session_state.hip_status)

            elif exercise == "Biceps Curls (Dumbbell)":
                st.subheader("Curl Metrics")
                st.metric("Elbow Angle", f"{st.session_state.elbow_angle}°")
                st.metric("Shoulder Stability", st.session_state.shoulder_status)
                st.metric("Swing Detection", st.session_state.swing_status)

            elif exercise == "Shoulder Press":
                st.subheader("Shoulder Press Metrics")
                st.metric("Elbow Angle", f"{st.session_state.elbow_angle}°")
                st.metric("Arm Extension", st.session_state.extension_status)
                st.metric("Back Arch", st.session_state.back_arch_status)

            elif exercise == "Lunges":
                st.subheader("Lunge Metrics")
                st.metric("Front Knee Angle", f"{st.session_state.front_knee_angle}°")
                st.metric("Torso Angle", f"{st.session_state.torso_angle}°")
                st.metric("Balance Status", st.session_state.balance_status)

    st.title("AI Real-time GYM Coach")
    st.markdown("#### Real-time pose detection with proactive AI voice coaching · Built by **NIKHIL MALI**")
 
    if st.session_state.get("audio_to_play"):
        autoplay_audio(st.session_state.audio_to_play)

    if st.session_state.get("coach_feedback"):
        st.markdown("")
        st.success(f"🤖 **Coach:** {st.session_state.coach_feedback}")

    if not workout_started:
        st.markdown(
            """
            <div style="
                border: 10px dashed #444;
                border-radius: 0px;
                padding: 48px 32px;
                text-align: center;
                color: #888;
                margin-top: 32px;
                margin-bottom: 32px;
            ">
                <h2 style="color:#ccc; margin-bottom:8px;">👈 Set your workout plan</h2>
                <p style="font-size:1.05rem;">
                    Choose your exercise, sets and reps in the sidebar,<br>
                    then click <strong>Start Workout</strong> to activate the camera and AI coach.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        context = webrtc_streamer(
            key="exercise-analysis",
            mode=WebRtcMode.SENDRECV,
            video_processor_factory=VideoProcessorClass,
            rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
            media_stream_constraints={
                "video": True,
                "audio": False
            },
            async_processing=True
        )

        sync_metrics_update(context)

        if context.state.playing:
            time.sleep(0.25)
            st.rerun()

        inject_webrtc_styles()

    st.divider()

    st.markdown("#### Workout History")

    user_id = st.session_state.get("user_id", 0)

    if isinstance(user_id, int):
        history_rows = get_users_exercises(user_id)

        arr = [
            {
                "Exercise": row['exercise_name'],
                "Reps": row['reps'],
                "Sets": row['sets'],
                "Time (sec)": row['time'],
                "Form Score (%)": row['form_score'] if 'form_score' in row.keys() else 100,
                "Date": row['created_at']
            }
            for row in history_rows
        ]

        df = pd.DataFrame(arr)

        if not df.empty:
            df["Date"] = pd.to_datetime(df["Date"]).dt.date
            agg_df = df.groupby(["Exercise", "Date"]).agg({
                "Reps": 'sum',
                "Sets": "sum",
                "Time (sec)": "sum",
                "Form Score (%)": "mean"
            }).reset_index()
            agg_df["Form Score (%)"] = agg_df["Form Score (%)"].round().astype(int)
            agg_df.index += 1
            st.table(agg_df, border="horizontal")
            
            # Form Quality Score progress chart
            st.markdown("#### 📈 Form Quality Tracker")
            selected_ex = st.session_state.get("plan_exercise") or "Squats"
            filtered_df = agg_df[agg_df["Exercise"] == selected_ex]
            if not filtered_df.empty:
                import plotly.graph_objects as go
                import plotly.express as px
                
                # 1. 2D Glowing Spline Line Chart
                df_sorted = filtered_df.sort_values(by="Date")
                fig_2d = go.Figure()
                fig_2d.add_trace(go.Scatter(
                    x=df_sorted["Date"],
                    y=df_sorted["Form Score (%)"],
                    mode='lines+markers',
                    line=dict(color='#f5a623', width=4, shape='spline'),
                    marker=dict(
                        size=10, 
                        color='#00d4ff',
                        symbol='circle',
                        line=dict(color='#f5a623', width=2)
                    ),
                    fill='tozeroy',
                    fillcolor='rgba(245, 166, 35, 0.06)',
                    hovertemplate='<b>Date</b>: %{x}<br><b>Accuracy</b>: %{y}%<extra></extra>'
                ))
                fig_2d.update_layout(
                    paper_bgcolor='rgba(10, 10, 15, 0.95)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=40, r=20, t=20, b=40),
                    xaxis=dict(
                        showgrid=True,
                        gridcolor='rgba(255,255,255,0.05)',
                        tickfont=dict(color='#888888', size=11, family='Inter, sans-serif'),
                        linecolor='rgba(255,255,255,0.1)'
                    ),
                    yaxis=dict(
                        showgrid=True,
                        gridcolor='rgba(255,255,255,0.05)',
                        tickfont=dict(color='#888888', size=11, family='Inter, sans-serif'),
                        range=[0, 105],
                        linecolor='rgba(255,255,255,0.1)'
                    ),
                    hoverlabel=dict(
                        bgcolor='#151520',
                        font_size=12,
                        font_family='Inter, sans-serif',
                        font_color='#e8e8e8',
                        bordercolor='#f5a623'
                    ),
                    showlegend=False,
                    height=300,
                )
                st.plotly_chart(fig_2d, use_container_width=True)
                
                # 2. 3D Performance Space Visualization
                st.markdown("#### 🛸 3D Performance Space")
                st.caption("Rotate, zoom, and explore your workout metrics in interactive 3D!")
                
                df_sorted["Date_str"] = df_sorted["Date"].astype(str)
                fig_3d = px.scatter_3d(
                    df_sorted,
                    x="Date_str",
                    y="Reps",
                    z="Form Score (%)",
                    color="Form Score (%)",
                    size="Sets",
                    color_continuous_scale=px.colors.sequential.Sunsetdark,
                    labels={"Date_str": "Date", "Reps": "Reps Completed", "Form Score (%)": "Form Score (%)"}
                )
                fig_3d.update_layout(
                    scene=dict(
                        xaxis=dict(backgroundcolor="rgba(10,10,15,0.95)", gridcolor="rgba(255,255,255,0.05)", title="Date"),
                        yaxis=dict(backgroundcolor="rgba(10,10,15,0.95)", gridcolor="rgba(255,255,255,0.05)", title="Reps"),
                        zaxis=dict(backgroundcolor="rgba(10,10,15,0.95)", gridcolor="rgba(255,255,255,0.05)", title="Form Score (%)", range=[0, 100])
                    ),
                    paper_bgcolor='rgba(10, 10, 15, 0.95)',
                    margin=dict(l=0, r=0, t=10, b=0),
                    height=400,
                )
                st.plotly_chart(fig_3d, use_container_width=True)
                
            else:
                st.info(f"No history found for {selected_ex} to generate a tracker chart.")
        else:
            st.info("No workout history found.")


if __name__ == "__main__":
    main()
    