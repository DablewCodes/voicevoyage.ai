document.addEventListener('DOMContentLoaded', function() {
    var owlDots = document.querySelector('.owl-dots');

    if (owlDots) {
        owlDots.parentNode.removeChild(owlDots);
    }
});

// Target Language Select JS

let selectContainer = document.querySelector(".target-lang-select-container");
let select = document.querySelector(".target-lang-select");
let input = document.getElementById("target-lang-input");
let options = document.querySelectorAll(".target-lang-select-container .target-lang-option");

select.onclick = () => {
    selectContainer.classList.toggle("active");
};

options.forEach((e) => {
    e.addEventListener("click", () => {
        input.value = e.innerText;
        selectContainer.classList.remove("active");
        options.forEach((e) => {
            e.classList.remove("selected");
        });
        e.classList.add("selected");
    });
});

// Target Voice Select JS

let voiceSelectContainer = document.querySelector(".target-voice-select-container");
let voiceSelect = document.querySelector(".target-voice-select");
let voiceInput = document.getElementById("target-voice-input");
let voiceOptions = document.querySelectorAll(".target-voice-select-container .target-voice-option");

voiceSelect.onclick = () => {
    voiceSelectContainer.classList.toggle("active");
};

voiceOptions.forEach((e) => {
    e.addEventListener("click", () => {
        voiceInput.value = e.innerText;
        voiceSelectContainer.classList.remove("active");
        voiceOptions.forEach((e) => {
            e.classList.remove("selected");
        });
        e.classList.add("selected");
    });
});

// File Upload Widget JS

document.addEventListener('DOMContentLoaded', function() {
    var uploadFile = document.getElementById('upload-file');
    var fileUploadName = document.getElementById('file-upload-name');
    var uploadWrapper = document.getElementsByClassName('upload-wrapper')[0];

    uploadFile.addEventListener('change', function() {
        var filename = this.value;
        fileUploadName.innerHTML = filename;

        if (filename !== "") {
            setTimeout(function() {
                uploadWrapper.classList.add("uploaded");
            }, 300);

            setTimeout(function() {
                uploadWrapper.classList.remove("uploaded");
                uploadWrapper.classList.add("success");
            }, 800);
        }
    });
});

// Form handling JS

document.addEventListener('DOMContentLoaded', function() {
    var videoURL = document.getElementById('videoURL');
    var fileUpload = document.getElementById('upload-file');
    var languageInput = document.getElementById('target-lang-input');
    var voiceInput = document.getElementById('target-voice-input');
    var submitButton = document.getElementById('form-submition-button');
    var langSelectContainer = document.querySelector(".target-lang-select-container");
    var langSelectOptions = document.querySelectorAll(".target-lang-select-container .target-lang-option");
    var voiceSelectContainer = document.querySelector(".target-voice-select-container");
    var voiceSelectOptions = document.querySelectorAll(".target-voice-select-container .target-voice-option");

    // Function to check the state of inputs and adjust button availability
    function updateButtonState() {
        var urlRegex = /^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)[\w-]+$/;
        var isURLValid = urlRegex.test(videoURL.value);

        if ((isURLValid || fileUpload.files.length) && languageInput.value && voiceInput.value) {
            submitButton.disabled = false;
            submitButton.classList.remove('button-overlay');
            submitButton.style.cursor = "pointer"

            submitButton.addEventListener('click', function(event) {

                event.preventDefault();

                var videoURL = document.getElementById('videoURL');
                var fileUpload = document.getElementById('upload-file');
                var languageInput = document.getElementById('target-lang-input');
                var voiceInput = document.getElementById('target-voice-input');

                var formData = new FormData();

                if (fileUpload.files.length)
                {
                    formData.append("uploadedFile", fileUpload.files[0]);
                } else {
                    formData.append("videoURL", videoURL.value);
                }
                formData.append("targetLanguage", languageInput.value);
                formData.append("targetVoice", voiceInput.value);

                fetch('/dubbing/get_dubbing', { // Replace '/submit' with your actual submission endpoint
                    method: 'POST',
                    body: formData,
                })
                .then(response => response.blob())
                .then(blob => {
                    download(blob)
                    // Handle response here (e.g., display a success message, redirect, etc.)
                })
                .catch(error => {
                    alert(error)
                    console.error('Error:', error);
                    // Handle error here (e.g., display an error message)
                });

            });

        } else {
            submitButton.disabled = true;
            submitButton.classList.add('button-overlay');
        }
    }

    // Event listeners for input changes
    videoURL.addEventListener('input', function() {
        var fileUploadName = document.getElementById('file-upload-name');
        var uploadWrapper = document.getElementsByClassName('upload-wrapper')[0];
        fileUploadName.innerHTML = "";
        uploadWrapper.classList.remove("uploaded");
        uploadWrapper.classList.remove("uploaded");
        uploadWrapper.classList.remove("success");
        fileUpload.value = ''; // Clear file input if URL is entered
        updateButtonState();
    });

    fileUpload.addEventListener('change', function() {
        videoURL.value = ''; // Clear URL input if file is uploaded
        updateButtonState();
    });

    // Event listener for the custom select dropdown options
    langSelectOptions.forEach((option) => {
        option.addEventListener('click', () => {
            languageInput.value = option.innerText;
            langSelectContainer.classList.remove("active");
            updateButtonState(); // Update the button state when a language is selected
        });
    });

    voiceSelectOptions.forEach((option) => {
        option.addEventListener('click', () => {
            voiceInput.value = option.innerText;
            voiceSelectContainer.classList.remove("active");
            updateButtonState(); // Update the button state when a language is selected
        });
    });
});


// Socket handling js

//var socket = io(); // Socket variable for client-server communication

// Event listener for server messages
//ocket.on('processing_update', function (data) {
  //console.log('Message from server:', data); // Receive message from the server
  // Process the message received from the server
  //console.log(data)
  //document.getElementById('status-text').innerText = data
//});

//socket.on('connect', function () {
  //console.log("CONNECTED")
//})