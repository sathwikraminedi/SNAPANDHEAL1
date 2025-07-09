# SNAP & HEAL

A modern Flask web app that accepts either an injury image (real, not fake/AI-generated) or a text description, and uses OpenAI to generate crisp, actionable first aid guidelines in English or Hindi, always with a medical disclaimer.

## Features
- Upload an injury image (PNG, JPG, JPEG only) or enter a text description
- Enforces image-only upload (other file types are rejected with a clear error)
- Choose your language: English or Hindi
- Uses OpenAI GPT to generate first aid steps in the selected language
- Includes a strong, clear medical disclaimer in the correct language
- Clean, mobile-friendly UI with aligned controls

## Setup
1. Clone/download this repo and enter the folder.
2. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the project directory and add your OpenAI API key (required for the app to work):
   ```env
   OPENAI_API_KEY=sk-...
   ```
   - Replace `sk-...` with your actual OpenAI API key.
   - The app uses [python-dotenv](https://pypi.org/project/python-dotenv/) to load this key automatically when you run it.
   - **Do not commit your real .env file to public repositories.**
4. Run the app:
   ```bash
   python app.py
   ```
5. Open your browser to http://127.0.0.1:5000

## Security Notes
- `app.secret_key` is for Flask session security. It should be a random string and **must NOT be your OpenAI API key**.
- Your OpenAI API key is only used to communicate with OpenAI servers for guideline generation.

## Usage
- Enter an injury description and/or upload a real injury image (no fake/AI images; only PNG, JPG, JPEG).
- Select your preferred language (English or Hindi).
- Click **Get First Aid Guidelines** to receive actionable steps and a disclaimer.
- If a non-image file is uploaded, the app will show an error and not process it.

## Limitations
- The fake/AI image detector is a placeholder. For real use, integrate an AI-based detector.
- The app does not give real medical advice. Always consult a healthcare professional in emergencies.
- Currently, only English and Hindi are supported. More languages can be added easily.

## Credits
- Built with Flask, OpenAI GPT, and ❤️ for rapid first aid guidance.
