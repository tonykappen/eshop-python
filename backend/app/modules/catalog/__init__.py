"""Catalog bounded context package.

Seeder registration and outbox worker wiring are performed at application
startup through the bootstrap lifecycle, not via import side effects here.
"""
