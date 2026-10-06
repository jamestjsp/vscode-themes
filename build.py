import json
from pathlib import Path
import xml.etree.ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parent
VSIX_NS = "http://schemas.microsoft.com/developer/vsx-schema/2011"
CONTENT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"


def build(output_dir=None, project_dir=None):
    project = Path(project_dir).resolve() if project_dir else ROOT
    package = json.loads((project / "package.json").read_text())
    output = Path(output_dir) if output_dir else ROOT / "dist"
    output.mkdir(parents=True, exist_ok=True)
    target = output / f"{package['name']}-{package['version']}.vsix"
    manifest = ET.Element("PackageManifest", Version="2.0.0", xmlns=VSIX_NS)
    metadata = ET.SubElement(manifest, "Metadata")
    ET.SubElement(metadata, "Identity", {
        "Language": "en-US", "Id": package["name"],
        "Version": package["version"], "Publisher": package["publisher"],
    })
    ET.SubElement(metadata, "DisplayName").text = package["displayName"]
    ET.SubElement(metadata, "Description").text = package["description"]
    ET.SubElement(metadata, "Categories").text = "Themes"
    properties = ET.SubElement(metadata, "Properties")
    for key, value in {
        "Microsoft.VisualStudio.Code.Engine": package["engines"]["vscode"],
        "Microsoft.VisualStudio.Code.ExecutesCode": "false",
    }.items():
        ET.SubElement(properties, "Property", Id=key, Value=value)
    ET.SubElement(metadata, "License").text = "extension/LICENSE"
    install = ET.SubElement(manifest, "Installation")
    ET.SubElement(install, "InstallationTarget", Id="Microsoft.VisualStudio.Code")
    ET.SubElement(manifest, "Dependencies")
    assets = ET.SubElement(manifest, "Assets")
    for kind, path in {
        "Microsoft.VisualStudio.Code.Manifest": "package.json",
        "Microsoft.VisualStudio.Services.Content.Details": "README.md",
        "Microsoft.VisualStudio.Services.Content.License": "LICENSE",
    }.items():
        ET.SubElement(assets, "Asset", Type=kind, Path=f"extension/{path}", Addressable="true")
    content = ET.Element("Types", xmlns=CONTENT_NS)
    for suffix, mime in {
        "json": "application/json", "svg": "image/svg+xml",
        "md": "text/markdown", "vsixmanifest": "text/xml",
    }.items():
        ET.SubElement(content, "Default", Extension=suffix, ContentType=mime)
    ET.SubElement(content, "Override", PartName="/extension/LICENSE", ContentType="text/plain")
    sources = {project / name for name in ("package.json", "README.md", "LICENSE")}
    for name in ("THIRD_PARTY_NOTICES.md",):
        if (project / name).exists():
            sources.add(project / name)
    for kind in ("themes", "iconThemes"):
        for contribution in package["contributes"].get(kind, []):
            theme_path = (project / contribution["path"]).resolve()
            sources.add(theme_path)
            if kind == "iconThemes":
                icons = json.loads(theme_path.read_text())
                for definition in icons["iconDefinitions"].values():
                    sources.add((theme_path.parent / definition["iconPath"]).resolve())
    for source in tuple(sources):
        if not source.resolve().is_relative_to(project):
            raise ValueError(f"Asset outside project: {source}")
        if not source.is_file():
            raise ValueError(f"Missing asset: {source}")
    if project == ROOT:
        for license_path in (ROOT / "packages").glob("*/LICENSE"):
            sources.add(license_path)
    with ZipFile(target, "w", ZIP_DEFLATED) as archive:
        archive.writestr("extension.vsixmanifest", ET.tostring(manifest, encoding="utf-8", xml_declaration=True))
        archive.writestr("[Content_Types].xml", ET.tostring(content, encoding="utf-8", xml_declaration=True))
        for source in sorted(sources):
            archive.write(source, "extension/" + source.relative_to(project).as_posix())
    return target


if __name__ == "__main__":
    import argparse
    import hashlib

    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="Build standalone themes too")
    args = parser.parse_args()
    outputs = [build()]
    if args.all:
        outputs.extend(build(project_dir=ROOT / "packages" / name) for name in ("ember-light", "aiux-light"))
    sums = []
    for output in outputs:
        sums.append(f"{hashlib.sha256(output.read_bytes()).hexdigest()}  {output.name}")
        print(output)
    (ROOT / "dist" / "SHA256SUMS").write_text("\n".join(sums) + "\n")
