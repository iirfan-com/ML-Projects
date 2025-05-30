import os
import streamlit as st
from PIL import Image
import pytesseract
from gtts import gTTS
from langdetect import detect, DetectorFactory
import base64
from translate import Translator

# Set up language detection
DetectorFactory.seed = 0

# Configure Tesseract path (adjust for your system)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Language mapping
language_mapping = {
    'en': {'tesseract': 'eng', 'gtts': 'en', 'name': 'English'},
    'hi': {'tesseract': 'hin', 'gtts': 'hi', 'name': 'Hindi'},
    'ta': {'tesseract': 'tam', 'gtts': 'ta', 'name': 'Tamil'},
    'ml': {'tesseract': 'mal', 'gtts': 'ml', 'name': 'Malayalam'},
    'bn': {'tesseract': 'ben', 'gtts': 'bn', 'name': 'Bengali'},
    'fr': {'tesseract': 'fra', 'gtts': 'fr', 'name': 'French'},
    'de': {'tesseract': 'deu', 'gtts': 'de', 'name': 'German'},
    'es': {'tesseract': 'spa', 'gtts': 'es', 'name': 'Spanish'},
    'ar': {'tesseract': 'ara', 'gtts': 'ar', 'name': 'Arabic'},
    'kn': {'tesseract': 'kan', 'gtts': 'kn', 'name': 'Kannada'},
    'te': {'tesseract': 'tel', 'gtts': 'te', 'name': 'Telugu'},
    'pa': {'tesseract': 'pan', 'gtts': 'pa', 'name': 'Punjabi'},
}

# Supported languages for translation (using language codes from the 'translate' library)
translation_languages = {
    'en': 'English',
    'hi': 'Hindi',
    'ta': 'Tamil',
    'ml': 'Malayalam',
    'bn': 'Bengali',
    'fr': 'French',
    'de': 'German',
    'es': 'Spanish',
    'ar': 'Arabic',
    'ja': 'Japanese',
    'ko': 'Korean',
    'zh': 'Chinese',
    'ru': 'Russian',
    'pt': 'Portuguese',
    'it': 'Italian'
}

def detect_text_language(text):
    try:
        lang_code = detect(text)
        st.write(f"Detected language code: {lang_code}")
        
        # Handle similar languages
        if lang_code == 'mr':  # Marathi
            lang_code = 'hi'
        elif lang_code == 'ur':  # Urdu
            lang_code = 'hi'

        return language_mapping.get(lang_code)
    except Exception as e:
        st.error(f"Language detection failed: {e}")
        return None

def text_to_speech(text, lang_code, filename='output.mp3'):
    try:
        tts = gTTS(text=text, lang=lang_code)
        tts.save(filename)
        return filename
    except Exception as e:
        st.error(f"Error in text-to-speech conversion: {e}")
        return None

def autoplay_audio(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio controls autoplay="true">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(
            md,
            unsafe_allow_html=True,
        )

def translate_text(text, dest_lang='en'):
    try:
        translator = Translator(to_lang=dest_lang)
        translation = translator.translate(text)
        return translation
    except Exception as e:
        st.error(f"Translation failed: {e}")
        return None

def process_image(image, manual_lang=None):
    try:
        # Try OCR with default languages first
        default_langs = '+'.join(['eng', 'hin', 'mal', 'tam', 'ben'])
        initial_text = pytesseract.image_to_string(image, lang=default_langs)

        if not initial_text.strip():
            st.warning("No text could be extracted with default OCR.")
            return None, None, None

        # Detect language or use manual selection
        if manual_lang:
            lang_info = language_mapping.get(manual_lang)
            st.write(f"Using manually selected language: {lang_info['name']}")
        else:
            lang_info = detect_text_language(initial_text)
            if lang_info:
                st.write(f"Automatically detected language: {lang_info['name']}")
            else:
                st.warning("Could not detect language automatically. Using English as fallback.")
                lang_info = language_mapping.get('en')

        # Perform OCR with the selected language
        extracted_text = pytesseract.image_to_string(image, lang=lang_info['tesseract'])

        if not extracted_text.strip():
            st.warning("No text found after using detected language.")
            return None, None, None

        return extracted_text, lang_info['gtts'], lang_info['name']

    except Exception as e:
        st.error(f"An error occurred during image processing: {str(e)}")
        return None, None, None

def main():
    st.title("OCR with Text-to-Speech and Translation")
    st.markdown("""
    Upload an image containing text, and this app will:
    1. Extract the text using OCR
    2. Detect the language (or use your selection)
    3. Convert the text to speech
    4. Optionally translate to another language
    """)

    # File uploader
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

    # Manual language selection
    manual_mode = st.checkbox("Manually select source language")
    if manual_mode:
        lang_options = {code: info['name'] for code, info in language_mapping.items()}
        selected_lang = st.selectbox(
            "Select source language",
            options=list(lang_options.keys()),
            format_func=lambda x: lang_options[x]
        )
    else:
        selected_lang = None

    # Translation options
    translate = st.checkbox("Enable translation")
    if translate:
        # Get all supported translation languages
        dest_lang = st.selectbox(
            "Select target language for translation",
            options=list(translation_languages.keys()),
            format_func=lambda x: f"{x} - {translation_languages[x]}"
        )

    if uploaded_file is not None:
        # Display the uploaded image
        image = Image.open(uploaded_file)
        st.image(image, caption='Uploaded Image', use_container_width=True)

        # Process the image when button is clicked
        if st.button("Extract Text and Convert to Speech"):
            with st.spinner("Processing image..."):
                extracted_text, lang_code, source_lang_name = process_image(image, selected_lang)

            if extracted_text and lang_code:
                st.subheader("Extracted Text")
                st.text_area("OCR Output", extracted_text, height=200)

                # Translation section
                if translate:
                    with st.spinner("Translating text..."):
                        translated_text = translate_text(extracted_text, dest_lang)
                    
                    if translated_text:
                        st.subheader("Translated Text")
                        st.text_area(f"Translation to {translation_languages[dest_lang]}", 
                                   translated_text, height=200)
                        
                        # Generate TTS for translated text
                        with st.spinner("Converting translated text to speech..."):
                            translated_audio = text_to_speech(translated_text, dest_lang, 'translated_output.mp3')
                        
                        if translated_audio:
                            st.success(f"Translated to {translation_languages[dest_lang]}! Here's the audio:")
                            autoplay_audio(translated_audio)
                            
                            with open(translated_audio, "rb") as f:
                                st.download_button(
                                    label="Download Translated Audio",
                                    data=f,
                                    file_name="translated_audio.mp3",
                                    mime="audio/mp3"
                                )

                # Original text TTS
                with st.spinner("Converting to speech..."):
                    audio_file = text_to_speech(extracted_text, lang_code)
                
                if audio_file:
                    st.success(f"Original {source_lang_name} audio:")
                    autoplay_audio(audio_file)
                    
                    # Download button for the original audio file
                    with open(audio_file, "rb") as f:
                        st.download_button(
                            label="Download Original Audio",
                            data=f,
                            file_name="original_audio.mp3",
                            mime="audio/mp3"
                        )

if __name__ == "__main__":
    main()