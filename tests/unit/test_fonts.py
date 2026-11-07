import tempfile
from pathlib import Path

import pytest
import shadlet as ui
from shadlet.fonts import FontManager


def test_font_registration_and_css(tmp_path: Path) -> None:
    font = tmp_path / "inter.woff2"
    font.write_bytes(b"font")
    manager = FontManager()
    face = manager.register(
        "Inter",
        source=str(font),
        weight="100 900",
        style="normal",
        display="swap",
        preload=True,
        fallback=("system-ui",),
        unicode_range="U+0000-00FF",
        feature_settings='"kern" 1',
    )
    assert face.family == "Inter"
    assert manager.preload_urls == [str(font).replace("\\", "/")]
    css = manager.css()
    assert "@font-face" in css
    assert 'font-family: "Inter"' in css
    assert "font-weight: 100 900" in css
    assert "unicode-range: U+0000-00FF" in css


def test_duplicate_font_registration_raises(tmp_path: Path) -> None:
    font = tmp_path / "inter.woff2"
    font.write_bytes(b"font")
    app = ui.App()
    app.fonts.register("Inter", source=str(font))
    with pytest.raises(ValueError, match="already registered"):
        app.fonts.register("Inter", source=str(font))


def test_missing_font_raises(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="does not exist"):
        FontManager().register("Missing", source=str(tmp_path / "missing.woff2"))


def test_invalid_weight_raises() -> None:
    with pytest.raises(ValueError):
        FontManager().register("Bad", source="/fonts/bad.woff2", weight="10000")
    with pytest.raises(ValueError):
        FontManager().register("Bad", source="/fonts/bad.woff2", weight="900 100")


def test_italic_and_variable_range() -> None:
    face = FontManager().register(
        "Italic",
        source="/fonts/italic.woff2",
        weight="300 700",
        style="italic",
    )
    assert face.style == "italic"
    assert face.weight == "300 700"
    assert "font-style: italic" in face.to_css()


def test_theme_font_configuration() -> None:
    app = ui.App()
    app.theme.configure(
        font_family="Inter",
        heading_font="Geist",
        mono_font_family="Geist Mono",
        tokens={"--accent": "red"},
    )
    variables = app.theme.css_variables()
    assert "Geist" in variables["--font-heading"]
    assert "Geist Mono" in variables["--font-mono"]
    assert variables["--accent"] == "red"
    assert str(app.theme) == "light"


def test_app_init_message_includes_fonts() -> None:
    import asyncio

    app = ui.App()
    font_path = Path(tempfile.mkdtemp()) / "inter.woff2"
    font_path.write_bytes(b"font")
    app.fonts.register("Inter", source=str(font_path), preload=True)
    app.theme.configure(font_family="Inter")

    messages: list[dict[str, object]] = []

    async def send(message: dict[str, object]) -> None:
        messages.append(message)

    async def run() -> None:

        ui.Session(app, send_json=send) if False else None

    # Use the real Session class.
    from shadlet.runtime.session import Session

    async def main() -> None:
        session = Session(app, send_json=send)
        await session.send_init()
        assert messages[0]["type"] == "init"
        assert "fonts_css" in messages[0]
        assert messages[0]["font_preloads"]
        await session.close()

    asyncio.run(main())
