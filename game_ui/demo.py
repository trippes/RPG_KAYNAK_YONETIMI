"""Deterministic content used by the vertical-slice executable."""

from application.content_pack import populate_demo_content, populate_opening_content


def create_demo_service(game):
    service, _ = populate_demo_content(game)
    return service


def create_opening_service(game):
    service, _ = populate_opening_content(game)
    return service
