"""Tests for collections/factory.py."""
import pytest

from dosctl.collections.factory import create_collection, get_available_collections


class TestCreateCollection:
    def test_creates_known_collection(self, tmp_path):
        collection = create_collection(
            "tdc_release_14",
            source="https://example.com",
            cache_dir=str(tmp_path),
        )
        assert collection is not None

    def test_raises_for_unknown_type_with_helpful_message(self, tmp_path):
        with pytest.raises(ValueError) as exc_info:
            create_collection("bad_type", source="https://example.com", cache_dir=str(tmp_path))
        assert "bad_type" in str(exc_info.value)
        assert "tdc_release_14" in str(exc_info.value)


class TestGetAvailableCollections:
    def test_includes_tdc_release_14(self):
        assert "tdc_release_14" in get_available_collections()
