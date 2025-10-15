# Keycloak Setup - Quick Guide

> **📍 Location:** All Keycloak documentation is now in `infra/keycloak/`

## Quick Start

```bash
# 1. Copy credentials template
cp infra/keycloak/credentials.yaml.example infra/keycloak/credentials.yaml

# 2. Edit with your credentials
nano infra/keycloak/credentials.yaml

# 3. Provision Keycloak
cd backend
python scripts/provision_keycloak.py
```

## Documentation

All Keycloak documentation has been organized into `infra/keycloak/`:

- **[Full Setup Guide](infra/keycloak/README.md)** - Complete provisioning documentation
- **[Quick Reference](infra/keycloak/QUICK_REFERENCE.md)** - Common commands and examples
- **[Credentials Template](infra/keycloak/credentials.yaml.example)** - YAML configuration template

## Features

✅ **No hardcoded credentials** - All configuration in YAML file  
✅ **Realm admin provisioning** - Realm admin creates application resources  
✅ **CLI tool** - Easy provisioning with validation  
✅ **Auto-provision** - Optional startup provisioning  

## File Structure

```
infra/keycloak/
├── README.md                   # Full documentation
├── QUICK_REFERENCE.md          # Quick reference
├── credentials.yaml.example    # Template (copy this)
├── credentials.yaml            # Your credentials (DO NOT COMMIT)
├── credentials.py              # Credentials loader
└── keycloak_setup.py           # Provisioning logic

backend/
├── scripts/
│   └── provision_keycloak.py   # CLI provisioning tool
└── app/
    └── core/
        └── auth/
            └── rbac.py         # RBAC with provisioning utilities
```

## Need Help?

- **Full documentation**: [infra/keycloak/README.md](infra/keycloak/README.md)
- **Quick reference**: [infra/keycloak/QUICK_REFERENCE.md](infra/keycloak/QUICK_REFERENCE.md)
- **Validate config**: `cd backend && python scripts/provision_keycloak.py --validate`
- **Show config**: `cd backend && python scripts/provision_keycloak.py --show-config`

---

**Note:** This is a quick guide. For complete documentation including troubleshooting, security best practices, and advanced usage, see [infra/keycloak/README.md](infra/keycloak/README.md).

