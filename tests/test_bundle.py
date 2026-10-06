import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = json.loads((ROOT / "package.json").read_text())
spec = importlib.util.spec_from_file_location("build", ROOT / "build.py")
BUILD = importlib.util.module_from_spec(spec)
spec.loader.exec_module(BUILD)


class BundleTests(unittest.TestCase):
    def test_two_light_themes_and_icons(self):
        themes = PACKAGE["contributes"]["themes"]
        self.assertEqual([theme["label"] for theme in themes], ["Ember Light", "AIUX Light"])
        for theme in themes:
            self.assertEqual(theme["uiTheme"], "vs")
            self.assertEqual(json.loads((ROOT / theme["path"]).read_text())["type"], "light")
        icons = PACKAGE["contributes"]["iconThemes"]
        self.assertEqual(len(icons), 1)
        self.assertEqual(icons[0]["id"], "ember-light-icons")
        self.assertEqual(PACKAGE["publisher"], "jamestjsp")
        self.assertEqual(PACKAGE["repository"]["url"], "https://github.com/jamestjsp/vscode-themes.git")
        self.assertNotIn("main", PACKAGE)

    def test_bundle_contains_original_assets_and_licenses(self):
        with tempfile.TemporaryDirectory() as directory:
            with ZipFile(BUILD.build(directory)) as archive:
                self.assertIsNone(archive.testzip())
                package = json.loads(archive.read("extension/package.json"))
                self.assertEqual(package, PACKAGE)
                for kind in ("themes", "iconThemes"):
                    for theme in package["contributes"][kind]:
                        name = "extension/" + theme["path"].removeprefix("./")
                        self.assertEqual(archive.read(name), (ROOT / theme["path"]).read_bytes())
                icons_path = ROOT / package["contributes"]["iconThemes"][0]["path"]
                icons = json.loads(icons_path.read_text())
                for definition in icons["iconDefinitions"].values():
                    asset = (icons_path.parent / definition["iconPath"]).resolve()
                    name = "extension/" + asset.relative_to(ROOT).as_posix()
                    self.assertEqual(archive.read(name), asset.read_bytes())
                for name in ("LICENSE", "THIRD_PARTY_NOTICES.md", "packages/aiux-light/LICENSE", "packages/ember-light/LICENSE"):
                    self.assertIn("extension/" + name, archive.namelist())
                excluded = ("tests/", "build.py", ".git", ".DS_Store", "__pycache__")
                for name in archive.namelist():
                    self.assertFalse(any(fragment in name for fragment in excluded), name)
                    self.assertFalse(name.endswith(".vsix"), name)

    def test_standalone_packages_keep_extension_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            for name in ("ember-light", "aiux-light"):
                project = ROOT / "packages" / name
                original = json.loads((project / "package.json").read_text())
                with ZipFile(BUILD.build(directory, project)) as archive:
                    self.assertEqual(json.loads(archive.read("extension/package.json")), original)
                    manifest = ET.fromstring(archive.read("extension.vsixmanifest"))
                    identity = manifest.find("{*}Metadata/{*}Identity")
                    self.assertEqual(identity.get("Publisher"), original["publisher"])
                    self.assertEqual(identity.get("Id"), original["name"])


if __name__ == "__main__":
    unittest.main()
