class Errors:
    no_results_found = "No Results found."
    default = "An Error has occurred."
    info_check = "An Error has occurred while checking Info."
    spotify_pull = (
        "**There was an error pulling the Spotify Playlist, 0 Songs were added.**"
    )
    cant_reach_youtube = "Can't reach YouTube. Server Error on their side maybe?"
    youtube_url_invalid = "This YouTube Url is invalid."
    youtube_video_not_available = "The requested YouTube Video is not available."
    error_please_retry = "error_please_retry"

    @staticmethod
    def as_list():
        l = []
        for att in Errors.__dict__:
            if type(Errors.__dict__[att]) == list:
                l.append(Errors.__dict__[att])
        return l
