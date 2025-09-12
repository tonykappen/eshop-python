#!/usr/bin/env python3
"""Test script for environment variable fallback system."""

from app.config.env import get_all_env, get_env, get_env_bool, get_env_int, has_env


def test_env_fallback():
    """Test the environment variable fallback system."""
    print("🔍 Testing Environment Variable Fallback System")
    print("=" * 60)

    # Test key environment variables
    test_vars = [
        "DATABASE_URL",
        "REDIS_URL",
        "RABBITMQ_URL",
        "KEYCLOAK_SERVER_URL",
        "SEQ_URL",
        "SEQ_API_KEY",
        "LOG_ENABLE_SEQ",
        "LOG_LEVEL",
    ]

    print("\n📋 Environment Variable Values:")
    for var in test_vars:
        try:
            value = get_env(var, "NOT_FOUND")
            source = "launch.json" if has_env(var) else "default"
            print(f"  {var}: {value} (source: {source})")
        except Exception as e:
            print(f"  {var}: ERROR - {e}")

    print("\n🔧 Boolean Environment Variables:")
    bool_vars = ["LOG_ENABLE_SEQ", "DEBUG", "LOG_ENABLE_FILE"]
    for var in bool_vars:
        try:
            value = get_env_bool(var, False)
            print(f"  {var}: {value}")
        except Exception as e:
            print(f"  {var}: ERROR - {e}")

    print("\n🔢 Integer Environment Variables:")
    int_vars = ["PORT", "DB_PORT", "REDIS_PORT"]
    for var in int_vars:
        try:
            value = get_env_int(var, 0)
            print(f"  {var}: {value}")
        except Exception as e:
            print(f"  {var}: ERROR - {e}")

    print("\n🌐 All Environment Variables:")
    all_env = get_all_env()
    for key, value in sorted(all_env.items()):
        if any(
            service in key.lower()
            for service in ["database", "redis", "rabbitmq", "keycloak", "seq", "log"]
        ):
            print(f"  {key}: {value}")

    print("\n✅ Environment Fallback Test Complete!")


if __name__ == "__main__":
    test_env_fallback()

