import argparse


def subcommand_build_video_def(args):
    print("Building video definition...")
    print(args)


def subcommand_render_video(args):
    print("Rendering video...")
    print(args)


def subcommand_full(args):
    print("Doing everything...")
    print(args)


def setup_argparser():
    parser = argparse.ArgumentParser(
        description="Create a WatchUGO video from a Wikipedia list article."
    )

    subparsers = parser.add_subparsers(required=True, dest="command")
    video_def_parser = subparsers.add_parser(
        "vid-def",
        help="Build video definition file(s) from a Wikipedia list article.",
        description="Build video definition file(s) from a Wikipedia list article.",
    )
    video_def_parser.add_argument(
        "url", type=str, help="The URL of the Wikipedia list article."
    )
    video_def_parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="The output path for the video definition file(s).",
    )
    video_def_parser.set_defaults(command=subcommand_build_video_def)

    render_vid_parser = subparsers.add_parser(
        "render",
        help="Render a video from a video definition file.",
        description="Render a video from a video definition file.",
    )
    render_vid_parser.add_argument(
        "file", type=str, help="The location of the video definition file."
    )
    render_vid_parser.add_argument(
        "--out", type=str, default=None, help="The output path for the video file.",
    )
    render_vid_parser.set_defaults(command=subcommand_render_video)

    return parser


if __name__ == "__main__":
    parser = setup_argparser()
    args = parser.parse_args()

    args.command(args)
