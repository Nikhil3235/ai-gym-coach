# AI Real-time GYM Coach
An ultra-premium, real-time AI-powered personal gym coach website and web application. It uses computer vision to analyze your posture, count repetitions, calculate biomechanical joint angles, and deliver instant corrective voice feedback in multiple languages (English, Hindi, Marathi).

The project contains a premium, startup-style landing page and a full-featured Streamlit Web Application integrated with MediaPipe, SQLite, and Groq AI.

---

## 🚀 Key Features

### 🌐 Premium Landing Page (`LandingPage/`)
* **3D Tilt Visuals:** Glassmorphic cards with responsive 3D cursor-tracking tilt effects (`data-tilt`).
* **Particle Canvas:** Floating background particles rendered in real-time via HTML5 Canvas.
* **Secure Web Demo Video:** An optimized, browser-compatible H.264 video player showcasing the AI coach in action (with disabled right-clicks and downloads for privacy protection).
* **Reveal Animations:** Staggered fade-up scroll animations for a premium startup feel.
* **Interactive Grid:** Beautiful showcase grids for supported exercises, technology stack, and testimonials.

### 🏋️‍♂️ Streamlit Web Application (`main_app/`)
* **👤 Secure Login:** Simple user registration and database-linked login wall.
* **🌐 Multilingual Voice Coach:** Proactive voice instructions in **English, Hindi, or Marathi** with live audio playback.
* **📐 Biomechanical Pose Analysis:** Captures 33 skeleton coordinates in real-time using **MediaPipe Pose** and calculates precise joint angles:
  * **Squats:** Knee angle, hip alignment, and squat depth status.
  * **Push-ups:** Elbow angle, body alignment, and hip position.
  * **Biceps Curls:** Elbow flexion angle, shoulder stability, and body swing detection.
  * **Shoulder Press:** Elbow extension, arm extension, and back arch tracking.
  * **Lunges:** Front knee angle, torso alignment, and balance tracking.
* **🔢 Automatic Rep & Set Counter:** Real-time state machines that detect complete repetitions and sets.
* **🤖 Proactive AI Feedback:** Integrates **Groq AI (LLM)** to generate custom corrective voice suggestions based on form errors.
* **📊 Workout History Dashboard:** Visualizes daily workout logs, total repetitions, completed sets, and average form quality score.

---

## 🛠️ Tech Stack
* **Frontend (Landing Page):** HTML5, CSS3 (Vanilla Glassmorphism), Vanilla JavaScript
* **Backend Framework:** Streamlit (Python Web Framework)
* **Real-time Streaming:** Streamlit WebRTC (WebRTC connection for webcam streams)
* **AI & Computer Vision:**
  * **MediaPipe Pose:** Real-time human body pose landmark tracking.
  * **OpenCV:** Frame resizing, transformation, and drawing vector skeletons.
  * **Groq AI (LLM):** LLM-powered adaptive coaching logic.
  * **gTTS (Google Text-to-Speech) / Pyttsx3:** Text-to-speech engine for reactive feedback.
* **Database:** SQLite3 (Local persistence database)

---

## 📁 Project Structure
```text
ai-gym-coach/
├── index.html                   # Root redirect to Landing Page
├── README.md                    # Project documentation
├── LandingPage/                 # Landing Page directory
│   ├── index.html               # Main landing page markup
│   ├── style.css                # Premium custom stylesheet
│   ├── script.js                # Particle systems & tilt effects
│   ├── fonts/                   # Averta and other premium fonts
│   ├── IMGs_add_your_own/       # Exercises icons and images
│   └── videos_add_your_own/     # Compressed H.264 demo video
└── main_app/                    # Streamlit Web Application
    ├── main.py                  # Streamlit main entry point
    ├── requirements.txt         # App python dependencies
    ├── packages.txt             # Linux system dependencies (apt-get)
    ├── data.db                  # SQLite database (auto-generated)
    ├── core/                    # Base exercise models and structure
    ├── detectors/               # Exercise-specific angle processors
    │   ├── squat.py, pushup.py, biceps_curl.py, lunges.py, shoulder_press.py
    ├── ml_models/               # MediaPipe landmark models
    ├── services/                # Business logic services
    │   ├── auth/                # Login and user verification
    │   ├── persistence/         # SQLite DB repository operations
    │   ├── coaching/            # LLM prompt, TTS generation & voice pipeline
    │   ├── tracking/            # Real-time state metrics syncing
    │   └── ui/                  # Custom CSS styles injection
    └── static/                  # Streamlit custom font and styles
```

---

## ⚙️ Installation & Local Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Nikhil3235/ai-gym-coach.git
cd ai-gym-coach
```

### 2. Run the Landing Page
Simply open the `index.html` file in any web browser to view the premium landing page locally, or open `LandingPage/index.html` directly.

### 3. Run the Streamlit Application
Navigate into the `main_app` directory:
```bash
cd main_app
```

#### Windows Setup:
```bash
# Setup virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the Streamlit App
streamlit run main.py
```

#### macOS/Linux Setup:
```bash
# Setup virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the Streamlit App
streamlit run main.py
```

### 4. Configure Secrets (For AI Voice Coaching)
Create a `.env` file in the `main_app` folder (or `.streamlit/secrets.toml`):
```env
GROQ_API_KEY="your_groq_api_key_here"
```

---

## 📝 Database Schema (SQLite)
The application automatically creates and manages a local `data.db` SQLite database with the following structure:

### `users` Table
Stores registered profiles:
* `id` (INTEGER, Primary Key)
* `username` (TEXT, Unique)
* `created_at` (TIMESTAMP)

### `exercises` Table
Logs workout history and stats:
* `id` (INTEGER, Primary Key)
* `user_id` (INTEGER, Foreign Key referencing `users(id)`)
* `exercise_name` (TEXT)
* `reps` (INTEGER)
* `sets` (INTEGER)
* `time` (INTEGER) - Workout duration in seconds
* `form_score` (INTEGER) - Form quality score (0 to 100%)
* `created_at` (TIMESTAMP)

---

## 📄 License
This project is for educational and portfolio demonstration purposes.

Developed with ❤️ by [Nikhil Mali](https://github.com/Nikhil3235)