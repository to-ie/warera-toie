# My War Era dashboard

A personal, single-page dashboard for the [War Era](https://app.warera.io/)
player **toie**. One scroll, three cards, works on mobile.

It is a single self-contained `index.html` — plain HTML/CSS/vanilla JS, no build
step, no framework, **no proxy/worker**. Every request goes straight to the game
API (`api2.warera.io`) using your personal API token.

## What it shows

1. **Companies — best region?** Each company with its item, current region,
   production bonus and income tax, plus a verdict (`✓ Best placed` or
   `→ Move to <region> +X%`). For companies you personally work in (👷) it
   optimises *take-home* (after tax) instead of raw output.
2. **Employees — clock-ins & payments.** Per worker: an Active / Slowing / Idle
   status with last clock-in, the last few wage payments, and a 48h clock-in
   count. Clock-ins are derived from wage transactions where the worker sold
   labour **to you**.
3. **Wealth trend.** Historic wealth snapshots (embedded) plus a live "now"
   reading, drawn as a sparkline with total and change since the first record.

The `↻ Refresh` button re-pulls everything.

## Data sources (all direct, no proxy)

| Data | Endpoint | Auth |
|------|----------|------|
| Company list & details | `company.getCompanies`, `company.getById` | public |
| Regions & deposits | `region.getRegionsObject` | public |
| Country bonuses / industrialism | `api.warerastats.io/countries` | public |
| Live wealth | `user.getUserById` | public |
| Worker roster | `worker.getWorkers` | **token** |
| Wage transactions | `transaction.getPaginatedTransactions` | **token** |

The token is sent only as the `X-API-Key` header to `api2.warera.io`.

> Note: country-side bonus figures come from warerastats and can differ from the
> in-game value by a fraction of a percent (e.g. +61.8% vs +62%). This is
> immaterial for ranking regions.

## The API token

The page needs your token to read the worker roster and wage transactions. It
looks for it in this order:

1. `localStorage` on the current browser (set the first time you paste it).
2. A file named `api-token` sitting next to `index.html`.

`api-token` is **gitignored** and must never be committed — it grants full API
access to your account.

## Run it locally (zero typing)

```bash
cd warera-toie
python3 -m http.server 8000
```

Open `http://localhost:8000`. With the `api-token` file present it loads
automatically — no typing. To open it on your phone, use your machine's LAN
address, e.g. `http://192.168.1.x:8000`.

`file://` will not work — `fetch` needs a real origin.

## Deploy to GitHub Pages

Push **`index.html`** and **`.nojekyll`** only. Do **not** commit `api-token`
(the gitignore prevents this unless you force it).

Enable Pages on the repo (Settings → Pages → deploy from branch). On the live
site the `api-token` file won't exist, so the page shows a one-time paste field:
enter your token once and it's saved in that browser's `localStorage` and
auto-loads thereafter. You paste once per device, never again.

### Why not a GitHub Actions secret?

Secrets only stay hidden during a server-side build. This is a static
client-side page, so the token has to reach the browser to work — baking a
secret into the deployed files would make it public. The only ways to keep a
token truly hidden are a server-side proxy (deliberately avoided here) or having
each user supply their own token at runtime (what this page does).

## Security

- `api-token` grants full account API access. Keep it gitignored; never deploy
  or serve it publicly.
- The `index.html` itself is safe to publish — a stranger opening the URL just
  sees an empty paste prompt and gets no access to your account.
- The token, once pasted on a deployed page, lives only in that browser's
  `localStorage`.
