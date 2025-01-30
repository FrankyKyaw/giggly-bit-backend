from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import torch
from src.laughter_detection import detect_laughter
from src import laughter_detection_models as models
import logging

# Create Flask app
app = Flask(__name__)

# CORS Configuration (allow specific origins in production)
allowed_origins = os.environ.get("CORS_ALLOWED_ORIGINS", "*").split(",")
CORS(app, resources={r"/*": {"origins": allowed_origins}})
print(f"Configured origins: {allowed_origins}")  

# Environment Variables for Configuration
MODEL_CKPT_PATH = os.environ.get("MODEL_CKPT_PATH", './model_checkpoints/best.pth.tar')
TEMP_AUDIO_PATH = os.environ.get("TEMP_AUDIO_PATH", 'temp_audio.wav')

# Device Configuration
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize model
try:
    logger.info("Loading laughter detection model...")
    model = models.ResNetBigger(
        dropout_rate=0.0,
        linear_layer_size=128,
        filter_sizes=[128, 64, 32, 32],
    )
    model.load_state_dict(torch.load(MODEL_CKPT_PATH, map_location='cpu')['state_dict'])
    model.to(DEVICE)
    model.eval()
    logger.info("Model loaded successfully.")
except Exception as e:
    logger.error(f"Error loading model: {e}")
    raise

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        logger.warning("No file part in request.")
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        logger.warning("No file selected in request.")
        return jsonify({'error': 'No selected file'}), 400

    # Save the uploaded file temporarily
    try:
        file.save(TEMP_AUDIO_PATH)
        logger.info(f"File saved temporarily at {TEMP_AUDIO_PATH}.")
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        return jsonify({'error': 'Failed to save file'}), 500

    try:
        # Detect laughter
        laughter_detected = detect_laughter(TEMP_AUDIO_PATH, model)
        result = "Laughter detected!" if laughter_detected else "No laughter detected"
        logger.info(f"Laughter detection result: {result}")
        return jsonify({'result': result})
    except Exception as e:
        logger.error(f"Error during laughter detection: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        # Clean up temporary file
        if os.path.exists(TEMP_AUDIO_PATH):
            os.remove(TEMP_AUDIO_PATH)
            logger.info(f"Temporary file {TEMP_AUDIO_PATH} removed.")

@app.route('/debug-cors')
def debug_cors():
    return {
        'CORS_ALLOWED_ORIGINS': os.environ.get('CORS_ALLOWED_ORIGINS', 'not set'),
        'parsed_origins': os.environ.get('CORS_ALLOWED_ORIGINS', '*').split(',')
    }
    
# The app is now ready to be served by a WSGI server (e.g., gunicorn, uWSGI).
