"""Opening content used by the executable."""

from application.content_pack import populate_opening_content


def create_opening_service(game):
    service, _ = populate_opening_content(game)
    return service
