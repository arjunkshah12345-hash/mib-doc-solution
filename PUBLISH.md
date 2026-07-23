# Publish as public solution repo

Ship build: **v27** only (see `../mib-solution/artifacts/SHIP.md`).

Agents on this machine cannot create the remote. From this directory, you run:

1. Commit the ship tree (code + docs only — no `data/`, no train preds).
2. Create/push public repo named **`arjunkshah12345-hash/mib-doc-solution`**
   (same URL as in `SUBMISSION.md`).

Suggested commit message: `Ship v27: 132.34 train, CFA=0 offline MIB solution.`

If an empty remote already exists, add it as `origin` and push `main`.
