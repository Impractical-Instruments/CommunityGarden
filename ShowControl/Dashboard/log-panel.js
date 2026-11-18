// The log panel on every Element detail page: connectLogs(host, port) streams the
// Element's /logs socket into #log-lines and shows the connection in #log-conn.
const MAX_LOG_LINES = 500;

function appendLog(entry) {
  const logPanel = document.getElementById('log-panel');
  const logLines = document.getElementById('log-lines');
  const div = document.createElement('div');
  div.className = 'log-line log-' + entry.level.toLowerCase();
  div.textContent = `[${entry.ts}] ${entry.level.padEnd(8)} ${entry.msg}`;
  logLines.appendChild(div);
  if (logPanel.scrollTop + logPanel.clientHeight >= logPanel.scrollHeight - 40)
    logPanel.scrollTop = logPanel.scrollHeight;
  while (logLines.children.length > MAX_LOG_LINES)
    logLines.removeChild(logLines.firstChild);
}

function connectLogs(host, port) {
  const logConn = document.getElementById('log-conn');
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  const ws = new WebSocket(`${proto}://${host}:${port}/logs`);
  ws.onopen  = () => { logConn.textContent = 'connected';     logConn.className = 'log-conn connected'; };
  ws.onclose = () => { logConn.textContent = 'reconnecting…'; logConn.className = 'log-conn disconnected'; setTimeout(() => connectLogs(host, port), 2000); };
  ws.onerror = () => ws.close();
  ws.onmessage = ev => { try { appendLog(JSON.parse(ev.data)); } catch (_) {} };
}
