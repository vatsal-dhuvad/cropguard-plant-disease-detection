// Global variables
let mediaStream = null;
let capturedImageBlob = null;

// DOM elements
const resultDiv = document.getElementById("result");
const loadingDiv = document.getElementById("loading");
const video = document.getElementById("camera");
const canvas = document.getElementById("canvas");
const startCameraBtn = document.getElementById("start-camera-btn");
const stopCameraBtn = document.getElementById("stop-camera-btn");
const captureBtn = document.getElementById("capture-btn");
const retakeBtn = document.getElementById("retake-btn");
const analyzeCapturedBtn = document.getElementById("analyze-captured-btn");
const newPhotoBtn = document.getElementById("new-photo-btn");
const capturedPreview = document.getElementById("captured-preview");
const previewImage = document.getElementById("preview-image");

// ---------------- FILE UPLOAD FUNCTIONALITY ---------------- #
document.getElementById("upload-form").addEventListener("submit", async function(e) {
  e.preventDefault();
  await analyzeImageFile();
});

async function analyzeImageFile() {
  const fileInput = document.getElementById("file-input");
  const file = fileInput.files[0];
  
  if (!file) {
    showError("Please select an image first.");
    return;
  }

  showLoading();
  
  try {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch("/predict", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    hideLoading();

    if (data.error) {
      showError(data.error);
      return;
    }

    displayResult(data);
  } catch (error) {
    hideLoading();
    showError("Prediction failed. Please try again.");
    console.error("JS Error:", error);
  }
}

// ---------------- CAMERA FUNCTIONALITY ---------------- #
startCameraBtn.addEventListener("click", startCamera);
stopCameraBtn.addEventListener("click", stopCamera);
captureBtn.addEventListener("click", capturePhoto);
retakeBtn.addEventListener("click", retakePhoto);
analyzeCapturedBtn.addEventListener("click", analyzeCapturedPhoto);
newPhotoBtn.addEventListener("click", newPhoto);

async function startCamera() {
  try {
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      mediaStream = await navigator.mediaDevices.getUserMedia({ 
        video: { 
          facingMode: 'environment', // Use back camera if available
          width: { ideal: 1280 },
          height: { ideal: 720 }
        } 
      });
      
      video.srcObject = mediaStream;
      video.style.display = 'block';
      
      // Show camera controls
      startCameraBtn.style.display = 'none';
      stopCameraBtn.style.display = 'inline-block';
      document.querySelector('.capture-controls').style.display = 'block';
      
      // Hide preview if it was showing
      capturedPreview.style.display = 'none';
      
      console.log("Camera started successfully");
    } else {
      showError("Camera not supported on this device.");
    }
  } catch (err) {
    console.error("Error accessing camera:", err);
    if (err.name === 'NotAllowedError') {
      showError("Camera access denied. Please allow camera permission and try again.");
    } else if (err.name === 'NotFoundError') {
      showError("No camera found on this device.");
    } else {
      showError("Error accessing camera: " + err.message);
    }
  }
}

function stopCamera() {
  if (mediaStream) {
    mediaStream.getTracks().forEach(track => track.stop());
    mediaStream = null;
  }
  
  video.style.display = 'none';
  startCameraBtn.style.display = 'inline-block';
  stopCameraBtn.style.display = 'none';
  document.querySelector('.capture-controls').style.display = 'none';
  
  console.log("Camera stopped");
}

function capturePhoto() {
  if (!mediaStream) {
    showError("Camera is not active. Please start the camera first.");
    return;
  }

  try {
    // Set canvas dimensions to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    // Draw the current video frame to canvas
    const context = canvas.getContext("2d");
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // Convert canvas to blob
    canvas.toBlob((blob) => {
      if (blob) {
        capturedImageBlob = blob;
        
        // Create preview image
        const imageUrl = URL.createObjectURL(blob);
        previewImage.src = imageUrl;
        
        // Show preview and hide camera
        capturedPreview.style.display = 'block';
        video.style.display = 'none';
        document.querySelector('.capture-controls').style.display = 'none';
        
        console.log("Photo captured successfully");
      } else {
        showError("Failed to capture photo. Please try again.");
      }
    }, "image/jpeg", 0.9);
    
  } catch (error) {
    console.error("Error capturing photo:", error);
    showError("Error capturing photo. Please try again.");
  }
}

function retakePhoto() {
  // Clear captured image
  capturedImageBlob = null;
  if (previewImage.src) {
    URL.revokeObjectURL(previewImage.src);
    previewImage.src = '';
  }
  
  // Hide preview and show camera again
  capturedPreview.style.display = 'none';
  video.style.display = 'block';
  document.querySelector('.capture-controls').style.display = 'block';
}

function newPhoto() {
  retakePhoto();
  stopCamera();
  startCamera();
}

async function analyzeCapturedPhoto() {
  if (!capturedImageBlob) {
    showError("No photo captured. Please capture a photo first.");
    return;
  }

  showLoading();
  
  try {
    const formData = new FormData();
    formData.append("file", capturedImageBlob, "camera_capture.jpg");

    const response = await fetch("/predict", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    hideLoading();

    if (data.error) {
      showError(data.error);
      return;
    }

    displayResult(data);
    
    // Scroll to results
    resultDiv.scrollIntoView({ behavior: 'smooth' });
    
  } catch (error) {
    hideLoading();
    showError("Analysis failed. Please try again.");
    console.error("JS Error:", error);
  }
}

// ---------------- HELPER FUNCTIONS ---------------- #
function showLoading() {
  loadingDiv.style.display = 'block';
  resultDiv.innerHTML = '';
}

function hideLoading() {
  loadingDiv.style.display = 'none';
}

function showError(message) {
  resultDiv.innerHTML = `
    <div class="error-message">
      <h2>❌ Error</h2>
      <p>${message}</p>
    </div>
  `;
}

function displayResult(data) {
  // Determine result type for styling
  let resultClass = 'success';
  if (data.confidence < 60) {
    resultClass = 'warning';
  }
  if (data.error) {
    resultClass = 'error';
  }

  resultDiv.innerHTML = `
    <h2>🧪 Analysis Result</h2>
    <p class="${resultClass}"><strong>Disease:</strong> ${data.prediction}</p>
    <p class="${resultClass}"><strong>Confidence:</strong> ${data.confidence}%</p>
    <p class="${resultClass}"><strong>Description:</strong> ${data.description}</p>
    <p class="${resultClass}"><strong>Treatment:</strong> ${data.treatment}</p>
    <p class="${resultClass}"><strong>Duration:</strong> ${data.duration}</p>
    <p class="${resultClass}"><strong>Prevention:</strong> ${data.prevention}</p>
  `;
}

// ---------------- INITIALIZATION ---------------- #
document.addEventListener('DOMContentLoaded', function() {
  // Initialize camera view as hidden
  video.style.display = 'none';
  
  // Add file input change handler for better UX
  document.getElementById("file-input").addEventListener("change", function(e) {
    const fileName = e.target.files[0]?.name;
    if (fileName) {
      document.querySelector(".file-label").textContent = `Selected: ${fileName}`;
    }
  });
  
  console.log("Plant Disease Detection App initialized");
});

// ---------------- ERROR HANDLING ---------------- #
window.addEventListener('error', function(e) {
  console.error('Global error:', e.error);
  showError('An unexpected error occurred. Please refresh the page and try again.');
});

// Handle page visibility change to stop camera when tab is hidden
document.addEventListener('visibilitychange', function() {
  if (document.hidden && mediaStream) {
    stopCamera();
  }
});

// ---------------- DISEASES DATABASE FUNCTIONALITY ---------------- #
const loadAllDiseasesBtn = document.getElementById("load-all-diseases-btn");
const searchPlantBtn = document.getElementById("search-plant-btn");
const plantSearchInput = document.getElementById("plant-search-input");
const diseasesDisplay = document.getElementById("diseases-display");

loadAllDiseasesBtn.addEventListener("click", loadAllDiseases);
searchPlantBtn.addEventListener("click", togglePlantSearch);
plantSearchInput.addEventListener("keypress", function(e) {
  if (e.key === "Enter") {
    searchPlantDiseases();
  }
});

function togglePlantSearch() {
  if (plantSearchInput.style.display === "none") {
    plantSearchInput.style.display = "inline-block";
    searchPlantBtn.textContent = "🔍 Search";
    plantSearchInput.focus();
  } else {
    plantSearchInput.style.display = "none";
    searchPlantBtn.textContent = "🔍 Search by Plant Type";
    plantSearchInput.value = "";
  }
}

async function loadAllDiseases() {
  try {
    loadAllDiseasesBtn.textContent = "⏳ Loading...";
    loadAllDiseasesBtn.disabled = true;
    
    const response = await fetch("/diseases");
    const data = await response.json();
    
    if (data.error) {
      showDiseasesError(data.error);
      return;
    }
    
    displayAllDiseases(data);
    
  } catch (error) {
    showDiseasesError("Failed to load diseases. Please try again.");
    console.error("Error loading diseases:", error);
  } finally {
    loadAllDiseasesBtn.textContent = "📋 Load All Diseases";
    loadAllDiseasesBtn.disabled = false;
  }
}

async function searchPlantDiseases() {
  const plantType = plantSearchInput.value.trim();
  if (!plantType) {
    showDiseasesError("Please enter a plant type to search.");
    return;
  }
  
  try {
    searchPlantBtn.textContent = "⏳ Searching...";
    searchPlantBtn.disabled = true;
    
    const response = await fetch(`/diseases/${encodeURIComponent(plantType)}`);
    const data = await response.json();
    
    if (data.error) {
      showDiseasesError(data.error);
      return;
    }
    
    displayPlantDiseases(data);
    
  } catch (error) {
    showDiseasesError("Failed to search diseases. Please try again.");
    console.error("Error searching diseases:", error);
  } finally {
    searchPlantBtn.textContent = "🔍 Search";
    searchPlantBtn.disabled = false;
  }
}

function displayAllDiseases(data) {
  const { total_diseases, healthy_plants, diseased_plants, diseases } = data;
  
  let html = `
    <div class="disease-stats">
      <h3>📊 Disease Database Statistics</h3>
      <div class="stats-grid">
        <div class="stat-item">
          <div class="stat-number">${total_diseases}</div>
          <div class="stat-label">Total Entries</div>
        </div>
        <div class="stat-item">
          <div class="stat-number">${healthy_plants}</div>
          <div class="stat-label">Healthy Plants</div>
        </div>
        <div class="stat-item">
          <div class="stat-number">${diseased_plants}</div>
          <div class="stat-label">Diseased Plants</div>
        </div>
      </div>
    </div>
  `;
  
  diseases.forEach(disease => {
    html += createDiseaseCard(disease);
  });
  
  diseasesDisplay.innerHTML = html;
}

function displayPlantDiseases(data) {
  const { plant_type, count, diseases } = data;
  
  let html = `
    <div class="disease-stats">
      <h3>🌿 ${plant_type} - Disease Information</h3>
      <div class="stats-grid">
        <div class="stat-item">
          <div class="stat-number">${count}</div>
          <div class="stat-label">Total Varieties</div>
        </div>
      </div>
    </div>
  `;
  
  diseases.forEach(disease => {
    html += createDiseaseCard(disease);
  });
  
  diseasesDisplay.innerHTML = html;
}

function createDiseaseCard(disease) {
  const isHealthy = disease.Disease.toLowerCase().includes('healthy');
  const cardClass = isHealthy ? 'disease-card healthy' : 'disease-card';
  
  // Check if link exists and is valid (handle NaN values from CSV)
  const hasValidLink = disease.Link && 
                      disease.Link !== 'N/A' && 
                      disease.Link !== 'nan' &&
                      disease.Link !== 'null' &&
                      disease.Link !== null &&
                      typeof disease.Link === 'string' &&
                      disease.Link.trim() !== '' && 
                      disease.Link.startsWith('http');
  
  return `
    <div class="${cardClass}">
      <h3>${disease.Disease.replace(/_/g, ' ')}</h3>
      <div class="disease-info">
        <p><strong>Description:</strong> ${disease.Description || 'N/A'}</p>
        <p><strong>Treatment:</strong> ${disease.Treatment || 'N/A'}</p>
        <p><strong>Medicine:</strong> ${disease.Medicine || 'N/A'}</p>
        <p><strong>Duration:</strong> ${disease.Duration || 'N/A'}</p>
        <p><strong>Prevention:</strong> ${disease.Prevention || 'N/A'}</p>
      </div>
      ${hasValidLink ? `
        <div class="disease-links">
          <a href="${disease.Link}" target="_blank" rel="noopener noreferrer">
            🔍 Search for ${disease.Medicine || 'Treatment'} Online
          </a>
        </div>
      ` : '<div class="disease-links"><p style="color: #6c757d; font-style: italic;">No online search link available</p></div>'}
    </div>
  `;
}

function showDiseasesError(message) {
  diseasesDisplay.innerHTML = `
    <div class="error-message">
      <h3>❌ Error</h3>
      <p>${message}</p>
    </div>
  `;
}
