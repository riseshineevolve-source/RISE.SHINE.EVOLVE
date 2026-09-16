# IndexNow setup for RSE

IndexNow is prepared but intentionally **not enabled automatically in CI** until the owner creates and hosts a real verification key.

## Production host

`rise-shine-evolve-learning-hub.com`

## 1. Create a key

Create an IndexNow key using the current protocol requirements. Do not commit it to Git.

The helper expects:

- `INDEXNOW_KEY` — required for a real submission.
- `INDEXNOW_KEY_LOCATION` — optional HTTPS location of the verification text file on the RSE production domain.
- `INDEXNOW_ENDPOINT` — optional; defaults to `https://api.indexnow.org/indexnow`.

## 2. Host the verification file

Preferred protocol pattern: host the UTF-8 key file on the production website, ideally at the root, and ensure it is publicly retrievable over HTTPS.

Do not add a fake key file to the repository before a real key has been chosen.

## 3. Validate URLs without sending anything

```bash
npm run indexnow:submit -- --dry-run https://rise-shine-evolve-learning-hub.com/library/world-01/
```

The helper rejects URLs outside the production RSE origin.

## 4. Real submission

Set the secret only in the execution environment, then run:

```bash
INDEXNOW_KEY="<real-key>" npm run indexnow:submit -- https://rise-shine-evolve-learning-hub.com/library/world-01/
```

If the verification file is not at the root/default location, also set:

```bash
INDEXNOW_KEY_LOCATION="https://rise-shine-evolve-learning-hub.com/<key-file>.txt"
```

Multiple changed URLs may be submitted in one command. The helper deduplicates them and enforces the protocol batch limit.

## 5. Automation policy

Do not submit unchanged URLs repeatedly.

A future deployment integration may call the helper only for URLs that were materially added, updated or removed. Until the actual static-site deployment mechanism and secret storage are verified, keep IndexNow manual/on-demand.

## Security rules

- never commit the key,
- never print the real key in logs,
- never submit staging/local URLs,
- do not add IndexNow submission to scheduled CI merely to create activity,
- treat HTTP 200/202 as receipt/acceptance, not a guarantee of indexing.
