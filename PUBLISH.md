# How to publish (you run this — agents cannot create GitHub remotes here)

```bash
bash /Users/arjunkshah21/Downloads/cursormib/mib-solution/tools/USER_PUBLISH.sh
```

That script:

1. Creates/pushes `https://github.com/arjunkshah12345-hash/mib-doc-solution`
2. Forks `8090-inc/mib-doc-challenge` and stages the three PR files
3. Opens the Google form URL

After the form is filled, tell the agent: **queue the challenge PR**
