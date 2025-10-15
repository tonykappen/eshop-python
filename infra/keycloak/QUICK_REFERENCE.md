# Keycloak Provisioning - Quick Reference

> **Location:** All Keycloak documentation and configuration is in `infra/keycloak/`

## Quick Start (3 Steps)

```bash
# 1. Copy and edit credentials file
cp infra/keycloak/credentials.yaml.example infra/keycloak/credentials.yaml
nano infra/keycloak/credentials.yaml

# 2. Validate
cd backend
python scripts/provision_keycloak.py --validate

# 3. Provision
python scripts/provision_keycloak.py
```

## CLI Commands

```bash
# Provision with default file
python scripts/provision_keycloak.py

# Provision with specific file
python scripts/provision_keycloak.py /path/to/credentials.yaml

# Validate only (no provisioning)
python scripts/provision_keycloak.py --validate

# Show current configuration
python scripts/provision_keycloak.py --show-config
```

## Environment Variables

```bash
# .env file
KEYCLOAK_SERVER_URL=http://localhost:8080
KEYCLOAK_REALM=eshop
KEYCLOAK_CREDENTIALS_PATH=infra/keycloak/credentials.yaml  # Optional - uses default search
KEYCLOAK_AUTO_PROVISION=false                              # true for dev only
```

## Python Code

```python
from app.core.auth.rbac import (
    provision_keycloak_sync,
    provision_keycloak_async,
    validate_credentials_file,
    load_credentials_config,
)

# Synchronous (scripts)
success = provision_keycloak_sync()

# Asynchronous (FastAPI)
success = await provision_keycloak_async()

# Validate
is_valid, msg = validate_credentials_file()

# Load config
config = load_credentials_config()
```

## Credentials File Structure

```yaml
master_admin:
  username: admin
  password: admin

realm_admin:
  username: realm-admin
  email: admin@eshop.com
  password: secure-password
  first_name: Realm
  last_name: Admin

clients:
  - client_id: eshop-api
    client_secret: your-secret
    redirect_uris: ["http://localhost:8000/*"]
    web_origins: ["http://localhost:8000"]

roles:
  - name: user
    description: "Basic user"
  - name: admin
    description: "Admin user"

users:
  - username: testuser
    email: test@example.com
    password: password123
    first_name: Test
    last_name: User
    roles: [user]

role_hierarchy:
  admin:
    includes: [user]
```

## Testing Authentication

```bash
# Get token
curl -X POST "http://localhost:8080/realms/eshop/protocol/openid-connect/token" \
  -d "username=testuser" \
  -d "password=password123" \
  -d "grant_type=password" \
  -d "client_id=eshop-api" \
  -d "client_secret=your-secret"

# Use token
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/protected-endpoint
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| File not found | Check `KEYCLOAK_CREDENTIALS_PATH` or create `infra/keycloak/credentials.yaml` |
| Master admin failed | Verify Keycloak is running: `docker ps \| grep keycloak` |
| Invalid YAML | Validate syntax: `yamllint infra/keycloak/credentials.yaml` |
| Role assignment failed | System retries automatically; check Keycloak logs |

## Security Checklist

- [ ] Never commit `infra/keycloak/credentials.yaml` (it's in `.gitignore`)
- [ ] Use strong passwords (not defaults like "admin/admin")
- [ ] Set file permissions: `chmod 600 infra/keycloak/credentials.yaml`
- [ ] Disable auto-provision in production: `KEYCLOAK_AUTO_PROVISION=false`
- [ ] Use different credentials files per environment
- [ ] Consider secret management for production (AWS Secrets Manager, Vault)

## File Locations

```
Project Root/
├── infra/
│   └── keycloak/
│       ├── README.md                    # Full documentation (this is the main guide)
│       ├── QUICK_REFERENCE.md           # This file
│       ├── credentials.yaml.example     # Template (copy this)
│       ├── credentials.yaml             # Your credentials (DO NOT COMMIT)
│       ├── credentials.py               # Credentials loader
│       └── keycloak_setup.py            # Provisioning logic
├── backend/
│   ├── scripts/
│   │   └── provision_keycloak.py        # CLI provisioning script
│   └── app/
│       ├── config/
│       │   └── settings.py              # Settings with credential path
│       └── core/
│           └── auth/
│               └── rbac.py              # Provisioning utilities (RBAC integration)
├── .gitignore                           # Contains credentials patterns
└── README.md                            # Main project README (links to Keycloak docs)
```

## Integration with RBAC

```python
# In your FastAPI routes
from app.core.auth.rbac import require_command_access, require_query_access

# Protect write operations (admin/manager only)
@router.post("/products")
async def create_product(
    user: KeycloakUser = Depends(require_command_access())
):
    pass

# Protect read operations (admin/manager/user)
@router.get("/products")
async def list_products(
    user: KeycloakUser = Depends(require_query_access())
):
    pass
```

## Auto-Provision on Startup

```python
# In app/main.py
from app.config.settings import settings
from app.core.auth.rbac import provision_keycloak_async

@app.on_event("startup")
async def startup():
    if settings.keycloak_auto_provision:
        logger.info("🔧 Auto-provisioning Keycloak...")
        success = await provision_keycloak_async()
        if success:
            logger.info("✅ Keycloak provisioned successfully")
```

## Installation

```bash
# Install dependencies
cd backend
poetry install

# Or with pip
pip install pyyaml>=6.0.0

# Make script executable (Unix/Mac)
chmod +x scripts/provision_keycloak.py
```

## Documentation Links

- **Full Guide**: [README.md](README.md) in this directory (comprehensive documentation)
- **Template**: [credentials.yaml.example](credentials.yaml.example) (copy and customize)
- **Main Project**: [../../README.md](../../README.md) (project overview)
- **Keycloak Docs**: https://www.keycloak.org/documentation

---

**Need Help?**
- **Full documentation**: See [README.md](README.md) in this directory
- **Check logs**: `backend/logs/app.log`
- **Validate file**: `cd backend && python scripts/provision_keycloak.py --validate`
- **Show config**: `cd backend && python scripts/provision_keycloak.py --show-config`

