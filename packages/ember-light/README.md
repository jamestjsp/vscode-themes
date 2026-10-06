# Ember Light

VS Code light theme using Monokai Pro Light’s pink-white surfaces, bright syntax palette, and italic type and parameter styling. Matching icons use original SVG artwork; their shapes differ from Monokai Pro’s icon font. All theme rules and SVG icons are newly authored.

## Install

1. In VS Code, open Extensions → `…` → **Install from VSIX…**.
2. Select `ember-light-0.2.0.vsix`.
3. Run **Preferences: Color Theme** → **Ember Light**.
4. Run **Preferences: File Icon Theme** → **Ember Light Icons**.

Both selections are independent; select both to enable the complete appearance.

## Palette

| Role | Color |
| --- | --- |
| Editor | `#faf4f2` |
| Text | `#29242a` |
| Keywords / coral | `#e14775` |
| Strings / amber | `#cc7a0a` |
| Functions / green | `#269d69` |
| Types / teal | `#1c8ca8` |
| Numbers / lavender | `#7058be` |

Includes semantic highlighting, terminal colors, Git and diff colors, muted italic comments, and icons for common languages, configuration, documents, and folders. Uses the editor’s font settings.

## Validate and package

```sh
uv run python3 -m unittest discover -s tests -v
uv run python3 build.py
```

Output: `dist/ember-light-0.2.0.vsix`. Python standard library only.
