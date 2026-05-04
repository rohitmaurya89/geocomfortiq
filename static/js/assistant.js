// GeoComfortIQ — assistant.js
// AI Assistant panel — supports Gemini API with multi-turn history + markdown

document.addEventListener('DOMContentLoaded', () => {
  const panel     = document.getElementById('assistantPanel');
  const mainArea  = document.getElementById('gciqMain');
  const toggleBtn = document.getElementById('toggleAssistant');
  const closeBtn  = document.getElementById('closeAssistant');
  const input     = document.getElementById('assistantInput');
  const sendBtn   = document.getElementById('assistantSend');
  const messages  = document.getElementById('assistantMessages');

  if (!panel) return;

  // ── Conversation history for multi-turn context ────────────────────────────
  const history = [];

  // ── Panel open / close ─────────────────────────────────────────────────────
  function openPanel() {
    panel.classList.add('open');
    mainArea.classList.add('panel-open');
    input?.focus();
  }
  function closePanel() {
    panel.classList.remove('open');
    mainArea.classList.remove('panel-open');
  }

  toggleBtn?.addEventListener('click', () =>
    panel.classList.contains('open') ? closePanel() : openPanel()
  );
  closeBtn?.addEventListener('click', closePanel);

  // ── Lightweight markdown renderer ─────────────────────────────────────────
  function renderMarkdown(text) {
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g,     '<em>$1</em>')
      .replace(/`(.*?)`/g,       '<code>$1</code>')
      .replace(/^• (.+)$/gm,     '<li>$1</li>')
      .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
      .replace(/\n/g,            '<br>');
  }

  // ── Add message bubble ─────────────────────────────────────────────────────
  function addMessage(text, role = 'bot', source = null) {
    const msg    = document.createElement('div');
    msg.className = `msg msg-${role}`;

    const bubble = document.createElement('div');
    bubble.className = 'msg-bubble';
    bubble.innerHTML = renderMarkdown(text);

    // Source badge on bot messages
    if (role === 'bot' && source) {
      const badge = document.createElement('div');
      badge.className = `assistant-source-badge ${source === 'gemini' ? 'badge-gemini' : 'badge-fallback'}`;
      badge.textContent = source === 'gemini' ? '✦ Gemini AI' : '⚙ Local';
      bubble.appendChild(badge);
    }

    msg.appendChild(bubble);
    messages.appendChild(msg);
    messages.scrollTop = messages.scrollHeight;
  }

  // ── Typing indicator ───────────────────────────────────────────────────────
  function showTyping() {
    const msg = document.createElement('div');
    msg.className = 'msg msg-bot typing-indicator';
    msg.id = 'typingIndicator';
    msg.innerHTML = `<div class="msg-bubble">
      <span class="typing-dot"></span>
      <span class="typing-dot"></span>
      <span class="typing-dot"></span>
    </div>`;
    messages.appendChild(msg);
    messages.scrollTop = messages.scrollHeight;
  }
  function removeTyping() {
    document.getElementById('typingIndicator')?.remove();
  }

  // ── Send message ───────────────────────────────────────────────────────────
  async function sendMessage(text) {
    text = text.trim();
    if (!text) return;

    addMessage(text, 'user');
    history.push({ role: 'user', content: text });
    if (input) input.value = '';
    sendBtn.disabled = true;

    showTyping();

    try {
      const payload = {
        message: text,
        history: history.slice(-6),
      };
      if (window.GCIQ_RESULT_ID) payload.result_id = window.GCIQ_RESULT_ID;

      const res = await fetch('/assistant/chat/', {
        method:  'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken':  getCookie('csrftoken'),
        },
        body: JSON.stringify(payload),
      });

      const data   = await res.json();
      removeTyping();

      const reply  = data.reply  || 'Sorry, I could not process that.';
      const source = data.source || 'fallback';

      addMessage(reply, 'bot', source);
      history.push({ role: 'assistant', content: reply });

    } catch (err) {
      removeTyping();
      addMessage('⚠️ Connection error. Please try again.', 'bot', 'fallback');
    } finally {
      sendBtn.disabled = false;
      input?.focus();
    }
  }

  sendBtn?.addEventListener('click', () => sendMessage(input?.value || ''));
  input?.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) sendMessage(input.value);
  });

  // ── Global quick-send (called from template buttons) ───────────────────────
  window.sendQuick = function(text) {
    openPanel();
    setTimeout(() => sendMessage(text), 150);
  };

  // ── CSRF helper ────────────────────────────────────────────────────────────
  function getCookie(name) {
    for (const cookie of document.cookie.split(';')) {
      const c = cookie.trim();
      if (c.startsWith(name + '='))
        return decodeURIComponent(c.slice(name.length + 1));
    }
    return null;
  }
});
