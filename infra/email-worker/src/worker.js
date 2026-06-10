/**
 * Cloudflare Email Routing worker for Finitum forwarding ingestion.
 *
 * Catch-all route on the apex `<domain>` -> this worker. It reads the raw MIME of the
 * forwarded message, HMAC-SHA256 signs it with INGEST_WEBHOOK_SECRET, and POSTs
 * it to the API's /ingest/email endpoint with the recipient as a query param.
 *
 * Bindings / secrets (see wrangler.toml):
 *   - INGEST_API_URL      (var)    e.g. https://api.finitum.app
 *   - INGEST_WEBHOOK_SECRET (secret) shared with the API
 */

async function hmacHex(secret, bytes) {
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const sig = await crypto.subtle.sign("HMAC", key, bytes);
  return [...new Uint8Array(sig)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

async function streamToBytes(stream) {
  const chunks = [];
  for await (const chunk of stream) chunks.push(chunk);
  let len = 0;
  for (const c of chunks) len += c.length;
  const out = new Uint8Array(len);
  let offset = 0;
  for (const c of chunks) {
    out.set(c, offset);
    offset += c.length;
  }
  return out;
}

export default {
  async email(message, env) {
    const raw = await streamToBytes(message.raw);
    const signature = await hmacHex(env.INGEST_WEBHOOK_SECRET, raw);
    const url = `${env.INGEST_API_URL}/ingest/email?recipient=${encodeURIComponent(message.to)}`;

    const res = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "message/rfc822",
        "X-Finitum-Signature": `sha256=${signature}`,
      },
      body: raw,
    });

    if (!res.ok) {
      // Reject so Cloudflare can surface the failure; avoid silent data loss.
      message.setReject(`Ingestion failed: ${res.status}`);
    }
  },
};
