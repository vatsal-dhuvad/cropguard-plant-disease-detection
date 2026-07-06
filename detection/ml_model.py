import numpy as np
import cv2
from PIL import Image
import os
from django.conf import settings
import logging
import requests
import base64
import io
import json

logger = logging.getLogger(__name__)

class CropDiseasePredictor:
    """
    Machine Learning Model Handler for Crop Disease Detection
    Uses Flask service for model predictions
    """
    
    def __init__(self, flask_service_url=None):
        """
        Initialize the ML model predictor
        
        Args:
            flask_service_url (str): URL of the Flask service
        """
        self.flask_service_url = flask_service_url or os.getenv("FLASK_SERVICE_URL", "http://localhost:5000")
        self.class_names = []
        self.remedies_map = {}
        self.load_class_labels()
        self.load_remedies()
        
        # Test connection to Flask service
        self.test_flask_connection()
    
    def test_flask_connection(self):
        """
        Test connection to Flask service
        """
        try:
            response = requests.get(f"{self.flask_service_url}/", timeout=5)
            if response.status_code == 200:
                logger.info(f"Flask service is running at {self.flask_service_url}")
            else:
                logger.warning(f"Flask service responded with status {response.status_code}")
        except Exception as e:
            logger.warning(f"Could not connect to Flask service at {self.flask_service_url}: {str(e)}")
    
    def load_class_labels(self):
        """
        Load class labels from JSON file
        """
        try:
            class_labels_path = os.path.join(settings.BASE_DIR, 'models', 'class_labels.json')
            if os.path.exists(class_labels_path):
                with open(class_labels_path, 'r') as f:
                    self.class_names = json.load(f)
                logger.info(f"Class labels loaded successfully from {class_labels_path}")
            else:
                logger.warning(f"Class labels file not found at {class_labels_path}")
                # Fallback to hardcoded labels
                self.class_names = [
                    'Apple___Apple_scab',
                    'Apple___Black_rot',
                    'Apple___Cedar_apple_rust',
                    'Apple___healthy',
                    'Blueberry___healthy',
                    'Cherry_(including_sour)___healthy',
                    'Cherry_(including_sour)___Powdery_mildew',
                    'Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot',
                    'Corn_(maize)___Common_rust',
                    'Corn_(maize)___healthy',
                    'Corn_(maize)___Northern_Leaf_Blight',
                    'Grape___Black_rot',
                    'Grape___Esca_(Black_Measles)',
                    'Grape___healthy',
                    'Grape___Leaf_blight_(Isariopsis_Leaf_Spot)',
                    'Orange___Haunglongbing_(Citrus_greening)',
                    'Peach___Bacterial_spot',
                    'Peach___healthy',
                    'Pepper,_bell___Bacterial_spot',
                    'Pepper,_bell___healthy',
                    'Potato___Early_blight',
                    'Potato___healthy',
                    'Potato___Late_blight',
                    'Raspberry___healthy',
                    'Soybean___healthy',
                    'Squash___Powdery_mildew',
                    'Strawberry___healthy',
                    'Strawberry___Leaf_scorch',
                    'Tomato___Bacterial_spot',
                    'Tomato___Early_blight',
                    'Tomato___healthy',
                    'Tomato___Late_blight',
                    'Tomato___Leaf_Mold',
                    'Tomato___Septoria_leaf_spot',
                    'Tomato___Spider_mites Two-spotted_spider_mite',
                    'Tomato___Target_Spot',
                    'Tomato___Tomato_mosaic_virus',
                    'Tomato___Tomato_Yellow_Leaf_Curl_Virus'
                ]
        except Exception as e:
            logger.error(f"Error loading class labels: {str(e)}")
            # Fallback to hardcoded labels
            self.class_names = [
                'Apple___Apple_scab',
                'Apple___Black_rot',
                'Apple___Cedar_apple_rust',
                'Apple___healthy',
                'Blueberry___healthy',
                'Cherry_(including_sour)___healthy',
                'Cherry_(including_sour)___Powdery_mildew',
                'Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot',
                'Corn_(maize)___Common_rust',
                'Corn_(maize)___healthy',
                'Corn_(maize)___Northern_Leaf_Blight',
                'Grape___Black_rot',
                'Grape___Esca_(Black_Measles)',
                'Grape___healthy',
                'Grape___Leaf_blight_(Isariopsis_Leaf_Spot)',
                'Orange___Haunglongbing_(Citrus_greening)',
                'Peach___Bacterial_spot',
                'Peach___healthy',
                'Pepper,_bell___Bacterial_spot',
                'Pepper,_bell___healthy',
                'Potato___Early_blight',
                'Potato___healthy',
                'Potato___Late_blight',
                'Raspberry___healthy',
                'Soybean___healthy',
                'Squash___Powdery_mildew',
                'Strawberry___healthy',
                'Strawberry___Leaf_scorch',
                'Tomato___Bacterial_spot',
                'Tomato___Early_blight',
                'Tomato___healthy',
                'Tomato___Late_blight',
                'Tomato___Leaf_Mold',
                'Tomato___Septoria_leaf_spot',
                'Tomato___Spider_mites Two-spotted_spider_mite',
                'Tomato___Target_Spot',
                'Tomato___Tomato_mosaic_virus',
                'Tomato___Tomato_Yellow_Leaf_Curl_Virus'
            ]
    
    def load_remedies(self):
        """
        Load remedies from CSV file
        """
        try:
            remedies_path = os.path.join(settings.BASE_DIR, 'models', 'Plant_Disease_Remedy_Updated.csv')
            if os.path.exists(remedies_path):
                import pandas as pd
                # Use proper CSV parsing with quote handling and error handling
                remedies_df = pd.read_csv(remedies_path, quoting=1, on_bad_lines='skip')  # QUOTE_ALL
                self.remedies_map = remedies_df.set_index("Disease").T.to_dict()
                logger.info(f"Remedies loaded successfully from {remedies_path}")
            else:
                logger.warning(f"Remedies file not found at {remedies_path}")
                self.remedies_map = {}
        except Exception as e:
            logger.error(f"Error loading remedies: {str(e)}")
            # Fallback: create a simple remedies map
            self.remedies_map = {}
    
    def preprocess_image(self, image):
        """
        Preprocess image for model prediction
        
        Args:
            image: PIL Image or numpy array
            
        Returns:
            bytes: Image bytes for Flask service
        """
        try:
            # Convert to PIL Image if it's not already
            if isinstance(image, np.ndarray):
                image = Image.fromarray(image)
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize image to standard size (128x128 as expected by the model)
            image = image.resize((128, 128))
            
            # Convert to bytes for Flask service
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG')
            img_byte_arr = img_byte_arr.getvalue()
            
            return img_byte_arr
            
        except Exception as e:
            logger.error(f"Error preprocessing image: {str(e)}")
            raise
    
    def predict(self, image):
        """
        Predict crop disease from image using Flask service
        
        Args:
            image: PIL Image or numpy array
            
        Returns:
            dict: Prediction results with class, confidence, and treatment
        """
        try:
            # Preprocess image
            image_bytes = self.preprocess_image(image)
            
            # Prepare data for Flask service
            files = {'file': ('image.jpg', image_bytes, 'image/jpeg')}
            
            # Call Flask service
            response = requests.post(f"{self.flask_service_url}/predict", files=files, timeout=30)
            
            if response.status_code == 200:
                # Parse Flask service response
                flask_result = response.json()
                
                # Extract prediction data
                predicted_label = flask_result.get('prediction', 'Unknown')
                confidence = flask_result.get('confidence', 0.0)
                description = flask_result.get('description', '')
                treatment = flask_result.get('treatment', '')
                duration = flask_result.get('duration', '')
                prevention = flask_result.get('prevention', '')
                
                # Parse crop and disease from class name
                if '___' in predicted_label:
                    crop, disease = predicted_label.split('___', 1)
                else:
                    crop = "Unknown"
                    disease = predicted_label
                
                # Determine if healthy or diseased
                is_healthy = 'healthy' in disease.lower()
                
                return {
                    'crop': crop,
                    'disease': disease,
                    'confidence': confidence,
                    'is_healthy': is_healthy,
                    'treatment': treatment,
                    'description': description,
                    'duration': duration,
                    'prevention': prevention,
                    'class_id': -1,  # Not needed for Flask service
                    'class_name': predicted_label
                }
            else:
                logger.error(f"Flask service error: {response.status_code} - {response.text}")
                raise RuntimeError("Flask model service error. Please ensure Flask (DM.h5) is running.")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Flask service: {str(e)}")
            raise RuntimeError("Flask model service unavailable. Please start Flask (DM.h5).")
        except Exception as e:
            logger.error(f"Error making prediction: {str(e)}")
            raise
    
    # Live prediction method removed
    
    def _get_dummy_prediction(self):
        """
        Get dummy prediction when Flask service is not available
        """
        import random
        
        # Random selection for testing
        class_name = random.choice(self.class_names)
        
        if '___' in class_name:
            crop, disease = class_name.split('___', 1)
        else:
            crop = "Unknown"
            disease = class_name
        
        is_healthy = 'healthy' in disease.lower()
        confidence = random.uniform(0.7, 0.95) if is_healthy else random.uniform(0.8, 0.98)
        
        # Get treatment from remedies map or fallback
        treatment_info = self._get_treatment_suggestion(crop, disease, is_healthy, class_name)
        
        return {
            'crop': crop,
            'disease': disease,
            'confidence': round(confidence * 100, 2),
            'is_healthy': is_healthy,
            'treatment': treatment_info.get('treatment', ''),
            'description': treatment_info.get('description', ''),
            'duration': treatment_info.get('duration', ''),
            'prevention': treatment_info.get('prevention', ''),
            'class_id': -1,
            'class_name': class_name
        }
    
    def _get_treatment_suggestion(self, crop, disease, is_healthy, class_name):
        """
        Get treatment suggestions based on crop and disease
        
        Args:
            crop (str): Crop name
            disease (str): Disease name
            is_healthy (bool): Whether the plant is healthy
            class_name (str): Full class name from model
            
        Returns:
            dict: Treatment information
        """
        if is_healthy:
            return {
                'treatment': f"Your {crop} plant appears to be healthy! Continue with regular care and monitoring.",
                'description': f"The model detected that your {crop} plant is healthy.",
                'duration': 'N/A',
                'prevention': 'Maintain regular plant care and monitoring.'
            }
        
        # Try to get remedy from CSV file first
        if class_name in self.remedies_map:
            remedy = self.remedies_map[class_name]
            return {
                'treatment': remedy.get('Treatment / Remedies', ''),
                'description': remedy.get('Description', ''),
                'duration': remedy.get('Duration', ''),
                'prevention': remedy.get('Prevention', '')
            }
        
        # Fallback to hardcoded treatments
        treatments = {
            'Apple': {
                'Apple_scab': 'Apply fungicides containing captan, myclobutanil, or thiophanate-methyl. Remove and destroy infected leaves and fruit. Maintain good air circulation by pruning.',
                'Black_rot': 'Prune and destroy infected branches. Apply fungicides containing captan or thiophanate-methyl. Remove all infected fruit and leaves.',
                'Cedar_apple_rust': 'Remove cedar trees within 2 miles if possible. Apply fungicides containing myclobutanil or triadimefon during spring.',
                'default': 'Apply appropriate fungicides and maintain good orchard hygiene.'
            },
            'Corn_(maize)': {
                'Cercospora_leaf_spot Gray_leaf_spot': 'Apply fungicides containing azoxystrobin, pyraclostrobin, or trifloxystrobin. Rotate crops and remove infected plant debris.',
                'Common_rust': 'Apply fungicides and plant resistant varieties. Remove crop debris.',
                'Northern_Leaf_Blight': 'Apply fungicides and use resistant hybrids. Rotate crops.',
                'default': 'Apply appropriate fungicides and maintain field hygiene.'
            },
            'Grape': {
                'Black_rot': 'Apply fungicides and remove infected berries. Maintain good air circulation.',
                'Esca_(Black_Measles)': 'Prune infected vines and apply fungicides. Maintain vineyard hygiene and proper vine training.',
                'Leaf_blight_(Isariopsis_Leaf_Spot)': 'Apply fungicides and remove infected leaves. Maintain good air flow.',
                'default': 'Apply appropriate fungicides and maintain vineyard hygiene.'
            },
            'Potato': {
                'Early_blight': 'Apply fungicides containing chlorothalonil, mancozeb, or azoxystrobin. Rotate crops and remove infected leaves.',
                'Late_blight': 'Apply fungicides immediately. Remove infected plants and avoid overhead irrigation.',
                'default': 'Apply appropriate fungicides and maintain field hygiene.'
            },
            'Tomato': {
                'Bacterial_spot': 'Apply copper-based bactericides. Remove infected plants and avoid overhead irrigation.',
                'Early_blight': 'Apply fungicides and remove infected leaves. Maintain good air circulation.',
                'Late_blight': 'Apply fungicides immediately. Remove infected plants and avoid overhead irrigation.',
                'Leaf_Mold': 'Apply fungicides and maintain good air circulation. Avoid overhead irrigation.',
                'Septoria_leaf_spot': 'Apply fungicides and remove infected leaves. Maintain good air circulation.',
                'Spider_mites Two-spotted_spider_mite': 'Apply miticides and maintain proper humidity. Remove heavily infested plants.',
                'Target_Spot': 'Apply fungicides and remove infected leaves. Maintain good air circulation.',
                'Tomato_mosaic_virus': 'Remove infected plants. Control aphid vectors with insecticides.',
                'Tomato_Yellow_Leaf_Curl_Virus': 'Control whitefly populations with insecticides. Remove infected plants.',
                'default': 'Apply appropriate fungicides and maintain good plant hygiene.'
            },
            'Peach': {
                'Bacterial_spot': 'Apply copper-based bactericides. Prune infected branches and maintain orchard hygiene.',
                'default': 'Apply appropriate bactericides and maintain orchard hygiene.'
            },
            'Pepper,_bell': {
                'Bacterial_spot': 'Apply copper-based bactericides. Remove infected plants and avoid overhead irrigation.',
                'default': 'Apply appropriate bactericides and maintain field hygiene.'
            },
            'Cherry_(including_sour)': {
                'Powdery_mildew': 'Apply fungicides containing myclobutanil, trifloxystrobin, or sulfur. Prune infected branches and maintain good air circulation.',
                'default': 'Apply appropriate fungicides and maintain orchard hygiene.'
            },
            'Strawberry': {
                'Leaf_scorch': 'Apply fungicides and remove infected leaves. Maintain good air circulation.',
                'default': 'Apply appropriate fungicides and maintain field hygiene.'
            }
        }
        
        # Get treatment for specific crop and disease
        if crop in treatments:
            crop_treatments = treatments[crop]
            if disease in crop_treatments:
                treatment = crop_treatments[disease]
            else:
                treatment = crop_treatments.get('default', f'Apply appropriate fungicides for {crop} {disease}.')
        else:
            treatment = f'Apply appropriate fungicides for {crop} {disease}. Consult with a local agricultural expert.'
        
        return {
            'treatment': treatment,
            'description': f'Detected {disease} on {crop} plant.',
            'duration': '7-14 days',
            'prevention': 'Maintain good plant hygiene and monitor regularly.'
        }

# Global instance for easy access
predictor = CropDiseasePredictor() 
