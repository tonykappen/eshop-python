"""Catalog bounded context package.

Default catalog data seeding is registered from ``initialize_dependency_injection``
(see ``register_default_application_seeders``). Outbox worker wiring uses the
catalog bootstrap lifecycle, not import side effects in this package.
"""
