"""Opening content used by the executable."""

from application.content_pack import populate_opening_content


def create_opening_service(game, content_package_path=None):
    service, _ = populate_opening_content(game, content_package_path=content_package_path)
    return service
