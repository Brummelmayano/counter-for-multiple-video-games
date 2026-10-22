"""Zoom tools used while reading frames. Sheets are written to build/zoom/ and their paths printed.

usage: python -m playend.annotation.zoom TOOL SESSION IDS [options]

SESSION is a capture session: its folder name, its id or a unique start of the id (fdb795).
IDS are frame ids, for example 199-264 or 12,15,20-30.

  grid    3x3 contact sheets, to tell the game and the type of screen
  mini    6x6 contact sheets, to screen a whole session quickly
  crop    one zoomed region of every frame: --box X0 Y0 X1 Y1 [--scale 2]
  names   the two fighter-name bars: --band Y0 Y1 (default 22 42)
  GAME    the HUD regions of one game, see the module of that game for what each crop shows;
          --layout picks one when the game has several (Beach Buggy: 3, 4, 2; Fortnite: split, solo, multi, og)

--cols and --rows change how many frames go on one sheet.
"""

import argparse

from . import beach_buggy, dragon_ball, fortnite, jstars, mortal_kombat, tekken, ufc, warzone
from .layout import Crop, Layout, contact_sheets, crop_sheets, parse_ids

GAMES = {
    "beach-buggy": beach_buggy,
    "dragon-ball": dragon_ball,
    "fortnite": fortnite,
    "jstars": jstars,
    "mortal-kombat": mortal_kombat,
    "tekken": tekken,
    "ufc": ufc,
    "warzone": warzone,
}


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m playend.annotation.zoom",
        description=__doc__.split("\n")[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("\n\n", 2)[2],
    )
    parser.add_argument("tool", choices=["grid", "mini", "crop", "names", *GAMES])
    parser.add_argument("session")
    parser.add_argument("ids", type=parse_ids)
    parser.add_argument("--cols", type=int)
    parser.add_argument("--rows", type=int)
    parser.add_argument("--box", type=int, nargs=4, metavar=("X0", "Y0", "X1", "Y1"))
    parser.add_argument("--scale", type=float, default=2.0)
    parser.add_argument("--band", type=int, nargs=2, metavar=("Y0", "Y1"), default=(22, 42))
    parser.add_argument("--layout")
    args = parser.parse_args()

    if args.tool == "grid":
        sheets = contact_sheets("grid", args.session, args.ids, cols=3, width=426, height=240, quality=92)
    elif args.tool == "mini":
        sheets = contact_sheets("mini", args.session, args.ids, cols=6, width=252, height=142, quality=80)
    elif args.tool == "crop":
        if not args.box:
            parser.error("crop needs --box X0 Y0 X1 Y1")
        x0, y0 = args.box[:2]
        layout = Layout((Crop(tuple(args.box), args.scale),), rows=12)
        sheets = crop_sheets("crop", args.session, args.ids, layout, args.cols, args.rows, suffix=f"_{x0}_{y0}")
    elif args.tool == "names":
        y0, y1 = args.band
        layout = Layout((Crop((150, y0, 300, y1)), Crop((1030, y0, 1180, y1))), cols=4, rows=60)
        sheets = crop_sheets("names", args.session, args.ids, layout, args.cols, args.rows)
    else:
        layouts = GAMES[args.tool].LAYOUTS
        name = args.layout or next(iter(layouts))
        if name not in layouts:
            parser.error(f"{args.tool} layouts: {', '.join(layouts)}")
        tool = args.tool if len(layouts) == 1 else f"{args.tool}-{name}"
        sheets = crop_sheets(tool, args.session, args.ids, layouts[name], args.cols, args.rows)
    print("\n".join(str(path) for path in sheets))


if __name__ == "__main__":
    main()
