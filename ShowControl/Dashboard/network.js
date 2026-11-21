// Where each Element is. Addresses come from ShowControl/network.json, which serve.py
// serves at /api/network. No page holds an address of its own (AGENTS.md constraint 3),
// and no page works one out for itself: elementBase() is the one way.

// A Dashboard opened on one of these is a development machine with its Elements beside it.
const LOCAL_HOSTS = ['localhost', '127.0.0.1', '[::1]'];

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
  if (LOCAL_HOSTS.includes(location.hostname)) return `http://${location.hostname}:${el.http_port}`;
  if (!el.ip) throw new Error(`network.json has no ip for "${id}"`);
  return `http://${el.ip}:${el.http_port}`;
}
