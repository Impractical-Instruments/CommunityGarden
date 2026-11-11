// Element ports come from ShowControl/network.json, which serve.py serves at
// /api/network. No page holds a port of its own (AGENTS.md constraint 3).

async function elementPorts() {
  const resp = await fetch('/api/network');
  if (!resp.ok) throw new Error(`/api/network: HTTP ${resp.status}`);
  const elements = (await resp.json()).elements || {};
  const ports = {};
  for (const [id, el] of Object.entries(elements)) ports[id] = el.http_port;
  return ports;
}

async function elementPort(id) {
  const port = (await elementPorts())[id];
  if (!port) throw new Error(`network.json has no http_port for "${id}"`);
  return port;
}
