async function sendMessage() {
    const inputBox = document.getElementById("user-input");
    const message = inputBox.value;
    if (!message) return;

    const response = await fetch("/chat", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({message})
    });
    const data = await response.json();

    const chatBox = document.getElementById("chat-box");
    chatBox.innerHTML += `<div><b>You:</b> ${message}</div>`;
    chatBox.innerHTML += `<div><b>Bot:</b> ${data.response}</div>`;
    inputBox.value = "";
    chatBox.scrollTop = chatBox.scrollHeight;
}
