# Publish this folder as a public remote

This machine blocks agents from creating remotes. From this directory, run once:

```bash
cd /Users/arjunkshah21/Downloads/cursormib/mib-challenge-v2
gh repo create arjunkshah12345-hash/mib-challenge-v2 --public --source=. --remote=origin --push
```

If the empty remote already exists:

```bash
cd /Users/arjunkshah21/Downloads/cursormib/mib-challenge-v2
git remote add origin https://github.com/arjunkshah12345-hash/mib-challenge-v2.git
git push -u origin main
```

Do **not** push into or modify `mib-challenge-v1`.
