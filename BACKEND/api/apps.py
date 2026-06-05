"""Configuración de la aplicación Django para el módulo api."""
from django.apps import AppConfig


class ApiConfig(AppConfig):
    """Configuración de la app 'api' de mortalidad y morbilidad materna."""

    name = 'api'

    def ready(self):
        """Configura psycopg2 para evitar doble parseo de JSONB.

        Django's JSONField llama json.loads() en from_db_value, pero
        psycopg2 ya convierte JSONB a dict antes de entregárselo a Django.
        Esto hace que from_db_value falle con TypeError. La solución es
        registrar un loads=identity en psycopg2 para que devuelva el
        string JSON crudo y Django lo parsee correctamente.
        """
        from django.db.backends.signals import connection_created

        def _configurar_json_psycopg2(sender, connection, **kwargs):
            if connection.vendor != 'postgresql':
                return
            try:
                import psycopg2.extras
                # Devolver JSON/JSONB como string crudo en lugar de dict
                psycopg2.extras.register_default_json(
                    connection.connection,
                    loads=lambda x: x,
                )
                psycopg2.extras.register_default_jsonb(
                    connection.connection,
                    loads=lambda x: x,
                )
            except Exception:
                pass

        connection_created.connect(_configurar_json_psycopg2)
