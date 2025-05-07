document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const cameraFeed = document.getElementById('camera-feed');
    const cameraCanvas = document.getElementById('camera-canvas');
    const captureBtn = document.getElementById('capture-btn');
    const retakeBtn = document.getElementById('retake-btn');
    const processCameraBtn = document.getElementById('process-camera-btn');
    const cameraPreview = document.getElementById('camera-preview');
    const cameraPreviewImg = document.getElementById('camera-preview-img');
    const fileInput = document.getElementById('file-input');
    const dropArea = document.getElementById('drop-area');
    const uploadPreview = document.getElementById('upload-preview');
    const uploadPreviewImg = document.getElementById('upload-preview-img');
    const changeFileBtn = document.getElementById('change-file-btn');
    const processUploadBtn = document.getElementById('process-upload-btn');
    const resultsContainer = document.querySelector('.results-container');
    const backBtn = document.getElementById('back-btn');
    const resultOriginalImg = document.getElementById('result-original-img');
    const resultProcessedImg = document.getElementById('result-processed-img');
    const extractedTextEl = document.getElementById('extracted-text');
    const medicineNameBadge = document.getElementById('medicine-name-badge');
    const infoLoading = document.getElementById('info-loading');
    const medicineInfo = document.getElementById('medicine-info');
    const errorModal = document.getElementById('error-modal');
    const errorMessage = document.getElementById('error-message');
    const closeModalBtns = document.querySelectorAll('.close-modal');

    // Variables
    let stream = null;
    let capturedImage = null;
    let uploadedFile = null;

    // Initialize
    initCamera();
    setupTabs();
    setupEventListeners();

    // Tab functionality
    function setupTabs() {
        tabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const tabId = btn.getAttribute('data-tab');
                
                // Update active tab button
                tabBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                // Show active tab content
                tabContents.forEach(content => {
                    content.classList.remove('active');
                    if (content.id === `${tabId}-tab`) {
                        content.classList.add('active');
                    }
                });
                
                // If switching to camera tab, ensure camera is initialized
                if (tabId === 'camera' && !stream) {
                    initCamera();
                }
            });
        });
    }

    // Setup event listeners
    function setupEventListeners() {
        // Camera controls
        captureBtn.addEventListener('click', captureImage);
        retakeBtn.addEventListener('click', retakePicture);
        processCameraBtn.addEventListener('click', processCameraImage);
        
        // File upload controls
        fileInput.addEventListener('change', handleFileSelect);
        dropArea.addEventListener('dragover', handleDragOver);
        dropArea.addEventListener('dragleave', handleDragLeave);
        dropArea.addEventListener('drop', handleFileDrop);
        dropArea.addEventListener('click', () => fileInput.click());
        changeFileBtn.addEventListener('click', () => fileInput.click());
        processUploadBtn.addEventListener('click', processUploadedImage);
        
        // Results controls
        backBtn.addEventListener('click', showMain);
        
        // Modal controls
        closeModalBtns.forEach(btn => {
            btn.addEventListener('click', closeErrorModal);
        });
    }
    
    // Camera functions
    function initCamera() {
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
                .then(videoStream => {
                    stream = videoStream;
                    cameraFeed.srcObject = stream;
                    cameraFeed.play();
                    toggleCameraControls(true);
                })
                .catch(error => {
                    showError(`Camera access error: ${error.message}. Please ensure you've granted camera permissions.`);
                    console.error('Camera error:', error);
                });
        } else {
            showError('Your browser does not support camera access. Please try using the file upload option instead.');
        }
    }
    
    function stopCamera() {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            stream = null;
        }
    }
    
    function toggleCameraControls(showCamera) {
        if (showCamera) {
            cameraFeed.style.display = 'block';
            cameraPreview.style.display = 'none';
            captureBtn.style.display = 'block';
            retakeBtn.style.display = 'none';
            processCameraBtn.style.display = 'none';
        } else {
            cameraFeed.style.display = 'none';
            cameraPreview.style.display = 'block';
            captureBtn.style.display = 'none';
            retakeBtn.style.display = 'block';
            processCameraBtn.style.display = 'block';
        }
    }
    
    function captureImage() {
        const context = cameraCanvas.getContext('2d');
        
        // Set canvas dimensions to match the video feed
        cameraCanvas.width = cameraFeed.videoWidth;
        cameraCanvas.height = cameraFeed.videoHeight;
        
        // Draw the current frame from the video onto the canvas
        context.drawImage(cameraFeed, 0, 0, cameraCanvas.width, cameraCanvas.height);
        
        // Convert the canvas content to a data URL
        capturedImage = cameraCanvas.toDataURL('image/png');
        
        // Display the captured image
        cameraPreviewImg.src = capturedImage;
        
        // Show the preview and relevant controls
        toggleCameraControls(false);
    }
    
    function retakePicture() {
        capturedImage = null;
        toggleCameraControls(true);
    }
    
    function processCameraImage() {
        if (!capturedImage) {
            showError('No image has been captured. Please take a photo first.');
            return;
        }
        
        processImage(capturedImage, 'camera');
    }
    
    // File upload functions
    function handleDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
        dropArea.classList.add('active');
    }
    
    function handleDragLeave(e) {
        e.preventDefault();
        e.stopPropagation();
        dropArea.classList.remove('active');
    }
    
    function handleFileDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        dropArea.classList.remove('active');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    }
    
    function handleFileSelect(e) {
        const files = e.target.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    }
    
    function handleFile(file) {
        // Check if the file is an image
        if (!file.type.match('image.*')) {
            showError('The selected file is not an image. Please select an image file (JPEG, PNG, etc.).');
            return;
        }
        
        uploadedFile = file;
        
        // Display the file preview
        const reader = new FileReader();
        reader.onload = function(e) {
            uploadPreviewImg.src = e.target.result;
            uploadPreview.style.display = 'block';
            dropArea.style.display = 'none';
            changeFileBtn.style.display = 'block';
            processUploadBtn.style.display = 'block';
        };
        reader.readAsDataURL(file);
    }
    
    function processUploadedImage() {
        if (!uploadedFile) {
            showError('No file has been selected. Please upload an image first.');
            return;
        }
        
        const reader = new FileReader();
        reader.onload = function(e) {
            processImage(e.target.result, 'upload');
        };
        reader.readAsDataURL(uploadedFile);
    }
    
    // Image processing functions
    function processImage(imageData, source) {
        showLoading(true);
        
        // Display the original image in results
        resultOriginalImg.src = imageData;
        
        // Make API call to process the image
        // This is a placeholder for the actual API call
        fetch('/api/process-medicine-image', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ image: imageData })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Server returned an error response');
            }
            return response.json();
        })
        .then(data => {
            // Handle successful response
            displayResults(data, imageData);
        })
        .catch(error => {
            showError(`Failed to process image: ${error.message}`);
            console.error('Processing error:', error);
            showLoading(false);
        });
    }
    
    // Results display functions
    function displayResults(data, originalImage) {
        // Update UI elements with results
        if (data.processedImage) {
            resultProcessedImg.src = data.processedImage;
        } else {
            resultProcessedImg.src = originalImage;
        }
        
        if (data.extractedText) {
            extractedTextEl.textContent = data.extractedText;
        } else {
            extractedTextEl.textContent = 'No text was detected in the image.';
        }
        
        if (data.medicineName) {
            medicineNameBadge.textContent = data.medicineName;
            medicineNameBadge.style.display = 'inline-block';
            
            // Fetch medicine information
            fetchMedicineInfo(data.medicineName);
        } else {
            medicineNameBadge.style.display = 'none';
            medicineInfo.textContent = 'No medicine was detected in the image.';
            infoLoading.style.display = 'none';
        }
        
        // Show results container
        showResults();
        showLoading(false);
    }
    
    function fetchMedicineInfo(medicineName) {
        infoLoading.style.display = 'block';
        medicineInfo.textContent = '';
        
        // Make API call to fetch medicine information
        fetch(`/api/medicine-info?name=${encodeURIComponent(medicineName)}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to fetch medicine information');
                }
                return response.json();
            })
            .then(data => {
                infoLoading.style.display = 'none';
                
                if (data.info) {
                    // Format and display medicine information
                    let infoHtml = '';
                    
                    if (data.info.description) {
                        infoHtml += `<p><strong>Description:</strong> ${data.info.description}</p>`;
                    }
                    if (data.info.usedFor) {
                        infoHtml += `<p><strong>Used for:</strong> ${data.info.usedFor}</p>`;
                    }
                    if (data.info.sideEffects) {
                        infoHtml += `<p><strong>Common side effects:</strong> ${data.info.sideEffects}</p>`;
                    }
                    if (data.info.warnings) {
                        infoHtml += `<p><strong>Warnings:</strong> ${data.info.warnings}</p>`;
                    }
                    
                    medicineInfo.innerHTML = infoHtml;
                } else {
                    medicineInfo.textContent = 'No detailed information available for this medicine.';
                }
            })
            .catch(error => {
                infoLoading.style.display = 'none';
                medicineInfo.textContent = `Could not retrieve medicine information: ${error.message}`;
                console.error('Medicine info error:', error);
            });
    }
    
    // UI state management
    function showMain() {
        resultsContainer.style.display = 'none';
        tabContents.forEach(content => {
            if (content.classList.contains('active')) {
                content.style.display = 'block';
            }
        });
        
        // Reset upload UI if needed
        if (uploadPreview.style.display === 'block') {
            uploadPreview.style.display = 'none';
            dropArea.style.display = 'block';
            changeFileBtn.style.display = 'none';
            processUploadBtn.style.display = 'none';
        }
    }
    
    function showResults() {
        tabContents.forEach(content => {
            content.style.display = 'none';
        });
        resultsContainer.style.display = 'block';
    }
    
    function showLoading(isLoading) {
        // Implement loading state UI
        const loadingElements = document.querySelectorAll('.loading-indicator');
        loadingElements.forEach(el => {
            el.style.display = isLoading ? 'block' : 'none';
        });
        
        // Disable buttons during loading
        const actionButtons = document.querySelectorAll('.action-btn');
        actionButtons.forEach(btn => {
            btn.disabled = isLoading;
        });
    }
    
    function showError(message) {
        errorMessage.textContent = message;
        errorModal.style.display = 'flex';
    }
    
    function closeErrorModal() {
        errorModal.style.display = 'none';
    }
    
    // Clean up resources when page is unloaded
    window.addEventListener('beforeunload', function() {
        stopCamera();
    });
});
    