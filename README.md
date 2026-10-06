# Light Themes

Ember Light and AIUX Light in one VS Code extension, with Ember’s original file icons.

| Theme | Appearance |
| --- | --- |
| **Ember Light** | Monokai Pro Light palette, pink-white surfaces, colorful syntax, italic types and parameters |
| **AIUX Light** | ServiceNow Lux Lab’s original light theme, preserved unchanged |
| **Ember Light Icons** | Original SVG file and folder icons; usable with either theme |

## Install on another computer

1. Download **light-themes-1.0.0.vsix** from the [latest release](https://github.com/jamestjsp/vscode-themes/releases/latest).
2. In VS Code, run **Extensions: Install from VSIX…** and select the downloaded file.
3. Run **Preferences: Color Theme** and select **Ember Light** or **AIUX Light**.
4. For icons, run **Preferences: File Icon Theme** and select **Ember Light Icons**.

Or install from a terminal:

```sh
code --install-extension light-themes-1.0.0.vsix
```

One download installs both themes and the icons. Separate Ember and AIUX VSIX files are also available in the release. GitHub releases distribute the VSIX files; updates are installed manually.

## Development

Python 3.10 or newer; no third-party Python dependencies.

```sh
uv run python3 -m unittest discover -s tests -v
uv run python3 -m unittest discover -s packages/ember-light/tests -v
uv run python3 build.py --all
```

`dist/` contains the combined VSIX, both standalone VSIX files, and `SHA256SUMS`.

Source lives in `packages/ember-light/` and `packages/aiux-light/`. Both standalone packages keep their existing extension IDs and versions. The combined extension ID is `jamestjsp.light-themes`.

## License

MIT. See [third-party notices](THIRD_PARTY_NOTICES.md) and the preserved per-theme licenses.
