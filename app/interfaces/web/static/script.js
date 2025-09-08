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
//##################################


async function sendMessage() {
  const inputBox = document.getElementById("user-input");
  const message = inputBox.value.trim();
  if (!message) return;

  const chatBox = document.getElementById("chat-box");

  // Add user message bubble
  const userBubble = document.createElement("div");
  userBubble.className = "message user-message";
  userBubble.textContent = message;
  chatBox.appendChild(userBubble);

  inputBox.value = "";
  chatBox.scrollTop = chatBox.scrollHeight;

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message })
    });
    const data = await response.json();

    // Add bot message bubble
    const botBubble = document.createElement("div");
    botBubble.className = "message bot-message";
    botBubble.textContent = data.response;
    chatBox.appendChild(botBubble);

    chatBox.scrollTop = chatBox.scrollHeight;
  } catch (err) {
    console.error("Error sending message:", err);
  }
}