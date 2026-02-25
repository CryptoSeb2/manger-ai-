(function() {
  'use strict';

  var script = document.currentScript;
  var businessId = script.getAttribute('data-business-id');
  if (!businessId) return;

  var baseUrl = script.src.replace(/\/static\/chat-widget\.js.*$/, '');
  var config = null;
  var history = [];
  var isOpen = false;
  var isLoaded = false;

  function loadConfig(cb) {
    if (config) { cb(); return; }
    fetch(baseUrl + '/api/chat/config?business_id=' + encodeURIComponent(businessId))
      .then(function(r) { return r.json(); })
      .then(function(data) {
        config = data;
        isLoaded = true;
        cb();
      })
      .catch(function() {
        config = { name: 'Us', greeting_message: 'Hi! How can I help you today?' };
        isLoaded = true;
        cb();
      });
  }

  function sendMessage(msg, cb) {
    history.push({ role: 'user', content: msg });
    fetch(baseUrl + '/api/chat/message', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ business_id: parseInt(businessId, 10), message: msg, conversation_history: history })
    })
      .then(function(r) { return r.json(); })
      .then(function(data) {
        history.push({ role: 'assistant', content: data.reply });
        cb(null, data.reply);
      })
      .catch(function(err) {
        cb(err, 'Sorry, I had trouble connecting. Please try again or call us.');
      });
  }

  function createWidget() {
    var style = document.createElement('style');
    style.textContent = [
      '#wwa-chat-root{font-family:system-ui,-apple-system,sans-serif;font-size:14px;line-height:1.5}',
      '#wwa-chat-btn{position:fixed;bottom:20px;right:20px;width:56px;height:56px;border-radius:50%;background:#4f46e5;color:#fff;border:none;cursor:pointer;box-shadow:0 4px 12px rgba(79,70,229,.4);display:flex;align-items:center;justify-content:center;z-index:99998;transition:transform .2s}',
      '#wwa-chat-btn:hover{transform:scale(1.05)}',
      '#wwa-chat-btn svg{width:24px;height:24px}',
      '#wwa-chat-window{position:fixed;bottom:90px;right:20px;width:380px;max-width:calc(100vw - 40px);height:480px;max-height:calc(100vh - 120px);background:#fff;border-radius:12px;box-shadow:0 10px 40px rgba(0,0,0,.15);display:flex;flex-direction:column;z-index:99999;overflow:hidden}',
      '#wwa-chat-window.hidden{display:none}',
      '#wwa-chat-header{padding:16px;background:#4f46e5;color:#fff;font-weight:600;font-size:15px}',
      '#wwa-chat-messages{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:12px;background:#f9fafb}',
      '#wwa-chat-messages .wwa-msg{max-width:85%;padding:10px 14px;border-radius:12px;font-size:14px}',
      '#wwa-chat-messages .wwa-msg.user{align-self:flex-end;background:#4f46e5;color:#fff;border-bottom-right-radius:4px}',
      '#wwa-chat-messages .wwa-msg.bot{align-self:flex-start;background:#fff;color:#1f2937;border:1px solid #e5e7eb;border-bottom-left-radius:4px}',
      '#wwa-chat-messages .wwa-typing{align-self:flex-start;padding:10px 14px;background:#fff;border:1px solid #e5e7eb;border-radius:12px;border-bottom-left-radius:4px;color:#6b7280;font-size:13px}',
      '#wwa-chat-input-wrap{padding:12px;border-top:1px solid #e5e7eb;background:#fff}',
      '#wwa-chat-input{width:100%;padding:12px 16px;border:1px solid #e5e7eb;border-radius:8px;font-size:14px;outline:none;box-sizing:border-box}',
      '#wwa-chat-input:focus{border-color:#4f46e5;box-shadow:0 0 0 2px rgba(79,70,229,.2)}'
    ].join('');
    document.head.appendChild(style);

    var root = document.createElement('div');
    root.id = 'wwa-chat-root';

    var btn = document.createElement('button');
    btn.id = 'wwa-chat-btn';
    btn.setAttribute('aria-label', 'Open chat');
    btn.innerHTML = '<svg fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z"/></svg>';
    root.appendChild(btn);

    var win = document.createElement('div');
    win.id = 'wwa-chat-window';
    win.className = 'hidden';
    win.innerHTML = [
      '<div id="wwa-chat-header">' + (config ? config.name : 'Chat') + '</div>',
      '<div id="wwa-chat-messages"></div>',
      '<div id="wwa-chat-input-wrap"><input id="wwa-chat-input" type="text" placeholder="Type your message..." autocomplete="off"></div>'
    ].join('');
    root.appendChild(win);

    document.body.appendChild(root);

    var messagesEl = document.getElementById('wwa-chat-messages');
    var inputEl = document.getElementById('wwa-chat-input');
    var headerEl = document.getElementById('wwa-chat-header');

    function addMsg(text, isUser) {
      var div = document.createElement('div');
      div.className = 'wwa-msg ' + (isUser ? 'user' : 'bot');
      div.textContent = text;
      messagesEl.appendChild(div);
      messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    function addTyping() {
      var div = document.createElement('div');
      div.className = 'wwa-typing';
      div.id = 'wwa-typing-el';
      div.textContent = 'Typing...';
      messagesEl.appendChild(div);
      messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    function removeTyping() {
      var el = document.getElementById('wwa-typing-el');
      if (el) el.remove();
    }

    function showGreeting() {
      var msg = (config && config.greeting_message) ? config.greeting_message : 'Hi! How can I help you today?';
      addMsg(msg, false);
    }

    btn.onclick = function() {
      isOpen = !isOpen;
      win.classList.toggle('hidden', !isOpen);
      if (isOpen && messagesEl.children.length === 0) showGreeting();
      if (isOpen) inputEl.focus();
    };

    function doSend() {
      var text = inputEl.value.trim();
      if (!text) return;
      inputEl.value = '';
      addMsg(text, true);
      addTyping();
      sendMessage(text, function(err, reply) {
        removeTyping();
        addMsg(reply, false);
      });
    }

    inputEl.onkeydown = function(e) {
      if (e.key === 'Enter') { e.preventDefault(); doSend(); }
    };

    loadConfig(function() {
      if (config && config.name) headerEl.textContent = config.name;
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', createWidget);
  } else {
    createWidget();
  }
})();
