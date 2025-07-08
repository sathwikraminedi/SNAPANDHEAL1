import os
import json
import traceback
import httpx
from dotenv import load_dotenv
from flask import Flask, render_template, request, url_for, flash, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from openai import OpenAI
import requests  # still used only for disabling SSL warnings

# --- BEGIN: Disable SSL verification for requests (for debugging only!) ---
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# --- END: Disable SSL verification ---

app = Flask(__name__)
app.secret_key = 'b4c2c6a6e1c74b7e9f6f7b7a8e2f1d7c5a9b3c4d6e7f8a1b2c3d4e5f6a7b8c9d'  # Use a secure random secret key

# Load environment variables from .env file
load_dotenv()
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

# Initialize OpenAI client with SSL verification disabled (for dev only)
client = OpenAI(
    api_key=OPENAI_API_KEY,
    http_client=httpx.Client(verify=False)
)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Dummy function to discourage fake/AI-generated images (replace with real model as needed)
def is_fake_image(image_path):
    # For demonstration, always returns False (not fake)
    # Integrate with a real detector for production
    return False


def generate_guidelines(user_input, language="en"):
    """
    Given a prompt (user_input) and a language code, fetches first aid guidelines from the OpenAI API.
    Removes any disclaimer from the response and formats the output for HTML display.
    """
    # These are just standard disclaimers. You can edit them if you want.
    english_disclaimer = (
        "Disclaimer: This information is for general guidance only and is not a substitute for professional medical advice. "
        "In case of emergency, call your local emergency number or consult a healthcare professional immediately."
    )
    hindi_disclaimer = (
        "अस्वीकरण: यह जानकारी केवल सामान्य मार्गदर्शन के लिए है और यह पेशेवर चिकित्सा सलाह का विकल्प नहीं है। "
        "आपातकाल की स्थिति में अपने स्थानीय आपातकालीन नंबर पर कॉल करें या तुरंत किसी स्वास्थ्य विशेषज्ञ से संपर्क करें।"
    )
    # Choose the right disclaimer for the language
    disclaimer_text = english_disclaimer if language == "en" else hindi_disclaimer
    debug_notes = []  # We'll collect debug notes here for transparency

    try:
        # Set up the system prompt and user prompt based on the language
        if language == "hi":
            sys_prompt = (
                "Imagine you are a friendly medical assistant. Please write clear, practical first aid steps in Hindi. "
                "Be concise and always add the disclaimer at the end, in Hindi."
            )
            user_msg = user_input + "\n" + hindi_disclaimer
        else:
            sys_prompt = (
                "Imagine you are a friendly medical assistant. Please write clear, practical first aid steps in English. "
                "Be concise and always add the disclaimer at the end."
            )
            user_msg = user_input + "\n" + english_disclaimer

        debug_notes.append("[DEBUG] About to contact OpenAI for guidelines...")

        # Actually make the API call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_msg}
            ],
            max_tokens=400,
            temperature=0.5,
        )
        debug_notes.append(f"[DEBUG] OpenAI API raw response: {response}")
        result_text = response.choices[0].message.content

        # Remove any disclaimer text, just in case
        import re
        patterns = [
            r"Disclaimer: This information is for general guidance only and is not a substitute for professional medical advice\. In case of emergency, call your local emergency number or consult a healthcare professional immediately\.?",
            r"अस्वीकरण: यह जानकारी केवल सामान्य मार्गदर्शन के लिए है और यह पेशेवर चिकित्सा सलाह का विकल्प नहीं है। आपातकाल की स्थिति में अपने स्थानीय आपातकालीन नंबर पर कॉल करें या तुरंत किसी स्वास्थ्य विशेषज्ञ से संपर्क करें।"
        ]
        for pattern in patterns:
            result_text = re.sub(pattern, "", result_text, flags=re.IGNORECASE)

        # Format the output for HTML display
        def make_guidelines_html(raw_text):
            import html
            txt = html.escape(raw_text)
            # Numbered list to <ol>
            txt = re.sub(r'(?m)^\s*\d+\.\s+', r'</li><li>', txt)
            txt = re.sub(r'(</li><li>)+', '</li><li>', txt)
            if '</li><li>' in txt:
                txt = '<ol>' + txt.replace('</li><li>', '<li>', 1) + '</li></ol>'
            # Bullet list to <ul>
            txt = re.sub(r'(?m)^\s*[\-\*•]\s+', r'</li><li>', txt)
            if '</li><li>' in txt:
                txt = '<ul>' + txt.replace('</li><li>', '<li>', 1) + '</li></ul>'
            # Paragraph breaks
            txt = txt.replace('\n', '<br>')
            return txt.strip()

        html_guidelines = make_guidelines_html(result_text.strip())
        return html_guidelines, "<br>".join(debug_notes)

    except Exception as exc:
        debug_notes.append(f"[ERROR] Could not get guidelines: {str(exc)}")
        import traceback
        debug_notes.append(traceback.format_exc().replace("\n", "<br>"))
        return None, "<br>".join(debug_notes)


@app.route('/', methods=['GET', 'POST'])
def index():
    guidelines = None
    error = None
    debug_info = None
    language = request.form.get('language', 'en') if request.method == 'POST' else 'en'
    text_input = ''
    uploaded_image_url = None

    if request.method == 'POST':
        text_input = request.form.get('injury_text', '').strip()
        file = request.files.get('injury_image')

        if file and file.filename:
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                uploaded_image_url = url_for('uploaded_file', filename=filename)

                # Check for fake image
                if is_fake_image(filepath):
                    error = "Uploaded image appears to be AI-generated or fake. Please upload a real injury photo."
                else:
                    # Optionally: Use image captioning to generate prompt (not implemented here)
                    prompt = "This is an image of an injury. Please provide first aid guidelines for such cases."
                    guidelines, debug_info = generate_guidelines(prompt, language)
            else:
                error = "Only image files (png, jpg, jpeg) are allowed. Please upload a valid image."

        elif text_input:
            guidelines, debug_info = generate_guidelines(text_input, language)

        else:
            error = "Please provide either an injury image or a text description."

    return render_template(
        'index.html',
        guidelines=guidelines,
        error=error,
        language=language,
        injury_text=text_input,
        uploaded_image_url=uploaded_image_url,
        debug_info=debug_info
    )


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    app.run(debug=True)
