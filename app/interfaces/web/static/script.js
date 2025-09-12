// TravelRoboto chat UI logic
// Wires the input to POST /api/chat and renders { reply } as a chat bubble.

const chatBox = document.getElementById("chat-box");
const form = document.getElementById("chat-form");
const input = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");

function appendMessage(role, text) {
  const div = document.createElement("div");
  div.className = `message ${role}-message`;
  div.textContent = text;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}

function setPending(isPending) {
  sendBtn.disabled = isPending;
  sendBtn.textContent = isPending ? "Sending…" : "Send";
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const message = input.value.trim();
  if (!message) return;

  appendMessage("user", message);
  input.value = "";
  setPending(true);

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });

    // Optional: surface request id if server provides it
    const reqId = res.headers.get("X-Request-ID");

    if (!res.ok) {
      appendMessage("sys", `Error ${res.status}${reqId ? ` (rid ${reqId})` : ""}`);
      console.error("Chat error:", res.status, await safeText(res));
      return;
    }

    const data = await res.json();

    // Backend returns { reply: "..." } per your API
    const reply = data?.reply ?? "(no reply)";
    appendMessage("bot", reply);
  } catch (err) {
    appendMessage("sys", "Network error. Please try again.");
    console.error("Network error:", err);
  } finally {
    setPending(false);
    input.focus();
  }
});

async function safeText(response) {
  try { return await response.text(); } catch { return ""; }
}
