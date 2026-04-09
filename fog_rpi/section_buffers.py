"""
Section Buffers
===============
Maintains a separate sliding-window buffer of gas readings for each
leaf RPi (section). The chained gas model needs ~36 readings of history
before it can make its first prediction, so each section accumulates
readings independently.
"""

from gas_model import WINDOW_SIZE


class SectionBuffers:
    """In-memory buffers for each section's recent gas readings."""

    def __init__(self):
        self._buffers = {}  # section_id -> list of reading dicts
        self._max_size = WINDOW_SIZE * 2  # bounded to prevent unbounded growth

    def append(self, section_id, reading):
        """
        Add a reading to this section's buffer.

        Parameters:
            section_id: MongoDB ObjectId string identifying the section
            reading: dict with at least 'ppm' and 'voltage' keys
        """
        if section_id not in self._buffers:
            self._buffers[section_id] = []

        self._buffers[section_id].append(reading)

        # Trim to prevent unbounded growth
        if len(self._buffers[section_id]) > self._max_size:
            self._buffers[section_id] = self._buffers[section_id][-self._max_size:]

    def get(self, section_id):
        """Return the buffer list for a section (empty list if none)."""
        return self._buffers.get(section_id, [])

    def size(self, section_id):
        """Return the current number of readings for a section."""
        return len(self._buffers.get(section_id, []))
