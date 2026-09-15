"""Tests for the S3-compatible collection backend."""
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from dosctl.collections.factory import create_collection, get_available_collections
from dosctl.collections.s3 import S3Collection

LIST_XML = """<?xml version="1.0" encoding="UTF-8"?>
<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
  <Name>games</Name>
  <IsTruncated>false</IsTruncated>
  <Contents><Key>1993/Doom (1993)(id Software).zip</Key><Size>100</Size></Contents>
  <Contents><Key>SHAREWARE.ZIP</Key><Size>50</Size></Contents>
  <Contents><Key>notes.txt</Key><Size>3</Size></Contents>
</ListBucketResult>
"""

TRUNCATED_XML = """<?xml version="1.0" encoding="UTF-8"?>
<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
  <Name>games</Name>
  <IsTruncated>true</IsTruncated>
  <NextContinuationToken>tok-1</NextContinuationToken>
  <Contents><Key>a (1990).zip</Key></Contents>
</ListBucketResult>
"""

SECOND_PAGE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
  <Name>games</Name>
  <IsTruncated>false</IsTruncated>
  <Contents><Key>b (1992).zip</Key></Contents>
</ListBucketResult>
"""


def _response(text, status=200):
    response = Mock()
    response.status_code = status
    response.text = text
    response.raise_for_status = Mock()
    if status >= 400:
        def raise_error():
            import requests
            raise requests.exceptions.HTTPError(f"{status} error")
        response.raise_for_status.side_effect = raise_error
    return response


def _make_zip(path: Path, members=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as zf:
        for name, content in (members or {"GAME.EXE": "fake game"}).items():
            zf.writestr(name, content)


def _expected_id(key: str) -> str:
    import hashlib
    return hashlib.sha1(key.encode()).hexdigest()[:8]


class TestSourceParsing:
    def test_aws_virtual_host_style(self):
        collection = S3Collection("s3://dosgames", "/tmp/cache")
        assert collection._base_url == "https://dosgames.s3.amazonaws.com"
        assert collection.bucket == "dosgames"
        assert collection.prefix == ""
        assert collection.collection_name == "dosgames"

    def test_aws_with_prefix(self):
        collection = S3Collection("s3://dosgames/zip/release", "/tmp/cache")
        assert collection._base_url == "https://dosgames.s3.amazonaws.com"
        assert collection.prefix == "zip/release"

    def test_custom_endpoint_path_style(self):
        collection = S3Collection("s3+https://minio.local:9000/games", "/tmp/cache")
        assert collection._base_url == "https://minio.local:9000/games"
        assert collection.bucket == "games"
        assert collection.prefix == ""

    def test_custom_endpoint_http(self):
        collection = S3Collection("s3+http://minio.local:9000/games/doom", "/tmp/cache")
        assert collection._base_url == "http://minio.local:9000/games"
        assert collection.prefix == "doom"

    @pytest.mark.parametrize("source", [
        "s3://",
        "s3+https://host-only",
        "s3+ftp://host/bucket",
        "https://host/bucket",
    ])
    def test_invalid_source_raises(self, source):
        with pytest.raises(ValueError, match="Invalid S3 source"):
            S3Collection(source, "/tmp/cache")


class TestListing:
    def test_ensure_cache_is_present_lists_and_writes_catalog(self, capsys):
        with tempfile.TemporaryDirectory() as cache_dir:
            with patch("requests.get", return_value=_response(LIST_XML)) as mock_get:
                collection = S3Collection("s3://dosgames", cache_dir)
                collection.ensure_cache_is_present()

            output = capsys.readouterr().out
            assert mock_get.call_args.args[0] == "https://dosgames.s3.amazonaws.com/"
            assert mock_get.call_args.kwargs["params"] == {"list-type": "2"}
            assert "Downloading game list from" in output
            assert "✅ Game list refreshed successfully." in output

            cache_file = Path(cache_dir) / "games.txt"
            doom_id = _expected_id("1993/Doom (1993)(id Software).zip")
            share_id = _expected_id("SHAREWARE.ZIP")
            assert cache_file.read_text(encoding="utf-8") == (
                f"{doom_id}\tDoom (1993)(id Software)\t1993\t1993/Doom (1993)(id Software).zip\n"
                f"{share_id}\tSHAREWARE\t\tSHAREWARE.ZIP\n"
            )

    def test_ensure_cache_is_present_skips_when_cached(self):
        with tempfile.TemporaryDirectory() as cache_dir:
            (Path(cache_dir) / "games.txt").write_text("existing")
            with patch("requests.get") as mock_get:
                collection = S3Collection("s3://dosgames", cache_dir)
                collection.ensure_cache_is_present()

            mock_get.assert_not_called()
            assert collection.get_games() == []

    def test_force_refresh_relists(self, capsys):
        with tempfile.TemporaryDirectory() as cache_dir:
            (Path(cache_dir) / "games.txt").write_text("")
            with patch("requests.get", return_value=_response(LIST_XML)):
                collection = S3Collection("s3://dosgames", cache_dir)
                collection.ensure_cache_is_present(force_refresh=True)

            assert collection.get_games()

    def test_list_follows_pagination(self):
        with tempfile.TemporaryDirectory() as cache_dir:
            responses = [_response(TRUNCATED_XML), _response(SECOND_PAGE_XML)]
            with patch("requests.get", side_effect=responses) as mock_get:
                collection = S3Collection("s3://dosgames", cache_dir)
                collection.ensure_cache_is_present()

            first_params = mock_get.call_args_list[0].kwargs["params"]
            second_params = mock_get.call_args_list[1].kwargs["params"]
            assert "continuation-token" not in first_params
            assert second_params["continuation-token"] == "tok-1"

            keys = sorted(g["full_path"] for g in collection.get_games())
            assert keys == ["a (1990).zip", "b (1992).zip"]

    def test_list_sends_prefix_when_set(self):
        with tempfile.TemporaryDirectory() as cache_dir:
            with patch("requests.get", return_value=_response(LIST_XML)) as mock_get:
                collection = S3Collection("s3://dosgames/zip", cache_dir)
                collection.ensure_cache_is_present()

            assert mock_get.call_args.kwargs["params"] == {"list-type": "2", "prefix": "zip"}

    def test_list_error_raises_click_exception(self):
        with tempfile.TemporaryDirectory() as cache_dir:
            with patch("requests.get", return_value=_response(LIST_XML, status=403)):
                collection = S3Collection("s3://dosgames", cache_dir)
                with pytest.raises(Exception, match="Could not list games"):
                    collection.ensure_cache_is_present()


class TestLookupAndDownload:
    def _collection(self, cache_dir):
        collection = S3Collection("s3://dosgames", cache_dir)
        collection._games_data = [{
            "id": _expected_id("1993/Doom (1993)(id Software).zip"),
            "name": "Doom (1993)(id Software)",
            "year": "1993",
            "full_path": "1993/Doom (1993)(id Software).zip",
        }]
        return collection

    def test_find_game_by_id(self):
        with tempfile.TemporaryDirectory() as cache_dir:
            collection = self._collection(cache_dir)
            game = collection.find_game(_expected_id("1993/Doom (1993)(id Software).zip"))
            assert game is not None
            assert game["name"] == "Doom (1993)(id Software)"
            assert collection.find_game("00000000") is None

    def test_download_url_quotes_the_key(self):
        with tempfile.TemporaryDirectory() as cache_dir:
            collection = self._collection(cache_dir)
            url = collection.get_download_url(_expected_id("1993/Doom (1993)(id Software).zip"))
            assert url == (
                "https://dosgames.s3.amazonaws.com/"
                "1993/Doom%20%281993%29%28id%20Software%29.zip"
            )

    def test_download_url_unknown_id(self):
        with tempfile.TemporaryDirectory() as cache_dir:
            assert self._collection(cache_dir).get_download_url("00000000") is None

    def test_download_game_streams_to_destination(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir) / "cache"
            downloads_dir = Path(temp_dir) / "downloads"
            collection = self._collection(str(cache_dir))

            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            mock_response.headers = {"content-length": "6"}
            mock_response.iter_content = Mock(return_value=[b"doom 6"])
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=None)

            with patch("requests.get", return_value=mock_response) as mock_get:
                result = collection.download_game(
                    _expected_id("1993/Doom (1993)(id Software).zip"), str(downloads_dir))

            assert mock_get.call_args.args[0] == (
                "https://dosgames.s3.amazonaws.com/"
                "1993/Doom%20%281993%29%28id%20Software%29.zip"
            )
            expected_path = downloads_dir / "Doom (1993)(id Software).zip"
            assert result == expected_path
            assert expected_path.read_bytes() == b"doom 6"

    def test_download_game_unknown_id(self):
        with tempfile.TemporaryDirectory() as cache_dir:
            collection = self._collection(cache_dir)
            with pytest.raises(FileNotFoundError, match="not found"):
                collection.download_game("00000000", "/tmp/unused")

    def test_download_game_skips_existing_file(self, capsys):
        with tempfile.TemporaryDirectory() as temp_dir:
            downloads_dir = Path(temp_dir) / "downloads"
            downloads_dir.mkdir()
            existing = downloads_dir / "Doom (1993)(id Software).zip"
            existing.write_bytes(b"already here")

            collection = self._collection(temp_dir)
            with patch("requests.get") as mock_get:
                result = collection.download_game(
                    _expected_id("1993/Doom (1993)(id Software).zip"), str(downloads_dir))

            mock_get.assert_not_called()
            assert result == existing
            assert existing.read_bytes() == b"already here"
            assert "Use --force to overwrite" in capsys.readouterr().out

    def test_download_game_rejects_truncated_download(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            downloads_dir = Path(temp_dir) / "downloads"
            collection = self._collection(temp_dir)

            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            mock_response.headers = {"content-length": "100"}
            mock_response.iter_content = Mock(return_value=[b"only 6"])
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=None)

            with patch("requests.get", return_value=mock_response):
                result = collection.download_game(
                    _expected_id("1993/Doom (1993)(id Software).zip"), str(downloads_dir))

            assert result is None
            assert not (downloads_dir / "Doom (1993)(id Software).zip").exists()


class TestUnzip:
    def test_unzip_game_unpacks_the_downloaded_zip(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            downloads_dir = temp_path / "downloads"
            downloads_dir.mkdir()
            _make_zip(downloads_dir / "Doom (1993)(id Software).zip")

            collection = S3Collection("s3://dosgames", temp_dir)
            collection._games_data = [{
                "id": "abc12345",
                "name": "Doom (1993)(id Software)",
                "year": "1993",
                "full_path": "1993/Doom (1993)(id Software).zip",
            }]
            install_path = temp_path / "installed" / "abc12345"

            collection.unzip_game("abc12345", downloads_dir, install_path)

            assert (install_path / "GAME.EXE").read_text() == "fake game"

    def test_unzip_game_unknown_id(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            collection = S3Collection("s3://dosgames", temp_dir)
            with pytest.raises(FileNotFoundError, match="not found"):
                collection.unzip_game("00000000", Path(temp_dir), Path(temp_dir) / "x")


class TestS3Factory:
    def test_create_collection(self):
        with tempfile.TemporaryDirectory() as cache_dir:
            collection = create_collection("s3", "s3://dosgames", cache_dir)

        assert isinstance(collection, S3Collection)
        assert "s3" in get_available_collections()


class TestColAddTypeInference:
    def _inferred_type(self, source):
        from dosctl.commands import col

        with patch.object(col, "add_collection") as mock_add:
            col.col_add.callback("name", source, None)
        return mock_add.call_args.args[1]

    @pytest.mark.parametrize("source", [
        "s3://dosgames",
        "s3://dosgames/prefix",
        "s3+https://minio.local:9000/games",
        "s3+http://minio.local/games",
    ])
    def test_s3_uris_default_to_s3(self, source):
        assert self._inferred_type(source) == "s3"

    @pytest.mark.parametrize("source", [
        "https://archive.org/x",
        tempfile.gettempdir(),
    ])
    def test_other_sources_keep_their_defaults(self, source):
        assert self._inferred_type(source) in ("local_file", "tdc_release_14")
