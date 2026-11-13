"""Stable back-to-front ordering for axial and sprite-anchored world drawables."""

class DepthSorter:
    """Sort axial cells or visual objects by their ground/depth anchor."""

    @staticmethod
    def sort(items, position_getter):
        return tuple(sorted(items, key=lambda item: (
            position_getter(item).r, position_getter(item).q,
        )))

    @staticmethod
    def sort_by_depth(items, depth_getter, stable_getter=None):
        """Sort by numeric ground depth with deterministic secondary ordering.

        Python's stable sort preserves input order when both keys are equal.
        Callers may supply an explicit stable key when input order is not
        guaranteed (for example, objects loaded from unordered content).
        """
        if stable_getter is None:
            return tuple(sorted(items, key=lambda item: depth_getter(item)))
        return tuple(sorted(items, key=lambda item: (
            depth_getter(item), stable_getter(item),
        )))
