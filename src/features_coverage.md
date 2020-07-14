# Instumentation Tests "Geiler-Musik-Bot"

## Summary:

**Percentage of Coverage: 76%** 26/34

## Details:

> Playing Songs

| Feature                | Covered with Test | Test Name        |
| ---------------------- | ----------------- | ---------------- |
| youtube url            | True              | youtube_url      |
| youtube playlist       | True              | youtube_playlist |
| spotify track          | True              | spotify_track    |
| spotify album          | True              | spotify_album    |
| spotify artist         | True              | spotify_artist   |
| spotify playlist       | True              | spotify_playlist |
| term search            | True              | youtube_term     |
| user is not in channel | True              | NaN              |
| queue a song           | True              | queue            |

> Pause a song

| Feature                       | Covered with Test | Test Name    |
| ----------------------------- | ----------------- | ------------ |
| pause                         | True              | test_pause   |
| pause when nothing is playing | True              | test_pause_b |
| pause when already paused     | True              | test_pause   |

> Resume a song

| Feature                        | Covered with Test | Test Name    |
| ------------------------------ | ----------------- | ------------ |
| resume                         | True              | test_unpause |
| resume when nothing is playing | True              | test_resume  |
| resume when nothing is playing | True              | test_pause_b |

> Skip a song

| Feature                      | Covered with Test | Test Name |
| ---------------------------- | ----------------- | --------- |
| skip                         | True              | test_skip |
| skip multiple                | False             | NaN       |
| skip when nothing is running | True              | test_skip |

> Special Play

| Feature  | Covered with Test | Test Name |
| -------- | ----------------- | --------- |
| PlaySkip | False             | NaN       |
| PlayNext | False             | NaN       |

> Stop

| Feature                      | Covered with Test | Test Name |
| ---------------------------- | ----------------- | --------- |
| Stop                         | False             | NaN       |
| Stop when nothing is playing | False             | NaN       |

> Info

| Feature | Covered with Test | Test Name |
| ------- | ----------------- | --------- |
| Info    | False             | NaN       |

> Queue

| Feature          | Covered with Test | Test Name        |
| ---------------- | ----------------- | ---------------- |
| show queue       | True              | test_queue_full  |
| show empty queue | True              | test_queue_empty |

> Clear queue

| Feature                        | Covered with Test | Test Name |
| ------------------------------ | ----------------- | --------- |
| Clear Queue                    | False             | NaN       |
| Clear Queue when already empty | False             | NaN       |

> Shuffle Queue

| Feature            | Covered with Test | Test Name          |
| ------------------ | ----------------- | ------------------ |
| Shuffle            | True              | test_shuffle       |
| Shuffle when empty | True              | test_shuffle_empty |

> Other

| Feature                   | Covered with Test | Test Name              |
| ------------------------- | ----------------- | ---------------------- |
| User not in channel check | True              | test_nobody_in_channel |

# Unit Tests "Geiler-Musik-Bot"

## Details

> RegEX

| Feature                    | Covered with Test | Test Name |
| -------------------------- | ----------------- | --------- |
| Spotify URL Verification   | True              | unit      |
| Spotify URI Verification   | True              | unit      |
| YouTube URL Verification   | True              | unit      |
| YouTube Title Verification | True              | unit      |