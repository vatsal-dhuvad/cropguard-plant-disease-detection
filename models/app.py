from flask import Flask, request, jsonify, render_template
try:
    from flask_cors import CORS
except ImportError:
    CORS = None
import tensorflow as tf
import numpy as np
from PIL import Image
import io
import os
import pandas as pd
import json
from tensorflow.keras.preprocessing.image import img_to_array
import base64

app = Flask(__name__, static_folder="static")
if CORS is not None:
    # Allow all origins for development to avoid CORS issues from different hostnames/IPs
    CORS(app, resources={r"/*": {"origins": "*"}})
else:
    # Fallback CORS: add headers manually if flask-cors isn't installed
    @app.after_request
    def add_cors_headers(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        return response

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------- LOAD MODEL ---------------- #
model = tf.keras.models.load_model(os.path.join(BASE_DIR, "trained_modelNew.h5"))

# ---------------- LOAD REMEDIES ---------------- #
remedy_csv = os.path.join(BASE_DIR, "Plant_Disease_Remedy_Updated3.csv")
if not os.path.exists(remedy_csv):
    remedy_csv = os.path.join(BASE_DIR, "Plant_Disease_Remedy_Updated.csv")
remedies_df = pd.read_csv(remedy_csv)
remedies_map = remedies_df.set_index("Disease").T.to_dict()

# ---------------- LOAD CLASS LABELS ---------------- #
with open(os.path.join(BASE_DIR, "class_labels.json")) as f:
    class_labels = json.load(f)

# ---------------- IMAGE PREPROCESSING ---------------- #
def preprocess_image(image_bytes):
    """Preprocess uploaded image just like Jupyter Notebook."""
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB").resize((128, 128))
    img_array = img_to_array(image)   # raw pixels (0–255) since model was trained that way
    return np.expand_dims(img_array, axis=0)

def preprocess_base64_image(base64_string):
    try:
        if base64_string.startswith('data:image'):
            base64_string = base64_string.split(',')[1]
        image_bytes = base64.b64decode(base64_string)
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB").resize((128, 128))
        img_array = img_to_array(image)
        return np.expand_dims(img_array, axis=0)
    except Exception as e:
        print(f"Error preprocessing base64 image: {e}")
        return None

# ---------------- ROUTES ---------------- #
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/predict", methods=["POST", "OPTIONS"])
def predict():
    try:
        if request.method == 'OPTIONS':
            return jsonify({"ok": True})
        if "file" not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files["file"]
        image_bytes = file.read()
        input_data = preprocess_image(image_bytes)

        prediction = model.predict(input_data)
        print("Raw prediction output:", prediction)
        print("Prediction shape:", prediction.shape)

        if prediction.shape[1] != len(class_labels):
            return jsonify({"error": "Prediction shape mismatch with class labels."})

        predicted_class_index = int(np.argmax(prediction))
        confidence = float(np.max(prediction))

        if predicted_class_index >= len(class_labels):
            return jsonify({"error": "Predicted index exceeds label count."})

        predicted_label = class_labels[predicted_class_index]
        remedy = remedies_map.get(predicted_label, {
            "Description": "No remedy info.",
            "Treatment": "N/A",
            "Duration": "N/A",
            "Prevention": "N/A"
        })

        # Confidence threshold handling
        if "healthy" in predicted_label.lower() and confidence < 0.6:
            return jsonify({
                "prediction": "Plant looks healthy",
                "confidence": round(confidence * 100, 2),
                "description": "Model prediction suggests the plant is likely healthy.",
                "treatment": "No treatment needed.",
                "duration": "N/A",
                "prevention": "Maintain regular plant care and monitoring."
            })

        if "healthy" not in predicted_label.lower() and confidence < 0.6:
            return jsonify({
                "prediction": "Uncertain — may be healthy",
                "confidence": round(confidence * 100, 2),
                "description": "Model isn't confident. The plant might be healthy.",
                "treatment": "No treatment unless symptoms appear.",
                "duration": "N/A",
                "prevention": "Observe the plant over time."
            })

        # Normal confident prediction
        return jsonify({
            "prediction": predicted_label,
            "confidence": round(confidence * 100, 2),
            "description": remedy.get("Description", ""),
            "treatment": remedy.get("Treatment", ""),
            "duration": remedy.get("Duration", ""),
            "prevention": remedy.get("Prevention", "")
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/predict-live", methods=["POST"])
def predict_live():
    try:
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({"error": "No image data provided"}), 400

        input_data = preprocess_base64_image(data['image'])
        if input_data is None:
            return jsonify({"error": "Invalid image format"}), 400

        prediction = model.predict(input_data)
        # Normalize to probabilities for stable confidence 0..1
        if prediction.ndim == 2:
            probs = tf.nn.softmax(prediction[0]).numpy()
        else:
            probs = tf.nn.softmax(prediction).numpy()

        if probs.shape[0] != len(class_labels):
            return jsonify({"error": "Prediction shape mismatch with class labels."})

        predicted_class_index = int(np.argmax(probs))
        confidence = float(np.max(probs))

        if predicted_class_index >= len(class_labels):
            return jsonify({"error": "Predicted index exceeds label count."})

        predicted_label = class_labels[predicted_class_index]
        remedy = remedies_map.get(predicted_label, {
            "Description": "No remedy info.",
            "Treatment": "N/A",
            "Duration": "N/A",
            "Prevention": "N/A"
        })

        return jsonify({
            "prediction": predicted_label,
            "confidence": round(confidence * 100, 2),
            "description": remedy.get("Description", ""),
            "treatment": remedy.get("Treatment", ""),
            "duration": remedy.get("Duration", ""),
            "prevention": remedy.get("Prevention", "")
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# JSON error handlers to avoid HTML responses
@app.errorhandler(404)
def handle_404(e):
    return jsonify({"error": "Not Found", "path": request.path}), 404

@app.errorhandler(405)
def handle_405(e):
    return jsonify({"error": "Method Not Allowed", "path": request.path}), 405

@app.errorhandler(500)
def handle_500(e):
    return jsonify({"error": "Internal Server Error"}), 500

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/diseases", methods=["GET"])
def get_all_diseases():
    """Get all disease information from the CSV file."""
    try:
        # Clean the DataFrame by replacing NaN values with 'N/A'
        cleaned_df = remedies_df.fillna('N/A')
        
        # Convert DataFrame to list of dictionaries for JSON serialization
        diseases_list = cleaned_df.to_dict('records')
        
        # Add some statistics
        total_diseases = len(diseases_list)
        healthy_plants = len([d for d in diseases_list if 'healthy' in d['Disease'].lower()])
        diseased_plants = total_diseases - healthy_plants
        
        return jsonify({
            "total_diseases": total_diseases,
            "healthy_plants": healthy_plants,
            "diseased_plants": diseased_plants,
            "diseases": diseases_list
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/diseases/<plant_type>", methods=["GET"])
def get_plant_diseases(plant_type):
    """Get diseases for a specific plant type."""
    try:
        # Filter diseases by plant type (case-insensitive)
        plant_diseases = remedies_df[remedies_df['Disease'].str.contains(plant_type, case=False, na=False)]
        
        if plant_diseases.empty:
            return jsonify({"error": f"No diseases found for plant type: {plant_type}"}), 404
        
        # Clean the filtered DataFrame by replacing NaN values with 'N/A'
        cleaned_plant_diseases = plant_diseases.fillna('N/A')
        diseases_list = cleaned_plant_diseases.to_dict('records')
        
        return jsonify({
            "plant_type": plant_type,
            "count": len(diseases_list),
            "diseases": diseases_list
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------- MAIN ---------------- #
if __name__ == "__main__":
    app.run(
        host=os.getenv("FLASK_HOST", "127.0.0.1"),
        port=int(os.getenv("FLASK_PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "False").lower() == "true",
        use_reloader=False,
    )
