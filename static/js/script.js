/* ================= GLOBAL ================= */
let selectedType = "autonomous";

/* ================= SELECT TYPE ================= */
function selectType(type, element) {
    selectedType = type;

    document.querySelectorAll(".type-card").forEach(card => {
        card.classList.remove("active");
    });

    element.classList.add("active");
}

/* ================= NEW CHAT ================= */
function newChat() {
    document.getElementById("chat-box").innerHTML = "";
}

/* ================= SEND MESSAGE ================= */
function sendMessage() {
    const input = document.getElementById("userInput");
    const message = input.value.trim();

    if (message === "") return;

    const chatBox = document.getElementById("chat-box");

    /* USER MESSAGE */
    chatBox.innerHTML += `
        <div class="user">
            <div>${message}</div>
        </div>
    `;

    saveToHistory(message);

    /* BOT TYPING EFFECT */
    const typingDiv = document.createElement("div");
    typingDiv.className = "bot";
    typingDiv.innerHTML = `<div>Typing...</div>`;
    chatBox.appendChild(typingDiv);

    chatBox.scrollTop = chatBox.scrollHeight;

    /* API CALL */
    fetch("http://127.0.0.1:5000/chat", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            message: message,
            type: selectedType
        })
    })
    .then(res => res.json())
    .then(data => {

        /* REMOVE TYPING */
        typingDiv.remove();

        /* BOT RESPONSE */
        chatBox.innerHTML += `
            <div class="bot">
                <div>${data.bot_response}</div>
            </div>
        `;

        /* VIDEO PLAY BUTTON HANDLER */
        setTimeout(() => {
            document.querySelectorAll(".play-btn").forEach(btn => {
                btn.addEventListener("click", function () {
                    const videoId = this.getAttribute("data-video");
                    const video = document.getElementById(videoId);

                    if (video) {
                        video.play();
                        this.style.display = "none";
                    }
                });
            });
        }, 100);

        chatBox.scrollTop = chatBox.scrollHeight;
    })
    .catch(() => {

        typingDiv.remove();

        chatBox.innerHTML += `
            <div class="bot">
                <div>⚠️ Server error. Please try again.</div>
            </div>
        `;
    });

    input.value = "";
}

/* ================= ENTER KEY ================= */
document.getElementById("userInput")
.addEventListener("keypress", function(e) {
    if (e.key === "Enter") {
        sendMessage();
    }
});

/* ================= CHAT HISTORY ================= */
function saveToHistory(message) {
    const historyBox = document.getElementById("chat-history");

    const item = document.createElement("div");
    item.innerText = message.substring(0, 25) + "...";

    item.onclick = () => {
        document.getElementById("userInput").value = message;
    };

    historyBox.prepend(item);
}

/* ================= OPTIONAL: AUTO SCROLL FIX ================= */
const chatBox = document.getElementById("chat-box");

const observer = new MutationObserver(() => {
    chatBox.scrollTop = chatBox.scrollHeight;
});

observer.observe(chatBox, { childList: true });

/* ================= OPTIONAL: CLEAR HISTORY ================= */
function clearHistory() {
    document.getElementById("chat-history").innerHTML = "";
}