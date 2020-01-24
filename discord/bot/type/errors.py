class Errors:
    no_results_found = "No Results found."
    default = "An Error has occurred."
    info_check = "An Error has occurred while checking Info."
    spotify_pull = (
        "**There was an error pulling the Playlist, 0 Songs were added. "
        "This may be caused by the playlist being private or deleted.**"
    )
    cant_reach_youtube = (
        "Can't reach YouTube. Server Error on their side maybe?"
    )
    youtube_url_invalid = "This YouTube Url is invalid."
    youtube_video_not_available = (
        "The requested YouTube Video is not available."
    )
    error_please_retry = "error_please_retry"
    backend_down = (
        "Our backend seems to be down right now, try again in a few minutes."
    )

    @staticmethod
    def as_list():
        l = []
        for att in Errors.__dict__:
            if isinstance(Errors.__dict__[att], list):
                l.append(Errors.__dict__[att])
        return l
