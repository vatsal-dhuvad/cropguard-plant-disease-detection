import json
import os
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from .models import CustomUser, DiseaseDetection, UserStatistics, UserActivity
from .ml_model import predictor
from .email_service import send_welcome_email
from PIL import Image
import base64
import io
import logging
import threading
import requests

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def register(request):
    """Register new user with email validation"""
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        
        if not email or not password:
            return JsonResponse({'error': 'Email and password are required'}, status=400)
        
        # Check if user already exists
        if CustomUser.objects.filter(email=email).exists():
            return JsonResponse({'error': 'User with this email already exists'}, status=400)
        
        # Validate email before creating user
        from .email_service import validate_email
        is_valid, error_msg = validate_email(email)
        
        if not is_valid:
            return JsonResponse({
                'error': 'Invalid email address',
                'details': error_msg,
                'message': 'Please enter a valid email address that can receive emails.'
            }, status=400)
        
        # Create new user
        user = CustomUser.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # Automatically log in the user after registration
        login(request, user)
        
        # Record registration activity
        UserActivity.objects.create(
            user=user,
            activity_type='register',
            description=f"User registered with email {user.email}"
        )
        
        # Send welcome email in a separate thread
        email_thread = threading.Thread(target=send_welcome_email, args=(user.first_name or user.email, user.email))
        email_thread.start()
        
        return JsonResponse({
            'message': 'User registered successfully',
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
        })
        
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return JsonResponse({'error': 'Registration failed'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def login_view(request):
    """Login user with email-based authentication"""
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return JsonResponse({'error': 'Email and password are required'}, status=400)
        
        # Authenticate user
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            
            # Record login activity
            UserActivity.objects.create(
                user=user,
                activity_type='login',
                description=f"User logged in"
            )
            
            return JsonResponse({
                'message': 'Login successful',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name
                }
            })
        else:
            return JsonResponse({'error': 'Invalid credentials'}, status=401)
            
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return JsonResponse({'error': 'Login failed'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def logout_view(request):
    """Logout user"""
    try:
        logout(request)
        return JsonResponse({'message': 'Logout successful'})
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return JsonResponse({'error': 'Logout failed'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def detect_disease(request):
    """Detect disease in uploaded image using ML model"""
    try:
        # Temporarily disable authentication for testing
        # if not request.user.is_authenticated:
        #     return JsonResponse({'error': 'Authentication required'}, status=401)
        
        data = json.loads(request.body)
        image_data = data.get('image')
        
        if not image_data:
            return JsonResponse({'error': 'Image data is required'}, status=400)
        
        # Decode base64 image
        try:
            # Remove data URL prefix if present
            if image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
        except Exception as e:
            logger.error(f"Image decoding error: {str(e)}")
            return JsonResponse({'error': 'Invalid image format'}, status=400)
        
        # Make prediction using ML model
        try:
            prediction_result = predictor.predict(image)
        except Exception as e:
            logger.error(f"Detection backend unavailable: {str(e)}")
            return JsonResponse({'error': 'Model service unavailable. Please start the Flask service.'}, status=503)
        
        # Save detection to database (if user is authenticated)
        detection = None
        leaf_problem = prediction_result.get('problem') or prediction_result['disease']
        if request.user.is_authenticated:
            detection = DiseaseDetection.objects.create(
                user=request.user,
                prediction=f"Leaf problem - {leaf_problem}",
                confidence=prediction_result['confidence']
            )
            
            # Update user statistics
            stats, created = UserStatistics.objects.get_or_create(user=request.user)
            stats.update_statistics(prediction_result)
            
            # Record activity
            UserActivity.objects.create(
                user=request.user,
                activity_type='detection',
                description=f"Detected leaf problem: {leaf_problem}",
                crop='Leaf problem',
                disease=leaf_problem,
                confidence=prediction_result['confidence']
            )
        
        response_data = {
            'message': 'Disease detection completed',
            'detection': {
                'crop': 'Leaf',
                'disease': leaf_problem,
                'problem': leaf_problem,
                'confidence': prediction_result['confidence'],
                'is_healthy': prediction_result['is_healthy'],
                'treatment': prediction_result['treatment'],
                'description': prediction_result.get('description', ''),
                'duration': prediction_result.get('duration', ''),
                'prevention': prediction_result.get('prevention', ''),
                'class_name': leaf_problem,
            }
        }
        
        if detection:
            response_data['detection']['id'] = detection.id
            response_data['detection']['timestamp'] = detection.timestamp.isoformat()
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Disease detection error: {str(e)}")
        return JsonResponse({'error': 'Disease detection failed'}, status=500)

## Live camera endpoint removed

@csrf_exempt
@require_http_methods(["POST"])
def detect_live_proxy(request):
    """Proxy live camera detection to Flask to avoid CORS in frontend."""
    try:
        data = json.loads(request.body)
        image_data = data.get('image')
        if not image_data:
            return JsonResponse({'error': 'Image data is required'}, status=400)

        flask_service_url = os.getenv('FLASK_SERVICE_URL', 'http://localhost:5000')
        resp = requests.post(f'{flask_service_url}/predict-live', json={'image': image_data}, timeout=15)
        content_type = resp.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            return JsonResponse(resp.json(), status=resp.status_code, safe=False)
        else:
            logger.error(f"Flask non-JSON response (status {resp.status_code}): {resp.text[:300]}")
            return JsonResponse({'error': 'Flask returned non-JSON response', 'details': resp.text[:200]}, status=resp.status_code)
    except requests.exceptions.RequestException as e:
        logger.error(f"Proxy error to Flask: {str(e)}")
        return JsonResponse({'error': 'Model service unavailable. Please start the Flask service.'}, status=503)
    except Exception as e:
        logger.error(f"Live proxy error: {str(e)}")
        return JsonResponse({'error': 'Live detection failed'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def detect_upload_proxy(request):
    """Proxy multipart upload to Flask /predict to avoid CORS."""
    try:
        upload = request.FILES.get('file')
        if not upload:
            return JsonResponse({'error': 'No file part'}, status=400)
        files = {'file': (getattr(upload, 'name', 'image.jpg'), upload.read(), getattr(upload, 'content_type', 'image/jpeg'))}
        flask_service_url = os.getenv('FLASK_SERVICE_URL', 'http://localhost:5000')
        resp = requests.post(f'{flask_service_url}/predict', files=files, timeout=20)
        content_type = resp.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            return JsonResponse(resp.json(), status=resp.status_code, safe=False)
        else:
            logger.error(f"Flask non-JSON response (status {resp.status_code}): {resp.text[:300]}")
            return JsonResponse({'error': 'Flask returned non-JSON response', 'details': resp.text[:200]}, status=resp.status_code)
    except requests.exceptions.RequestException as e:
        logger.error(f"Proxy upload error to Flask: {str(e)}")
        return JsonResponse({'error': 'Model service unavailable. Please start the Flask service.'}, status=503)
    except Exception as e:
        logger.error(f"Upload proxy error: {str(e)}")
        return JsonResponse({'error': 'Live detection failed'}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def detection_history(request):
    """Get user's detection history and statistics"""
    try:
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        # Get detection history
        detections = DiseaseDetection.objects.filter(user=request.user).order_by('-timestamp')
        
        history = []
        for detection in detections:
            # Parse prediction to extract the leaf problem. Older rows may
            # contain crop names, but the UI should focus on the problem only.
            prediction_parts = detection.prediction.split(' - ', 1)
            crop = 'Leaf'
            disease = prediction_parts[1] if len(prediction_parts) > 1 else 'Unknown'
            
            history.append({
                'id': detection.id,
                'crop': crop,
                'disease': disease,
                'problem': disease,
                'confidence': detection.confidence,
                'is_healthy': 'healthy' in disease.lower(),
                'treatment': 'Apply appropriate treatment based on disease type.',
                'timestamp': detection.timestamp.isoformat()
            })
        
        # Get user statistics
        stats, created = UserStatistics.objects.get_or_create(user=request.user)
        
        # Get recent activities
        activities = UserActivity.objects.filter(user=request.user).order_by('-timestamp')[:10]
        activity_timeline = []
        for activity in activities:
            activity_timeline.append({
                'id': activity.id,
                'type': activity.activity_type,
                'description': activity.description,
                'crop': 'Leaf' if activity.activity_type == 'detection' else activity.crop,
                'disease': activity.disease,
                'problem': activity.disease,
                'confidence': activity.confidence,
                'timestamp': activity.timestamp.isoformat()
            })
        
        return JsonResponse({
            'history': history,
            'statistics': {
                'total_scans': stats.total_scans,
                'diseased_plants': stats.diseased_plants,
                'healthy_plants': stats.healthy_plants,
                'last_updated': stats.last_updated.isoformat()
            },
            'activity_timeline': activity_timeline
        })
        
    except Exception as e:
        logger.error(f"History retrieval error: {str(e)}")
        return JsonResponse({'error': 'Failed to retrieve history'}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def user_info(request):
    """Get current user information"""
    try:
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        return JsonResponse({
            'user': {
                'id': request.user.id,
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name
            }
        })
        
    except Exception as e:
        logger.error(f"User info error: {str(e)}")
        return JsonResponse({'error': 'Failed to get user info'}, status=500)

def api_info(request):
    """Root API endpoint with available endpoints info"""
    return JsonResponse({
        'message': 'Crop Disease Detection API',
        'version': '1.0.0',
        'endpoints': {
            'register': '/api/register/',
            'login': '/api/login/',
            'logout': '/api/logout/',
            'detect': '/api/detect/',
            'history': '/api/history/',
            'user': '/api/user/'
        },
        'status': 'running'
    }) 
