# CLAUDE.md

## Release

Use `./release.sh` to bump version and publish:

```bash
./release.sh patch   # 0.1.0 -> 0.1.1
./release.sh minor   # 0.1.0 -> 0.2.0
./release.sh major   # 0.1.0 -> 1.0.0
```

This script updates `.claude-plugin/plugin.json`, commits, tags, and pushes automatically.
