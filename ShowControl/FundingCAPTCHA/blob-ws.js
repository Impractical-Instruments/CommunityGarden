/**
 * BlobWS — WebSocket client that receives blob frames from the server
 * and forwards them to a callback.
 *
 * Separate from TouchInput so either piece can be used or replaced independently.
 */
class BlobWS {
  /** Build the ws:// or wss:// URL for the current page's server. */
  static wsUrl() {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    return `${proto}://${location.host}/ws`;
  }

  /**
   * @param {object} opts
   * @param {string} opts.url           WebSocket URL (use BlobWS.wsUrl() for same-host)
   * @param {(blobs: {id,x,y,z}[]) => void} opts.onBlobs  Called each frame with blob array
   * @param {number} [opts.reconnectMs=2000]  Delay before reconnect after close/error
   */
  constructor({ url, onBlobs, reconnectMs = 2000 }) {
    this._url          = url;
    this._onBlobs      = onBlobs;
    this._reconnectMs  = reconnectMs;
    this._ws           = null;
    this._destroyed    = false;
    this._connect();
  }

  _connect() {
    if (this._destroyed) return;
    const ws = new WebSocket(this._url);
    this._ws = ws;

    ws.onmessage = (ev) => {
      let msg;
      try { msg = JSON.parse(ev.data); } catch (_) { return; }
      if (Array.isArray(msg.blobs)) this._onBlobs(msg.blobs);
    };

    ws.onclose = () => {
      if (!this._destroyed) setTimeout(() => this._connect(), this._reconnectMs);
    };

    ws.onerror = () => ws.close();
  }

  destroy() {
    this._destroyed = true;
    this._ws?.close();
    this._ws = null;
  }
}
