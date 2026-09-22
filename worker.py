"""Cloudflare Python Worker entry point for the Chic Interiors Flask app."""
from workers import WorkerEntrypoint, wsgi

from app import app, configure_worker


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        # Apply Worker secrets such as SECRET_KEY before Flask reads the session.
        configure_worker(self.env)
        return await wsgi.fetch(app, request, self.env)
