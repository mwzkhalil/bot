// Audio setup
const beepSound = new Audio('/static/assets/beep.mp3');
let beepInterval;

// Global variables
let peerConnection = null;
let dataChannel = null;
let timerInterval = null;
let seconds = 0;
let isConnected = false;

// DOM elements
let ringBox, callStatus, timer, endCallBtn, callButton, avatarContainer;

// Initialize elements when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    ringBox = document.getElementById('ringBox');
    callStatus = document.querySelector('.call-status');
    timer = document.querySelector('.timer');
    endCallBtn = document.getElementById('endCallBtn');
    callButton = document.getElementById('callButton');
    avatarContainer = document.querySelector('.avatar-container');
    
    // Add event listeners
    callButton.addEventListener('click', startCall);
    endCallBtn.addEventListener('click', endCall);
    
    // Create star elements for animation
    createStars();
});

// Create animated stars in the background
function createStars() {
    const starCount = 30;
    for (let i = 0; i < starCount; i++) {
        setTimeout(() => {
            const star = document.createElement('div');
            star.className = 'stars';
            star.style.left = `${Math.random() * 100}%`;
            star.style.top = `${Math.random() * 100}%`;
            star.style.animationDuration = `${1 + Math.random() * 2}s`;
            star.style.animationDelay = `${Math.random() * 2}s`;
            
            ringBox.appendChild(star);
            
            // Remove stars after animation completes to prevent DOM clutter
            setTimeout(() => {
                if (ringBox.contains(star)) {
                    ringBox.removeChild(star);
                }
            }, 3000);
        }, i * 100);
    }
}

async function startCall() {
    ringBox.style.display = 'block';
    callButton.style.display = 'none';
    callStatus.textContent = 'Ringing...';
    
    // Ensure avatar has ringing animation
    avatarContainer.classList.add('ringing');
    
    startBeeping();
    createStars();
    showLoader('Connecting to AI assistant...');
    
    try {
        await initOpenAIRealtime();
    } catch (error) {
        hideLoader();
        showNotification('Failed to connect. Please try again.', 'error');
        endCall();
    }
}

function showLoader(message = 'Processing...') {
    const loader = document.querySelector('.loader');
    loader.querySelector('span').textContent = message;
    loader.style.display = 'flex';
}

function hideLoader() {
    document.querySelector('.loader').style.display = 'none';
}

function startBeeping() {
    beepSound.play();
    beepInterval = setInterval(() => beepSound.play(), 3000);
}

function stopBeeping() {
    clearInterval(beepInterval);
}

const fns = {
    changeBackgroundColor: ({ color1, color2 }) => {
        ringBox.style.background = `linear-gradient(135deg, ${color1} 0%, ${color2} 100%)`;
        return { success: true, color1, color2 };
    },
    sendEmail: async ({ message, customer_name, customer_email }) => {
        try {
            showLoader('Sending email...');
            const response = await fetch('/send-email', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    message, 
                    customer_name: customer_name || 'Customer',
                    customer_email
                })
            });
            hideLoader();
            const result = await response.json();
            
            if (result.success) {
                showNotification('Email sent successfully!', 'success');
            } else {
                showNotification('Failed to send email', 'error');
            }
            
            return result;
        } catch (error) {
            hideLoader();
            showNotification('Failed to send email', 'error');
            return { success: false, error: error.message };
        }
    }
};

async function initOpenAIRealtime() {
    try {
        const tokenResponse = await fetch("/session");
        const data = await tokenResponse.json();
        const EPHEMERAL_KEY = data.client_secret.value;

        peerConnection = new RTCPeerConnection();
        
        peerConnection.onconnectionstatechange = () => {
            if (peerConnection.connectionState === 'connected') {
                stopBeeping();
                isConnected = true;
                callStatus.textContent = 'Connected to AI Assistant';
                timer.style.display = 'block';
                endCallBtn.style.display = 'block';
                hideLoader();
                avatarContainer.classList.remove('ringing');
                startTimer();
                
                // Celebratory animation for successful connection
                showNotification('Connection established!', 'success');
            } else if (peerConnection.connectionState === 'failed' || 
                       peerConnection.connectionState === 'disconnected' || 
                       peerConnection.connectionState === 'closed') {
                hideLoader();
                if (isConnected) {
                    endCall();
                } else {
                    showNotification('Connection failed', 'error');
                    endCall();
                }
            }
        };

        const audioElement = document.createElement("audio");
        audioElement.autoplay = true;
        document.body.appendChild(audioElement);
        
        peerConnection.ontrack = event => {
            audioElement.srcObject = event.streams[0];
        };

        const mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaStream.getTracks().forEach(track => {
            peerConnection.addTrack(track, mediaStream);
        });

        dataChannel = peerConnection.createDataChannel('response');

        dataChannel.addEventListener('open', () => {
            const event = {
                type: 'session.update',
                session: {
                    modalities: ['text', 'audio'],
                    tools: [
                        {
                            type: 'function',
                            name: 'changeBackgroundColor',
                            parameters: {
                                type: 'object',
                                properties: {
                                    color1: { type: 'string' },
                                    color2: { type: 'string' }
                                },
                                required: ['color1', 'color2']
                            }
                        },
                        {
                            type: 'function',
                            name: 'sendEmail',
                            parameters: {
                                type: 'object',
                                properties: {
                                    message: { type: 'string' },
                                    customer_name: { type: 'string' },
                                    customer_email: { type: 'string' }
                                },
                                required: ['message', 'customer_email']
                            }
                        }
                    ]
                }
            };
            dataChannel.send(JSON.stringify(event));
        });

        dataChannel.addEventListener('message', async (ev) => {
            try {
                const msg = JSON.parse(ev.data);
                if (msg.type === 'response.function_call_arguments.done') {
                    const fn = fns[msg.name];
                    if (fn) {
                        const args = JSON.parse(msg.arguments);
                        const result = await fn(args);
                        const event = {
                            type: 'conversation.item.create',
                            item: {
                                type: 'function_call_output',
                                call_id: msg.call_id,
                                output: JSON.stringify(result)
                            }
                        };
                        dataChannel.send(JSON.stringify(event));
                    }
                }
            } catch (error) {
                console.error('Error handling message:', error);
            }
        });

        const offer = await peerConnection.createOffer();
        await peerConnection.setLocalDescription(offer);

        const apiUrl = "https://api.openai.com/v1/realtime";
        const model = "gpt-4o-realtime-preview-2024-12-17";
        
        const sdpResponse = await fetch(`${apiUrl}?model=${model}`, {
            method: "POST",
            body: offer.sdp,
            headers: {
                Authorization: `Bearer ${EPHEMERAL_KEY}`,
                "Content-Type": "application/sdp"
            },
        });

        if (!sdpResponse.ok) {
            throw new Error(`API responded with status: ${sdpResponse.status}`);
        }

        const answer = {
            type: "answer",
            sdp: await sdpResponse.text(),
        };
        await peerConnection.setRemoteDescription(answer);

    } catch (error) {
        console.error("Error:", error);
        hideLoader();
        showNotification('Connection error: ' + error.message, 'error');
        endCall();
    }
}

function startTimer() {
    seconds = 0;
    timer.textContent = formatTime(seconds);
    timerInterval = setInterval(() => {
        seconds++;
        timer.textContent = formatTime(seconds);
    }, 1000);
}

function formatTime(seconds) {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${String(hrs).padStart(2, '0')}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

function showNotification(message, type = 'success') {
    // Remove any existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notification => notification.remove());
    
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    // Add appropriate icon
    const icon = document.createElement('i');
    icon.className = type === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-circle';
    notification.appendChild(icon);
    
    const text = document.createElement('span');
    text.textContent = message;
    notification.appendChild(text);
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (document.body.contains(notification)) {
                document.body.removeChild(notification);
            }
        }, 500);
    }, 3000);
}

function endCall() {
    stopBeeping();
    hideLoader();
    
    if (timerInterval) clearInterval(timerInterval);
    
    if (peerConnection) {
        peerConnection.close();
        peerConnection = null;
    }
    
    if (isConnected) {
        fetch('/end-call', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ duration: seconds })
        }).catch(error => console.error('Failed to record call end:', error));
        
        callStatus.textContent = `Call ended - Duration: ${formatTime(seconds)}`;
        avatarContainer.classList.remove('ringing');
        endCallBtn.style.display = 'none';
        showNotification('Call ended successfully', 'success');
        
        setTimeout(() => {
            ringBox.style.display = 'none';
            callButton.style.display = 'block';
            timer.style.display = 'none';
        }, 3000);
    } else {
        callStatus.textContent = 'Call terminated';
        setTimeout(() => {
            ringBox.style.display = 'none';
            callButton.style.display = 'block';
        }, 1500);
    }
    
    isConnected = false;
    
    // Clean up any remaining elements
    const stars = document.querySelectorAll('.stars');
    stars.forEach(star => {
        if (star.parentNode) {
            star.parentNode.removeChild(star);
        }
    });
}