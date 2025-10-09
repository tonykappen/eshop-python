#!/usr/bin/env python3
"""Test script to verify Seq logging integration."""

import asyncio
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.config.settings import settings
from app.core.logging.logger import configure_logging, get_logger


async def test_seq_logging():
    """Test Seq logging integration."""
    print("🧪 Testing Seq Logging Integration")
    print(f"📊 Seq URL: {settings.seq_url}")
    print(f"🔑 Seq API Key: {settings.seq_api_key}")
    print(f"📝 Log Level: {settings.log_level}")
    print(f"✅ Seq Enabled: {settings.log_enable_seq}")
    
    # Configure logging
    configure_logging(
        log_level=settings.log_level,
        log_format="json",
        enable_seq=settings.log_enable_seq,
        seq_url=settings.seq_url,
        seq_api_key=settings.seq_api_key,
        enable_file_logging=True,
        log_directory="logs",
        separate_server_logs=True,
    )
    
    # Get logger
    logger = get_logger("seq_test")
    
    # Test different log levels
    print("\n📝 Sending test logs to Seq...")
    
    logger.info("🧪 Test info message", test_type="integration", service="eshop")
    logger.warning("⚠️ Test warning message", test_type="integration", service="eshop")
    logger.error("❌ Test error message", test_type="integration", service="eshop")
    
    # Test structured logging
    logger.info(
        "🎯 Structured log test",
        user_id="test-user-123",
        action="login",
        ip_address="192.168.1.100",
        user_agent="test-agent/1.0",
        test_type="structured",
    )
    
    # Test performance logging
    logger.info(
        "⚡ Performance test",
        operation="database_query",
        duration_ms=45.2,
        rows_returned=150,
        test_type="performance",
    )
    
    # Test error logging with exception
    try:
        raise ValueError("Test exception for Seq logging")
    except Exception as e:
        logger.error(
            "🔥 Exception test",
            error=str(e),
            error_type=type(e).__name__,
            test_type="exception",
        )
    
    print("✅ Test logs sent to Seq!")
    print(f"🌐 Check Seq UI at: {settings.seq_url}")
    print("🔍 Look for logs with 'test_type' field to find these test messages")
    print("👤 Seq Admin Login: admin / admin123")


if __name__ == "__main__":
    asyncio.run(test_seq_logging())








