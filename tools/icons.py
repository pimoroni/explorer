import argparse
import contextlib
import io
import pathlib
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
APPS = ROOT / "filesystem" / "apps"
FONTS = ROOT / "romfs" / "fonts"
BADGEWARE_FONTS = ROOT.parent / "badgeware" / "badgeware-fonts"
DEFAULT_SYMBOLS = BADGEWARE_FONTS / "roboto-medium-with-material-symbols" / "src" / "MaterialSymbolsSharp_Filled-Regular.ttf"
DEFAULT_ALRIGHT_FONTS = BADGEWARE_FONTS / "alright-fonts"
FALLBACK = "apps"
FLAG_16BIT_POINT_COUNT = 0b0000001
QUALITY = 5


def icon_names():
    names = {FALLBACK}
    for path in sorted(APPS.glob("*.py")):
        for line in path.read_text().splitlines()[:20]:
            if line.startswith("Icon:"):
                names.add(line[5:].strip())
    return sorted(names)


def main():
    parser = argparse.ArgumentParser(description="Build romfs/fonts/icons.af and icons.txt from the Material Symbols named by each app's Icon: line.")
    parser.add_argument("--symbols", type=pathlib.Path, default=DEFAULT_SYMBOLS, help="Material Symbols .ttf")
    parser.add_argument("--alright-fonts", type=pathlib.Path, default=DEFAULT_ALRIGHT_FONTS, help="alright-fonts checkout")
    args = parser.parse_args()

    sys.path.insert(0, str(args.alright_fonts))
    import freetype
    from python_alright_fonts import Encoder

    face = freetype.Face(str(args.symbols))
    codepoints = {face.get_glyph_name(index).decode(): codepoint for codepoint, index in face.get_chars() if codepoint >= 0xE000}
    names = icon_names()
    missing = [name for name in names if name not in codepoints]
    if missing:
        sys.exit(f"Not in {args.symbols.name}: {', '.join(missing)}")

    with open(args.symbols, "rb") as symbols, open(args.symbols, "rb") as icons, contextlib.redirect_stdout(io.StringIO()):
        encoder = Encoder(symbols, icons, quality=QUALITY)
        for name in names:
            encoder.get_glyph(codepoints[name])

    font = b"af!?"
    font += struct.pack(">HHHH", FLAG_16BIT_POINT_COUNT, len(encoder.glyphs), encoder.total_path_count(), encoder.total_point_count())
    for packer in (encoder.get_packed_glyph, encoder.get_packed_glyph_paths, encoder.get_packed_glyph_path_points):
        for glyph in encoder.glyphs.values():
            font += packer(glyph)

    (FONTS / "icons.af").write_bytes(font)
    (FONTS / "icons.txt").write_text("".join(f"{name} {codepoints[name]:04x}\n" for name in names))
    print(f"{len(names)} icons, {len(font)} bytes -> {FONTS / 'icons.af'}")


if __name__ == "__main__":
    main()
