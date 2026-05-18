#!/usr/bin/env python3
"""CLI script to provision Keycloak from credentials file.

Usage:
    python scripts/provision_keycloak.py [credentials_path]

Examples:
    # Use default credentials file location
    python scripts/provision_keycloak.py

    # Use specific credentials file
    python scripts/provision_keycloak.py /path/to/keycloak_credentials.yaml

    # Validate credentials file without provisioning
    python scripts/provision_keycloak.py --validate

    # Show current credentials configuration
    python scripts/provision_keycloak.py --show-config
"""

import sys
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse

from app.core.auth.rbac import (load_credentials_config,
                                provision_keycloak_sync,
                                validate_credentials_file)
from app.core.logging.base_logger import BaseLogger

logger = BaseLogger(__name__)


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Provision Keycloak from credentials file"
    )
    parser.add_argument(
        "credentials_path",
        nargs="?",
        help="Path to credentials file (optional, uses default search locations if not provided)",
    )
    parser.add_argument(
        "--validate",
        "-v",
        action="store_true",
        help="Validate credentials file without provisioning",
    )
    parser.add_argument(
        "--show-config",
        "-s",
        action="store_true",
        help="Show current credentials configuration",
    )

    args = parser.parse_args()

    # Handle --show-config
    if args.show_config:
        print("\n📋 Current Keycloak Credentials Configuration\n")
        print("=" * 60)
        try:
            config = load_credentials_config(args.credentials_path)
            if not config:
                print("❌ Failed to load credentials configuration")
                return 1

            print("\n👤 Realm Admin:")
            print(f"   Username: {config.get('realm_admin', {}).get('username')}")
            print(f"   Email:    {config.get('realm_admin', {}).get('email')}")

            print(f"\n🔐 Clients ({len(config.get('clients', []))}):")
            for client in config.get("clients", []):
                print(f"   • {client['client_id']}")
                print(f"     Redirect URIs: {', '.join(client['redirect_uris'])}")

            print(f"\n🎭 Roles ({len(config.get('roles', []))}):")
            for role in config.get("roles", []):
                print(f"   • {role['name']}: {role['description']}")

            print(f"\n👥 Users ({len(config.get('users', []))}):")
            for user in config.get("users", []):
                print(f"   • {user['username']} ({user['email']})")
                print(f"     Roles: {', '.join(user['roles'])}")

            print("\n🏗️  Role Hierarchy:")
            for parent_role, hierarchy in config.get("role_hierarchy", {}).items():
                print(
                    f"   • {parent_role} includes: {', '.join(hierarchy['includes'])}"
                )

            print("\n" + "=" * 60)
            return 0
        except Exception as e:
            print(f"❌ Error loading configuration: {e}")
            return 1

    # Handle --validate
    if args.validate:
        print("\n🔍 Validating Keycloak credentials file...\n")
        is_valid, message = validate_credentials_file(args.credentials_path)
        if is_valid:
            print(f"✅ {message}")
            return 0
        else:
            print(f"❌ {message}")
            return 1

    # Provision Keycloak
    print("\n🚀 Starting Keycloak provisioning...\n")
    print("=" * 60)

    if args.credentials_path:
        print(f"📁 Using credentials file: {args.credentials_path}")
    else:
        print("📁 Using default credentials file search locations")

    print("=" * 60)
    print()

    # First validate the credentials file
    is_valid, message = validate_credentials_file(args.credentials_path)
    if not is_valid:
        print(f"❌ Validation failed: {message}")
        print("\nProvisioning aborted. Please fix the credentials file and try again.")
        return 1

    print(f"✅ Validation passed: {message}\n")

    # Provision Keycloak
    success = provision_keycloak_sync(args.credentials_path)

    print("\n" + "=" * 60)
    if success:
        print("✅ Keycloak provisioning completed successfully!")
        print("\nYou can now use the provisioned users to authenticate:")
        print("  - Check the credentials file for usernames and passwords")
        print("  - Use the Keycloak admin console to manage users/roles")
        print("=" * 60)
        return 0
    else:
        print("❌ Keycloak provisioning failed!")
        print("\nPlease check the logs above for error details.")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
