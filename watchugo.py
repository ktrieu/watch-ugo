import argparse
import os

import vid_def
import render
import wiki_api


def subcommand_build_video_def(args):
    if args.url is not None:
        url = args.url
    else:
        title = wiki_api.get_random_list_article()
        url = wiki_api.get_url_from_article_title(title)
        print(f"Selected article {title} ({url}).")
    video_def = vid_def.video_def_from_list_url(url)
    vid_def.save_video_def(video_def, args.out)


def get_default_output_path(input_path: str):
    return os.path.splitext(input_path)[0] + ".mp4"


def subcommand_render_video(args):
    video_def = render.load_video_def_from_file(args.file)
    clip = render.render_video_def(video_def)
    if args.out is None:
        args.out = f"{vid_def.get_video_def_file_name(video_def)}.mp4"
    render.save_file(args.out, clip)
    print(f"Video saved to {args.out}")
    print(f"Video title:\n {video_def.title}\n")
    print(f"Video description:\n {video_def.description}\n")


def subcommand_full(args):
    if args.url is not None:
        url = args.url
    else:
        title = wiki_api.get_random_list_article()
        url = wiki_api.get_url_from_article_title(title)
        print(f"Selected article {title} ({url}).")
    video_def = vid_def.video_def_from_list_url(url)
    if len(video_def.segments) == 0:
        print("Found zero video segments for URL. Exiting...")
        return

    clip = render.render_video_def(video_def)
    if args.out is None:
        args.out = f"{vid_def.get_video_def_file_name(video_def)}.mp4"
    render.save_file(args.out, clip)


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
        "--url",
        type=str,
        default=None,
        help="The URL of the Wikipedia list article. If not specified, a random article will be selected.",
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
        "--out",
        type=str,
        default=None,
        help="The output path for the video file.",
    )
    render_vid_parser.set_defaults(command=subcommand_render_video)

    full_parser = subparsers.add_parser(
        "full",
        help="Render a video from a Wikipedia list article. Combines the vid-def and render commands.",
        description="Render a video from a Wikipedia list article. Combines the vid-def and render commands.",
    )
    full_parser.set_defaults(command=subcommand_full)
    full_parser.add_argument(
        "--url",
        type=str,
        default=None,
        help="The URL of the Wikipedia list article. If not specified, a random article will be selected.",
    )
    full_parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="The output path for the video.",
    )

    return parser


if __name__ == "__main__":
    parser = setup_argparser()
    args = parser.parse_args()

    args.command(args)
