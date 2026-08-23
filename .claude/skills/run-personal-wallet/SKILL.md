---
name: run-personal-wallet
description: Run, start, build, screenshot, or verify the Esnupi Wallet React app. Use this skill when asked to launch the app, take a screenshot, test a UI change, or confirm a feature works in the browser.
---

# run-personal-wallet

The dev server proxies `/api` to `http://localhost:8000` (backend not required for the frontend to load).
The driver uses Playwright with the system-installed Chrome (`channel: 'chrome'`) — no additional browser download needed.

## Prerequisites

- Node 18+ with `npm`
- Google Chrome installed (the Playwright script uses `channel: 'chrome'`)
- `playwright` installed as a dev dependency (already in `package.json`)

Install dependencies (first time only):

```
npm install
```

## Build

No pre-build step required for dev. For a production bundle:

```
npm run build
```

## Run — agent path

In a second terminal, run the driver to screenshot the app:

```
node .claude/skills/run-personal-wallet/driver.mjs [route]
```

## Run — human path

```
npm start
```

Opens `http://localhost:5173` in the browser. Ctrl-C to stop.

