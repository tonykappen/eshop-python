"""OTEL baggage helpers (inject/extract)."""

import logging

logger = logging.getLogger(__name__)


class BaggageManager:
    """OTEL baggage management utilities."""

    @staticmethod
    def extract_baggage(headers: dict[str, str]) -> dict[str, str]:
        """
        Extract baggage from HTTP headers.

        Args:
            headers: HTTP headers dictionary

        Returns:
            Dictionary of baggage key-value pairs
        """
        baggage_header = headers.get("baggage", "")
        if not baggage_header:
            return {}

        baggage = {}
        # Parse W3C baggage format: key1=value1,key2=value2
        for item in baggage_header.split(","):
            if "=" in item:
                key, value = item.split("=", 1)
                baggage[key.strip()] = value.strip()

        return baggage

    @staticmethod
    def inject_baggage(baggage: dict[str, str]) -> str:
        """
        Inject baggage into HTTP header format.

        Args:
            baggage: Dictionary of baggage key-value pairs

        Returns:
            W3C baggage header string
        """
        if not baggage:
            return ""

        items = [f"{key}={value}" for key, value in baggage.items()]
        return ",".join(items)

    @staticmethod
    def get_baggage_value(
        baggage: dict[str, str], key: str, default: str | None = None
    ) -> str | None:
        """
        Get a baggage value by key.

        Args:
            baggage: Baggage dictionary
            key: Baggage key
            default: Default value if key not found

        Returns:
            Baggage value or default
        """
        return baggage.get(key, default)
