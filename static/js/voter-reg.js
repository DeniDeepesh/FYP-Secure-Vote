// Get references to the form and video elements
const form = document.getElementById('registrationForm');
const videoElement = document.getElementById('videoElement');
const canvasElement = document.getElementById('canvasElement');

// Access the webcam
navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => {
        videoElement.srcObject = stream;
    })
    .catch(error => {
        console.error('Error accessing webcam:', error);
    });

// Handle form submission
form.addEventListener('submit', async (event) => {
    event.preventDefault();

    // Get form data
    const formData = new FormData(event.target);

    // Capture facial landmarks
    const facialLandmarks = await captureFacialLandmarks();

    // Append facial landmarks to form data
    formData.append('facialLandmarks', JSON.stringify(facialLandmarks));

    // Send form data to the backend (your Python code)
    fetch('/register', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (response.ok) {
            console.log('Registration successful!');
            // Reset the form or show a success message
        } else {
            console.error('Registration failed');
            // Show an error message
        }
    })
    .catch(error => {
        console.error('Error during registration:', error);
        // Show an error message
    });
});

// Function to capture facial landmarks
async function captureFacialLandmarks() {
    // Implement your facial landmark detection logic here
    // You can use libraries like face-api.js or dlib.js
    // Return the facial landmarks as an object or null if no face is detected

    // Example:
    const facialLandmarks = {
        // facial landmark data
    };

    return facialLandmarks;
}