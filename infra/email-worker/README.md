# Finitum Email Worker

Cloudflare Email Routing worker that turns inbound forwarded bank emails into
HMAC-signed POSTs to the Finitum API (`POST /ingest/email`).

```
Bank → user's mailbox → (user forwarding filter)
     → u-<token>@<domain>
     → Cloudflare Email Routing (catch-all)
     → this Worker
     → POST https://api.finitum.app/ingest/email?recipient=...   (X-Finitum-Signature)
```

## Cloudflare setup

1. **Add the domain** to Cloudflare and enable **Email Routing**.
2. **MX records**: Email Routing automatically adds the `MX` (and SPF `TXT`)
   records on the **zone apex** (e.g. `finitum.app`). CF Email Routing is
   apex-only — ingest addresses must therefore live on the apex
   (`u-<token>@finitum.app`), which is what `INGEST_DOMAIN=finitum.app` produces.
   A dedicated `in.<domain>` subdomain is **not** supported by the managed
   catch-all and would require manually maintained subdomain MX records.
3. **Catch-all rule**: in Email Routing → Routing rules → Catch-all address, set
   the action to **Send to a Worker** and select `finitum-email-worker`. The
   catch-all matches every unmatched `…@<domain>` address, including the
   `u-<token>` ingest addresses.
4. **Deploy the worker**:
   ```sh
   cd infra/email-worker
   npm install -g wrangler   # if not installed
   wrangler deploy
   ```
5. **Set the shared secret** (must match the API's `INGEST_WEBHOOK_SECRET`):
   ```sh
   wrangler secret put INGEST_WEBHOOK_SECRET
   ```
6. **Point `INGEST_API_URL`** in `wrangler.toml` at your API origin.

## How signing works

The worker computes `HMAC-SHA256(raw_mime, INGEST_WEBHOOK_SECRET)` and sends it
as `X-Finitum-Signature: sha256=<hex>`. The API recomputes and compares in
constant time, rejecting mismatches with `401`. Unknown tokens still return
`200` (logged server-side) so retries can't probe which tokens are valid.
