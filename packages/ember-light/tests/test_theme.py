import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest
import xml.etree.ElementTree as ET
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = json.loads((ROOT / "package.json").read_text())
THEME = json.loads((ROOT / PACKAGE["contributes"]["themes"][0]["path"]).read_text())
ICON_PATH = ROOT / PACKAGE["contributes"]["iconThemes"][0]["path"]
ICONS = json.loads(ICON_PATH.read_text())
REFERENCE = json.loads((ROOT / "tests/fixtures/monokai-pro-light-reference.json").read_text())


def contrast(first, second):
    def luminance(color):
        rgb = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        rgb = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in rgb]
        return sum(x * weight for x, weight in zip(rgb, (0.2126, 0.7152, 0.0722)))
    a, b = sorted((luminance(first), luminance(second)))
    return (b + 0.05) / (a + 0.05)


class ThemeTests(unittest.TestCase):
    def test_only_light_theme_and_icon_theme(self):
        self.assertEqual(len(PACKAGE["contributes"]["themes"]), 1)
        self.assertEqual(PACKAGE["contributes"]["themes"][0]["uiTheme"], "vs")
        self.assertEqual(THEME["type"], "light")
        self.assertEqual(len(PACKAGE["contributes"]["iconThemes"]), 1)
        self.assertNotIn("main", PACKAGE)
        self.assertNotIn("activationEvents", PACKAGE)

    def test_colors_and_foreground_readability(self):
        for key, value in THEME["colors"].items():
            self.assertRegex(value, r"^#[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?$", key)
        background = THEME["colors"]["editor.background"]
        self.assertGreaterEqual(contrast(THEME["colors"]["editor.foreground"], background), 10)
        for rule in THEME["tokenColors"]:
            self.assertTrue(rule["scope"])
            self.assertRegex(rule["settings"]["foreground"], r"^#[0-9a-f]{6}$", rule["name"])
        for token, value in THEME["semanticTokenColors"].items():
            color = value if isinstance(value, str) else value["foreground"]
            self.assertRegex(color, r"^#[0-9a-f]{6}$", token)

    def test_reference_workbench_and_syntax_palette(self):
        for key, expected in REFERENCE["ui"].items():
            self.assertEqual(THEME["colors"][key], expected, key)
        scopes = {scope: rule["settings"] for rule in THEME["tokenColors"] for scope in rule["scope"]}
        for scope, expected in REFERENCE["syntax"].items():
            for setting, value in expected.items():
                self.assertEqual(scopes[scope][setting], value, scope)
        self.assertNotIn("tab.activeBorderTop", THEME["colors"])
        self.assertEqual(THEME["colors"]["tab.activeBorder"], "#e14775")

    def test_semantic_highlighting_preserves_reference_roles(self):
        semantic = THEME["semanticTokenColors"]
        for token, scope in {
            "variable": "variable.other.property", "property": "variable.other.property",
            "operator": "keyword.operator", "keyword": "keyword", "string": "string",
            "number": "constant.numeric", "function": "entity.name.function",
            "method": "entity.name.function", "type": "entity.name.type",
            "parameter": "variable.parameter", "comment": "comment",
        }.items():
            value = semantic[token]
            color = value if isinstance(value, str) else value["foreground"]
            self.assertEqual(color, REFERENCE["syntax"][scope]["foreground"], token)
        self.assertTrue(semantic["parameter"]["italic"])
        self.assertTrue(semantic["comment"]["italic"])

    def test_core_syntax_and_semantic_coverage(self):
        self.assertTrue(THEME["semanticHighlighting"])
        scopes = {scope for rule in THEME["tokenColors"] for scope in rule["scope"]}
        for scope in ("comment", "keyword", "string", "constant.numeric", "entity.name.function", "entity.name.type", "variable.parameter"):
            self.assertIn(scope, scopes)
        for token in ("type", "parameter", "function", "method", "property", "number", "comment"):
            self.assertIn(token, THEME["semanticTokenColors"])

    def test_terminal_palette_matches_reference(self):
        for key, color in THEME["colors"].items():
            if key.startswith("terminal.ansi"):
                self.assertEqual(color, REFERENCE["ui"][key], key)

    def test_icon_references_and_svg_integrity(self):
        definitions = ICONS["iconDefinitions"]
        used = set()
        for key in ("file", "folder", "folderExpanded", "rootFolder", "rootFolderExpanded"):
            used.add(ICONS[key])
        for key in ("fileExtensions", "fileNames", "languageIds", "folderNames", "folderNamesExpanded"):
            used.update(ICONS[key].values())
        self.assertTrue(used <= definitions.keys())
        for identifier, definition in definitions.items():
            path = (ICON_PATH.parent / definition["iconPath"]).resolve()
            self.assertTrue(path.is_relative_to(ROOT), identifier)
            tree = ET.parse(path)
            self.assertEqual(tree.getroot().tag, "{http://www.w3.org/2000/svg}svg")
            self.assertEqual(tree.getroot().get("viewBox"), "0 0 24 24")
            self.assertNotRegex(path.read_text(), r"<(script|image)\b|https?://(?!www\.w3\.org)")
            for element in tree.iter():
                stroke = element.get("stroke")
                if stroke and re.fullmatch(r"#[0-9A-Fa-f]{6}", stroke):
                    self.assertEqual(stroke, REFERENCE["icons"][identifier], identifier)
        for folder, icon in ICONS["folderNames"].items():
            self.assertEqual(ICONS["folderNamesExpanded"][folder], icon + "-open")

    def test_common_file_associations(self):
        for extension in ("go", "py", "js", "ts", "tsx", "json", "yaml", "md", "svg", "rs", "sql"):
            self.assertIn(extension, ICONS["fileExtensions"])
        for name in ("Dockerfile", ".gitignore", ".env", "go.mod", "package.json", "LICENSE"):
            self.assertIn(name, ICONS["fileNames"])

    def test_vsix_contains_all_assets_and_matching_metadata(self):
        spec = importlib.util.spec_from_file_location("build", ROOT / "build.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            with ZipFile(module.build(directory)) as archive:
                self.assertIsNone(archive.testzip())
                manifest = ET.fromstring(archive.read("extension.vsixmanifest"))
                ns = {"v": module.VSIX_NS}
                identity = manifest.find("v:Metadata/v:Identity", ns)
                for attribute, field in (("Id", "name"), ("Version", "version"), ("Publisher", "publisher")):
                    self.assertEqual(identity.get(attribute), PACKAGE[field])
                self.assertEqual(json.loads(archive.read("extension/package.json")), PACKAGE)
                for group in ("themes", "iconThemes"):
                    for contribution in PACKAGE["contributes"][group]:
                        self.assertIn("extension/" + contribution["path"].removeprefix("./"), archive.namelist())
                for definition in ICONS["iconDefinitions"].values():
                    source = (ICON_PATH.parent / definition["iconPath"]).resolve()
                    self.assertIn("extension/" + source.relative_to(ROOT).as_posix(), archive.namelist())
                ET.fromstring(archive.read("[Content_Types].xml"))


if __name__ == "__main__":
    unittest.main()
