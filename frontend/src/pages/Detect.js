import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';
import { 
  Upload, 
  X, 
  CheckCircle,
  AlertTriangle,
  Download,
  Loader,
  Leaf,
  Clock,
  Shield,
  Info,
  Camera,
  FileImage
} from 'lucide-react';

const Detect = () => {
  const [capturedImage, setCapturedImage] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const videoRef = React.useRef(null);
  const canvasRef = React.useRef(null);
  const [activeTab, setActiveTab] = useState('upload');
  

  // Dropzone for file upload
  const onDrop = useCallback((acceptedFiles) => {
    const file = acceptedFiles[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = () => {
        setCapturedImage(reader.result);
        setResult(null);
        setError('');
      };
      reader.readAsDataURL(file);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.gif', '.bmp']
    },
    multiple: false
  });

  const resetDetection = () => {
    setCapturedImage(null);
    setResult(null);
    setError('');
  };

  // Live camera: start/stop
  const startCamera = async () => {
    try {
      setError('');
      const mediaStream = await navigator.mediaDevices.getUserMedia({ 
        video: { 
          facingMode: 'environment', 
          width: { ideal: 800 }, 
          height: { ideal: 600 }
        } 
      });
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
        await videoRef.current.play().catch(() => {});
      }
      setIsStreaming(true);
    } catch (e) {
      setError('Unable to access camera. Please allow permissions.');
    }
  };

  const stopCamera = () => {
    const video = videoRef.current;
    if (video && video.srcObject) {
      const tracks = video.srcObject.getTracks();
      tracks.forEach(t => t.stop());
      video.srcObject = null;
    }
    setIsStreaming(false);
  };

  const captureFrameBase64 = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return null;
    const vw = video.videoWidth || 640;
    const vh = video.videoHeight || 480;
    const side = Math.min(vw, vh); // center square crop to avoid background
    const sx = Math.max(0, Math.floor((vw - side) / 2));
    const sy = Math.max(0, Math.floor((vh - side) / 2));
    canvas.width = side;
    canvas.height = side;
    const ctx = canvas.getContext('2d');
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'high';
    ctx.drawImage(video, sx, sy, side, side, 0, 0, side, side);
    // Use higher quality to reduce compression artifacts for the model
    return canvas.toDataURL('image/jpeg', 0.95);
  };

  // Estimate sharpness using simple gradient magnitude (fast approximation)
  const estimateSharpness = (canvas) => {
    try {
      const ctx = canvas.getContext('2d');
      const { width, height } = canvas;
      const img = ctx.getImageData(0, 0, width, height).data;
      let score = 0;
      for (let y = 1; y < height - 1; y += 2) {
        for (let x = 1; x < width - 1; x += 2) {
          const i = (y * width + x) * 4;
          const gx = img[i + 4] - img[i - 4];
          const gy = img[i + width * 4] - img[i - width * 4];
          score += gx * gx + gy * gy;
        }
      }
      return score / (width * height);
    } catch (e) {
      return 0;
    }
  };

  const analyzeLive = async () => {
    setIsAnalyzing(true);
    setError('');
    try {
      // Allow camera exposure to settle a tick before capture
      await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
      // Capture multiple frames, choose sharpest
      const candidates = [];
      for (let i = 0; i < 3; i++) {
        const dataUrl = captureFrameBase64();
        if (dataUrl) {
          // draw back to canvas to reuse sharpness estimator
          const img = new Image();
          await new Promise((res) => {
            img.onload = () => {
              const canvas = canvasRef.current;
              const ctx = canvas.getContext('2d');
              ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
              const s = estimateSharpness(canvas);
              candidates.push({ dataUrl, s });
              res();
            };
            img.src = dataUrl;
          });
        }
        await new Promise((r) => requestAnimationFrame(r));
      }
      if (candidates.length === 0) {
        setError('Failed to capture frame.');
        return;
      }
      candidates.sort((a, b) => b.s - a.s);
      const imageData = candidates[0].dataUrl;
      if (!imageData) {
        setError('Failed to capture frame.');
        return;
      }
      // Send base64 to Django /api/detect/ to get the SAME JSON shape as file upload
      const resp = await axios.post('/api/detect/', { image: imageData });
      setResult({
        crop: resp.data.detection.crop,
        disease: resp.data.detection.disease,
        problem: resp.data.detection.problem || resp.data.detection.disease,
        confidence: resp.data.detection.confidence,
        is_healthy: resp.data.detection.is_healthy,
        treatment: resp.data.detection.treatment,
        description: resp.data.detection.description,
        duration: resp.data.detection.duration,
        prevention: resp.data.detection.prevention,
        class_name: resp.data.detection.class_name,
        detectionId: resp.data.detection.id
      });
      // Trigger dashboard refresh
      localStorage.setItem('dashboardRefresh', Date.now().toString());
      window.dispatchEvent(new Event('storage'));
    } catch (e) {
      console.error('Live analyze error:', e);
      setError(e.response?.data?.error || e.message || 'Live analysis failed.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const analyzeImage = async () => {
    if (!capturedImage) return;

    setIsAnalyzing(true);
    setError('');

    try {
      const response = await axios.post('/api/detect/', {
        image: capturedImage
      });

      console.log('API Response:', response.data); // Debug log

      setResult({
        crop: response.data.detection.crop,
        disease: response.data.detection.disease,
        problem: response.data.detection.problem || response.data.detection.disease,
        confidence: response.data.detection.confidence,
        is_healthy: response.data.detection.is_healthy,
        treatment: response.data.detection.treatment,
        description: response.data.detection.description,
        duration: response.data.detection.duration,
        prevention: response.data.detection.prevention,
        class_name: response.data.detection.class_name,
        detectionId: response.data.detection.id
      });
      
      // Trigger dashboard refresh
      localStorage.setItem('dashboardRefresh', Date.now().toString());
      window.dispatchEvent(new Event('storage'));
    } catch (error) {
      console.error('Detection Error:', error); // Debug log
      setError(error.response?.data?.error || 'Failed to analyze image');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const downloadImage = () => {
    if (capturedImage) {
      const link = document.createElement('a');
      link.href = capturedImage;
      link.download = 'crop-detection.jpg';
      link.click();
    }
  };

  

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Crop Disease Detection
        </h1>
        <p className="text-lg text-gray-600">
          Choose Upload or Live Camera to detect crop diseases using our AI model
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="flex justify-center mb-8">
        <div className="bg-gray-100 rounded-lg p-1 flex">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setActiveTab('upload')}
            className={`flex items-center gap-2 px-6 py-3 rounded-md transition-all ${
              activeTab === 'upload'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <FileImage className="w-5 h-5" />
            Upload Image
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setActiveTab('camera')}
            className={`flex items-center gap-2 px-6 py-3 rounded-md transition-all ${
              activeTab === 'camera'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <Camera className="w-5 h-5" />
            Live Camera
          </motion.button>
        </div>
      </div>

      {/* Tab Content */}
      <AnimatePresence mode="wait">
        {activeTab === 'upload' ? (
          <motion.div
            key="upload"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-6"
          >
            {/* File Upload Section */}
            <div className="bg-white rounded-lg shadow-lg p-6 border">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">
                Upload Image for Detection
              </h2>
              
              {/* Dropzone */}
              <div
                {...getRootProps()}
                className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                  isDragActive
                    ? 'border-blue-400 bg-blue-50'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                <input {...getInputProps()} />
                <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                {isDragActive ? (
                  <p className="text-blue-600">Drop the image here...</p>
                ) : (
                  <div>
                    <p className="text-gray-600 mb-2">
                      Drag & drop an image here, or click to select
                    </p>
                    <p className="text-sm text-gray-500">
                      Supports: JPG, PNG, GIF, BMP
                    </p>
                  </div>
                )}
              </div>

              {/* Preview */}
              {capturedImage && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-6"
                >
                  <div className="relative">
                    <img
                      src={capturedImage}
                      alt="Preview"
                      className="w-full max-w-md mx-auto rounded-lg shadow-md"
                    />
                    <button
                      onClick={resetDetection}
                      className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1 hover:bg-red-600 transition-colors"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                  
                  <div className="flex justify-center gap-4 mt-4">
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={analyzeImage}
                      disabled={isAnalyzing}
                      className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                    >
                      {isAnalyzing ? (
                        <Loader className="w-5 h-5 animate-spin" />
                      ) : (
                        <Leaf className="w-5 h-5" />
                      )}
                      {isAnalyzing ? 'Analyzing...' : 'Analyze Image'}
                    </motion.button>
                    
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={downloadImage}
                      className="flex items-center gap-2 px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
                    >
                      <Download className="w-5 h-5" />
                      Download
                    </motion.button>
                  </div>
                </motion.div>
              )}
            </div>

            {/* Results Section */}
            <AnimatePresence>
              {result && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="bg-white rounded-lg shadow-lg p-6 border"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      {result.is_healthy ? (
                        <CheckCircle className="w-8 h-8 text-green-500" />
                      ) : (
                        <AlertTriangle className="w-8 h-8 text-red-500" />
                      )}
                      <div>
                        <h3 className="text-xl font-semibold text-gray-900">
                          Leaf Problem: {result.problem || result.disease}
                        </h3>
                        <p className="text-sm text-gray-500">
                          Confidence: {result.confidence}%
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="grid md:grid-cols-2 gap-6">
                    <div className="space-y-4">
                      {result.description && (
                        <div>
                          <h4 className="font-medium text-gray-900 mb-2 flex items-center gap-2">
                            <Info className="w-4 h-4" />
                            Description
                          </h4>
                          <p className="text-gray-700">{result.description}</p>
                        </div>
                      )}
                      
                      {result.treatment && (
                        <div>
                          <h4 className="font-medium text-gray-900 mb-2 flex items-center gap-2">
                            <Shield className="w-4 h-4" />
                            Treatment
                          </h4>
                          <p className="text-gray-700">{result.treatment}</p>
                        </div>
                      )}
                    </div>
                    
                    <div className="space-y-4">
                      {result.duration && result.duration !== 'N/A' && (
                        <div>
                          <h4 className="font-medium text-gray-900 mb-2 flex items-center gap-2">
                            <Clock className="w-4 h-4" />
                            Duration
                          </h4>
                          <p className="text-gray-700">{result.duration}</p>
                        </div>
                      )}
                      
                      {result.prevention && (
                        <div>
                          <h4 className="font-medium text-gray-900 mb-2 flex items-center gap-2">
                            <Shield className="w-4 h-4" />
                            Prevention
                          </h4>
                          <p className="text-gray-700">{result.prevention}</p>
                        </div>
                      )}
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Error Display */}
            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg"
                >
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5" />
                    {error}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        ) : (
          <motion.div
            key="camera"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-6"
          >
            {/* Live Camera Section */}
            <div className="bg-white rounded-lg shadow-lg p-6 border">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Camera className="w-5 h-5" /> Live Camera Detection
              </h2>
              <div className="relative bg-gray-900 rounded-lg overflow-hidden flex justify-center">
                <video ref={videoRef} autoPlay playsInline muted className="w-full max-w-[600px] aspect-square object-cover" />
                <canvas ref={canvasRef} className="hidden" />
              </div>
              <div className="flex flex-wrap gap-4 items-center mt-4">
                {!isStreaming ? (
                  <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} onClick={startCamera} className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700">
                    Start Camera
                  </motion.button>
                ) : (
                  <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} onClick={stopCamera} className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700">
                    Stop Camera
                  </motion.button>
                )}
                <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} onClick={analyzeLive} disabled={!isStreaming || isAnalyzing} className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
                  {isAnalyzing ? 'Analyzing...' : 'Capture & Analyze'}
                </motion.button>
              </div>
            </div>

            {/* Results Section */}
            <AnimatePresence>
              {result && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="bg-white rounded-lg shadow-lg p-6 border"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      {result.is_healthy ? (
                        <CheckCircle className="w-8 h-8 text-green-500" />
                      ) : (
                        <AlertTriangle className="w-8 h-8 text-red-500" />
                      )}
                      <div>
                        <h3 className="text-xl font-semibold text-gray-900">
                          Leaf Problem: {result.problem || result.disease}
                        </h3>
                        <p className="text-sm text-gray-500">
                          Confidence: {result.confidence}%
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="grid md:grid-cols-2 gap-6">
                    <div className="space-y-4">
                      {result.description && (
                        <div>
                          <h4 className="font-medium text-gray-900 mb-2 flex items-center gap-2">
                            <Info className="w-4 h-4" />
                            Description
                          </h4>
                          <p className="text-gray-700">{result.description}</p>
                        </div>
                      )}
                      
                      {result.treatment && (
                        <div>
                          <h4 className="font-medium text-gray-900 mb-2 flex items-center gap-2">
                            <Shield className="w-4 h-4" />
                            Treatment
                          </h4>
                          <p className="text-gray-700">{result.treatment}</p>
                        </div>
                      )}
                    </div>
                    
                    <div className="space-y-4">
                      {result.duration && result.duration !== 'N/A' && (
                        <div>
                          <h4 className="font-medium text-gray-900 mb-2 flex items-center gap-2">
                            <Clock className="w-4 h-4" />
                            Duration
                          </h4>
                          <p className="text-gray-700">{result.duration}</p>
                        </div>
                      )}
                      
                      {result.prevention && (
                        <div>
                          <h4 className="font-medium text-gray-900 mb-2 flex items-center gap-2">
                            <Shield className="w-4 h-4" />
                            Prevention
                          </h4>
                          <p className="text-gray-700">{result.prevention}</p>
                        </div>
                      )}
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Error Display */}
            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg"
                >
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5" />
                    {error}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default Detect; 
