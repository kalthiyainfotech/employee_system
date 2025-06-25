let startTime = 0;
let elapsedTime = 0;
let pauseStart = 0;
let accumulatedPauseTime = 0;
let timerInterval = null;
let isRunning = false;

// Elements
const statusButton = document.querySelector('.btn-status');
const displayTimer = document.querySelector('.stat-value');
const totalTimeDisplay = document.querySelectorAll('.timer')[0];
const workTimeDisplay = document.querySelectorAll('.timer')[1];
const pauseTimeDisplay = document.querySelectorAll('.timer')[2];

const startBtn = document.querySelector('.btn-start');
const pauseBtn = document.querySelector('.btn-pause');
const stopBtn = document.querySelector('.btn-stop');

// Format time as hh:mm:ss
function formatTime(ms) {
    const totalSeconds = Math.floor(ms / 1000);
    const hours = String(Math.floor(totalSeconds / 3600)).padStart(2, '0');
    const minutes = String(Math.floor((totalSeconds % 3600) / 60)).padStart(2, '0');
    const seconds = String(totalSeconds % 60).padStart(2, '0');
    return `${hours}:${minutes}:${seconds}`;
}

// Update the display
function updateTimerDisplay() {
    const now = Date.now();
    const workTime = elapsedTime + (isRunning ? now - startTime : 0);
    const pauseTime = accumulatedPauseTime + (!isRunning && pauseStart ? now - pauseStart : 0);
    const totalTime = workTime + pauseTime;

    displayTimer.textContent = formatTime(totalTime);
    totalTimeDisplay.textContent = formatTime(totalTime);
    workTimeDisplay.textContent = formatTime(workTime);
    pauseTimeDisplay.textContent = formatTime(pauseTime);
}

// Save timer state to localStorage
function saveTimerState() {
    localStorage.setItem("timerState", JSON.stringify({
        startTime,
        elapsedTime,
        pauseStart,
        accumulatedPauseTime,
        isRunning
    }));
}

// Load timer state from localStorage
function loadTimerState() {
    const saved = localStorage.getItem("timerState");
    if (saved) {
        const state = JSON.parse(saved);
        startTime = state.startTime;
        elapsedTime = state.elapsedTime;
        pauseStart = state.pauseStart;
        accumulatedPauseTime = state.accumulatedPauseTime;
        isRunning = state.isRunning;

        if (isRunning) {
            timerInterval = setInterval(updateTimerDisplay, 1000);
            statusButton.textContent = 'Running';
            pauseBtn.disabled = false;
            stopBtn.disabled = false;
        } else if (pauseStart) {
            statusButton.textContent = 'Paused';
            pauseBtn.disabled = true;
            stopBtn.disabled = false;
        }

        updateTimerDisplay();
    }
}

// Get CSRF token for Django
function getCSRFToken() {
    let name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Default state
pauseBtn.disabled = true;
stopBtn.disabled = true;

// START
startBtn.addEventListener('click', () => {
    if (!isRunning) {
        startTime = Date.now();
        if (pauseStart > 0) {
            accumulatedPauseTime += Date.now() - pauseStart;
            pauseStart = 0;
        }

        timerInterval = setInterval(updateTimerDisplay, 1000);
        statusButton.textContent = 'Running';
        isRunning = true;

        pauseBtn.disabled = false;
        stopBtn.disabled = false;
        startBtn.innerHTML = '<i class="bi bi-play-fill me-2"></i>START';

        saveTimerState();

        fetch("", {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
                "X-CSRFToken": getCSRFToken(),
            },
            body: "action=start_tracker",
        });
    }
});

// PAUSE
pauseBtn.addEventListener('click', () => {
    if (isRunning) {
        clearInterval(timerInterval);
        elapsedTime += Date.now() - startTime;
        pauseStart = Date.now();
        isRunning = false;
        statusButton.textContent = 'Paused';

        startBtn.innerHTML = '<i class="bi bi-play-fill me-2"></i>PLAY';
        pauseBtn.disabled = true;

        saveTimerState();
    }
});

// STOP
stopBtn.addEventListener('click', () => {
    clearInterval(timerInterval); // stop timer updates
    const now = Date.now();

    const finalWorkTime = elapsedTime + (isRunning ? now - startTime : 0);
    const finalPauseTime = accumulatedPauseTime + (!isRunning && pauseStart ? now - pauseStart : 0);
    const finalTotalTime = finalWorkTime + finalPauseTime;

    displayTimer.textContent = formatTime(finalTotalTime);
    totalTimeDisplay.textContent = formatTime(finalTotalTime);
    workTimeDisplay.textContent = formatTime(finalWorkTime);
    pauseTimeDisplay.textContent = formatTime(finalPauseTime);

    // Reset state
    elapsedTime = 0;
    startTime = 0;
    accumulatedPauseTime = 0;
    pauseStart = 0;
    isRunning = false;

    statusButton.textContent = 'Stopped';

    startBtn.innerHTML = '<i class="bi bi-play-fill me-2"></i>START';
    pauseBtn.disabled = true;
    stopBtn.disabled = true;

    // ✅ REMOVE localStorage saving after STOP
    localStorage.removeItem("timerState");

    // ✅ STOP global setInterval (prevent resaving after STOP)
    if (window.saveTimerInterval) clearInterval(window.saveTimerInterval);

    fetch("", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": getCSRFToken(),
        },
        body: `action=end_tracker&total_time=${formatTime(finalTotalTime)}&pause_time=${formatTime(finalPauseTime)}&work_time=${formatTime(finalWorkTime)}`
    }).then(() => {
        setTimeout(() => window.location.reload(), 100000);
    });
});

// Load saved timer state on page load
window.addEventListener("load", loadTimerState);

// Update display and save state every second
// Save reference to clear later
window.saveTimerInterval = setInterval(() => {
    updateTimerDisplay();
    saveTimerState();
}, 1000);



