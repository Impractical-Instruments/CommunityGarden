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

// http://ip:port of an Element, from network.json. `?<id>=host:port` in the
// page URL overrides it, e.g. fundingcaptcha.html?captcha=localhost:PORT for
// an app running on a laptop. The Dashboard runs on the TreeHouse host, so
// location.hostname is only right for the TreeHouse.
async function elementBases() {
  const resp = await fetch('/api/network');
  if (!resp.ok) throw new Error(`/api/network: HTTP ${resp.status}`);
  const elements = (await resp.json()).elements || {};
  const params = new URLSearchParams(location.search);
  const bases = {};
  for (const [id, el] of Object.entries(elements)) {
    const override = params.get(id);
    if (override)                    bases[id] = `http://${override}`;
    else if (el.ip && el.http_port)  bases[id] = `http://${el.ip}:${el.http_port}`;
  }
  return bases;
}

async function elementBase(id) {
  const base = (await elementBases())[id];
  if (!base) throw new Error(`network.json has no ip/http_port for "${id}"`);
  return base;
}
