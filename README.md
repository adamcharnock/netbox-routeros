# Netbox plugin for auto-configuring Mikrotik RouterOS devices

Features:

* Templating config using Jinja2
* Built-in functions to assist in templating
* Full access to Netbox's underlying Django models
* Will SSH into RouterOS devices to apply configuration updates
* Smart diffing – Applies only the necessary commands to modify your device's configuraiton. No restart required
* View current device configuration, the generated templated configuration, and the diff to be applied
* Manage and edit configuration templates within Netbox
* Bulk apply changes to multiple devices

## Release process

```bash
export VERSION=a.b.c

poetry version $VERSION
dephell convert
black setup.py

git add .
git commit -m "Releasing version $VERSION"

git tag "v$VERSION"
git branch "v$VERSION"
git push origin \
    refs/tags/"v$VERSION" \
    refs/heads/"v$VERSION" \
    main

# Wait for CI to pass

poetry publish --build
```
