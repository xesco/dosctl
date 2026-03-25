"""Tests for lib/decorators.py."""
from unittest.mock import patch, MagicMock

from dosctl.lib.decorators import ensure_cache


class TestEnsureCache:
    def test_setup_sequence(self):
        """Creates dirs, builds collection, and loads cache before calling the wrapped fn."""
        @ensure_cache
        def cmd(collection, **kwargs):
            pass

        mock_collection = MagicMock()
        with patch("dosctl.lib.decorators.ensure_dirs_exist") as mock_dirs, \
             patch("dosctl.lib.decorators.create_collection", return_value=mock_collection) as mock_create:
            cmd()

        mock_dirs.assert_called_once()
        mock_create.assert_called_once()
        mock_collection.ensure_cache_is_present.assert_called_once_with()

    def test_passes_collection_as_first_argument(self):
        received = []

        @ensure_cache
        def cmd(collection, **kwargs):
            received.append(collection)

        mock_collection = MagicMock()
        with patch("dosctl.lib.decorators.ensure_dirs_exist"), \
             patch("dosctl.lib.decorators.create_collection", return_value=mock_collection):
            cmd()

        assert received == [mock_collection]

    def test_returns_inner_function_result(self):
        @ensure_cache
        def cmd(collection, **kwargs):
            return "result"

        mock_collection = MagicMock()
        with patch("dosctl.lib.decorators.ensure_dirs_exist"), \
             patch("dosctl.lib.decorators.create_collection", return_value=mock_collection):
            assert cmd() == "result"
