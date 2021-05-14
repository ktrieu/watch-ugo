# watch-ugo

## Commands:

## `vid-def`

This command creates a video definition JSON from a Wikipedia URL, or a random article if no URL is specified.

This command takes two arguments:

- `--url [URL]`: specifies the URL of the Wikipedia article to take the list items from. Must be in the format "https://en.wikipedia.org/wiki/List_of_<...>". If not specified, WatchUGO will select an article at random
- `--out [file]`: specifies the name of the file to output the video definition JSON to. If not specified, WatchUGO will select a filename based on the article title.

## `render`

This command creates a rendered video from a video definition JSON.

This command takes two arguments:
- `[file]`: specifies the name of the video JSON file to create the video from.
- `--out [file]`: specifies the name of the file to output the video to. If not specified, WatchUGO will select a video name based on the input JSON filename.
