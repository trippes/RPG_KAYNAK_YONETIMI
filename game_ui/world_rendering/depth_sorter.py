"""Stable back-to-front ordering for axial world drawables."""


class DepthSorter:
    """Sort objects by their axial screen-depth (row), then column."""

    @staticmethod
    def sort(items, position_getter):
        return tuple(sorted(
            items,
            key=lambda item: (
                position_getter(item).r,
                position_getter(item).q,
            ),
        ))
