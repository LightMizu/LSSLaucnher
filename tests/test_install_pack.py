import sys
import types
import unittest
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

if "loguru" not in sys.modules:
    loguru_module = types.ModuleType("loguru")

    class _Logger:
        def info(self, *args, **kwargs):
            pass

        def warning(self, *args, **kwargs):
            pass

        def error(self, *args, **kwargs):
            pass

        def success(self, *args, **kwargs):
            pass

        def debug(self, *args, **kwargs):
            pass

    loguru_module.logger = _Logger()
    sys.modules["loguru"] = loguru_module

if "requests" not in sys.modules:
    requests_module = types.ModuleType("requests")

    class _RequestException(Exception):
        pass

    requests_module.exceptions = types.SimpleNamespace(
        RequestException=_RequestException
    )
    requests_module.get = lambda *args, **kwargs: None
    requests_module.post = lambda *args, **kwargs: None
    sys.modules["requests"] = requests_module

if "psutil" not in sys.modules:
    psutil_module = types.ModuleType("psutil")
    psutil_module.process_iter = lambda *args, **kwargs: []
    sys.modules["psutil"] = psutil_module

if "aiohttp" not in sys.modules:
    aiohttp_module = types.ModuleType("aiohttp")

    class _ClientPayloadError(Exception):
        pass

    class _ClientTimeout:
        def __init__(self, *args, **kwargs):
            pass

    class _ClientSession:
        def __init__(self, *args, **kwargs):
            pass

    aiohttp_module.ClientPayloadError = _ClientPayloadError
    aiohttp_module.ClientTimeout = _ClientTimeout
    aiohttp_module.ClientSession = _ClientSession
    sys.modules["aiohttp"] = aiohttp_module

from utils.dota_patcher import DOTA_MOD_FOLDER
from utils.install_pack import CustomPackInstallError, install_pack


class InstallPackTests(unittest.TestCase):
    def test_install_single_vpk_keeps_legacy_destination_name(self):
        with TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            packs_dir = base / "packs"
            packs_dir.mkdir()
            (packs_dir / "legacy-pack").write_bytes(b"legacy-vpk")

            dota_path = base / "dota"
            mod_dir = dota_path / "game" / DOTA_MOD_FOLDER
            mod_dir.mkdir(parents=True)
            (mod_dir / "old_file.vpk").write_bytes(b"old")

            with patch("utils.install_pack.APP_DATA_PATH", str(packs_dir)), patch(
                "utils.install_pack.patch_d"
            ) as patch_d:
                install_pack("legacy-pack", dota_path, api=None)

            patch_d.assert_called_once_with(dota_path=str(dota_path))
            self.assertEqual(sorted(path.name for path in mod_dir.iterdir()), ["pak01_dir.vpk"])
            self.assertEqual((mod_dir / "pak01_dir.vpk").read_bytes(), b"legacy-vpk")

    def test_install_zip_extracts_all_vpk_files(self):
        with TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            packs_dir = base / "packs"
            packs_dir.mkdir()
            zip_path = packs_dir / "custom-pack.zip"
            with zipfile.ZipFile(zip_path, "w") as archive:
                archive.writestr("nested/main.vpk", b"main-bytes")
                archive.writestr("nested/deeper/extra.VPK", b"extra-bytes")
                archive.writestr("nested/readme.txt", b"ignore me")

            dota_path = base / "dota"
            mod_dir = dota_path / "game" / DOTA_MOD_FOLDER
            mod_dir.mkdir(parents=True)
            (mod_dir / "old_file.vpk").write_bytes(b"old")

            with patch("utils.install_pack.APP_DATA_PATH", str(packs_dir)), patch(
                "utils.install_pack.patch_d"
            ) as patch_d:
                install_pack("custom-pack.zip", dota_path, api=None)

            patch_d.assert_called_once_with(dota_path=str(dota_path))
            self.assertEqual(
                sorted(path.name for path in mod_dir.iterdir()),
                ["extra.VPK", "main.vpk"],
            )
            self.assertEqual((mod_dir / "main.vpk").read_bytes(), b"main-bytes")
            self.assertEqual((mod_dir / "extra.VPK").read_bytes(), b"extra-bytes")

    def test_install_zip_without_vpk_keeps_existing_files(self):
        with TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            packs_dir = base / "packs"
            packs_dir.mkdir()
            zip_path = packs_dir / "broken-pack.zip"
            with zipfile.ZipFile(zip_path, "w") as archive:
                archive.writestr("nested/readme.txt", b"no vpk here")

            dota_path = base / "dota"
            mod_dir = dota_path / "game" / DOTA_MOD_FOLDER
            mod_dir.mkdir(parents=True)
            old_vpk = mod_dir / "old_file.vpk"
            old_vpk.write_bytes(b"old")

            with patch("utils.install_pack.APP_DATA_PATH", str(packs_dir)), patch(
                "utils.install_pack.patch_d"
            ):
                with self.assertRaises(CustomPackInstallError):
                    install_pack("broken-pack.zip", dota_path, api=None)

            self.assertTrue(old_vpk.exists())
            self.assertEqual(old_vpk.read_bytes(), b"old")

    def test_install_corrupted_zip_keeps_existing_files(self):
        with TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            packs_dir = base / "packs"
            packs_dir.mkdir()
            zip_path = packs_dir / "corrupted-pack.zip"
            with zipfile.ZipFile(
                zip_path, "w", compression=zipfile.ZIP_STORED
            ) as archive:
                archive.writestr("nested/main.vpk", b"valid-data" * 128)

            data = bytearray(zip_path.read_bytes())
            for i in range(50, len(data) - 50):
                if data[i] not in (0, 255):
                    data[i] ^= 1
                    break
            zip_path.write_bytes(data)

            dota_path = base / "dota"
            mod_dir = dota_path / "game" / DOTA_MOD_FOLDER
            mod_dir.mkdir(parents=True)
            old_vpk = mod_dir / "old_file.vpk"
            old_vpk.write_bytes(b"old")

            with patch("utils.install_pack.APP_DATA_PATH", str(packs_dir)), patch(
                "utils.install_pack.patch_d"
            ):
                with self.assertRaises(CustomPackInstallError):
                    install_pack("corrupted-pack.zip", dota_path, api=None)

            self.assertTrue(old_vpk.exists())
            self.assertEqual(old_vpk.read_bytes(), b"old")


if __name__ == "__main__":
    unittest.main()
