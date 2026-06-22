import os
import streamlit as st
import streamlit.components.v1 as components
import base64
 

def load_css(file_path):
    if os.path.exists(file_path):
        with open(file_path, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def inject_local_font(font_path, font_name):
    if not os.path.exists(font_path):
        return
    
    with open(font_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()

    ext = os.path.splitext(font_path)[1].lstrip(".")
    fmt = {"otf": "opentype"}.get(ext, ext)
    mime = {"otf": "font/otf"}.get(ext, f"font/{ext}")

    st.markdown(f"""
        <style>
        @font-face {{
            font-family: '{font_name}';
            src: url('data:{mime};base64,{encoded}') format('{fmt}');
            font-weight: 100 900;
            font-style: normal;
        }}
        </style>
    """, unsafe_allow_html=True)

def inject_webrtc_styles():
    _APP_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    font_path = os.path.join(_APP_DIR, "static", "AdobeClean.otf")
    
    if not os.path.exists(font_path):
        return

    with open(font_path, "rb") as font_file:
        encoded_font = base64.b64encode(font_file.read()).decode()

    components.html(
        f"""
        <script>
        (function patchWebRTCStyles() {{
            function injectIntoIframe(iframe) {{
                try {{
                    const doc = iframe.contentDocument || iframe.contentWindow.document;
                    if (!doc || !doc.head) return;
                    if (doc.head.querySelector('#webrtc-custom-styles')) return;
                    const style = doc.createElement('style');
                    style.id = 'webrtc-custom-styles';
                    style.textContent = `
                        @font-face {{
                            font-family: 'AdobeClean';
                            src: url('data:font/otf;base64,{encoded_font}') format('opentype');
                            font-weight: 100 900;
                            font-style: normal;
                        }}
                        .MuiButtonBase-root,
                        .MuiButton-root,
                        .MuiButton-contained,
                        .MuiButton-text {{
                            border-radius: 0 !important;
                            font-family: 'AdobeClean', sans-serif !important;
                            letter-spacing: 0.05em !important;
                        }}
                    `;
                    doc.head.appendChild(style);
                }} catch (e) {{
                    console.warn('[patcher] could not inject:', e);
                }}
            }}

            function findAndPatch() {{
                const parentDoc = window.parent.document;
                const iframes = parentDoc.querySelectorAll('iframe');
                iframes.forEach(iframe => {{
                    if (iframe.src && iframe.src.includes('webrtc')) {{
                        if (iframe.contentDocument && iframe.contentDocument.readyState === 'complete') {{
                            injectIntoIframe(iframe);
                        }} else {{
                            iframe.addEventListener('load', () => injectIntoIframe(iframe));
                        }}
                    }}
                }});
            }}

            findAndPatch();
        }})();
        </script>
        """,
        height=0,
    )


def inject_voice_commands():
    components.html(
        """
        <script>
        (function patchVoiceCommands() {
            const parentDoc = window.parent.document;
            if (parentDoc.getElementById('voice-commands-script')) return;

            const marker = parentDoc.createElement('div');
            marker.id = 'voice-commands-script';
            marker.style.display = 'none';
            parentDoc.body.appendChild(marker);

            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRecognition) {
                console.warn('[Voice Patcher] Speech recognition not supported.');
                return;
            }

            const recognition = new SpeechRecognition();
            recognition.continuous = true;
            recognition.interimResults = false;
            recognition.lang = 'en-US';

            recognition.onresult = function(event) {
                const lastResultIndex = event.results.length - 1;
                const command = event.results[lastResultIndex][0].transcript.trim().toLowerCase();
                console.log('[Voice Command Heard]:', command);

                if (command.includes('start') || command.includes('begin') || command.includes('shuru') || command.includes('chalu')) {
                    clickButtonByText('Start Workout');
                } else if (command.includes('end') || command.includes('finish') || command.includes('stop') || command.includes('ruko') || command.includes('band')) {
                    clickButtonByText('End Workout');
                }
            };

            function clickButtonByText(text) {
                const buttons = parentDoc.querySelectorAll('button');
                for (const btn of buttons) {
                    const btnText = btn.textContent || btn.innerText;
                    if (btnText && btnText.replace(/\s+/g, ' ').trim().toLowerCase() === text.toLowerCase()) {
                        console.log('[Voice Command] Clicking button:', text);
                        btn.click();
                        break;
                    }
                }
            }

            recognition.onend = function() {
                try {
                    recognition.start();
                } catch (e) {}
            };

            try {
                recognition.start();
                console.log('[Voice Patcher] Active and listening...');
            } catch (e) {
                console.error('[Voice Patcher] Error starting:', e);
            }
        })();
        </script>
        """,
        height=0,
    )
