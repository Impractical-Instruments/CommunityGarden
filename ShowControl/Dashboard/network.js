// Where each Element is. Addresses come from ShowControl/network.json, which serve.py
// serves at /api/network. No page holds an address of its own (AGENTS.md constraint 3),
// and no page works one out for itself: elementBase() is the one way.

// A Dashboard opened on a loopback name is a development machine with its Elements beside it.
// Any 127.x counts: serve.py prints the address of the machine's own name, 127.0.1.1 on Debian.
function openedLocally() {
  const host = location.hostname;
  return host === 'localhost' || host === '[::1]' || /^127(\.\d{1,3}){3}$/.test(host);
}

let elementsRequest = null;

function networkElements() {
  if (!elementsRequest) {
    elementsRequest = fetch('/api/network').then(async resp => {
      if (!resp.ok) throw new Error(`/api/network: HTTP ${resp.status}`);
      return (await resp.json()).elements || {};
    });
    elementsRequest.catch(() => { elementsRequest = null; });   // ask again next time
  }
  return elementsRequest;
}

// The base URL of an Element's monitoring server, with no trailing slash:
// elementBase('pipes'). `id` is a key of `elements` in network.json. In order:
//   1. ?<id>=host:port in the page's URL, as `make pipes-surface` prints for pipes;
//   2. on a Dashboard opened locally, that same host with the Element's http_port;
//   3. otherwise the Element's own ip and http_port. Elements do not run on the Dashboard's host.
async function elementBase(id) {
  const override = new URLSearchParams(location.search).get(id);
  if (override) return `http://${override}`;
  const el = (await networkElements())[id];
  if (!el || !el.http_port) throw new Error(`network.json has no http_port for "${id}"`);
  if (openedLocally()) return `http://${location.hostname}:${el.http_port}`;
  if (!el.ip) throw new Error(`network.json has no ip for "${id}"`);
  return `http://${el.ip}:${el.http_port}`;
}
