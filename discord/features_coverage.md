# Instumentation Tests "Geiler-Musik-Bot"

## Summary:

**Percentage of Coverage: 30%**

## Details:

> Playing Songs

| Feature                | Covered with Test | Test Name |
| ---------------------- | ----------------- | --------- |
| youtube url            | False             | NaN       |
| youtube playlist       | False             | NaN       |
| spotify track          | False             | NaN       |
| spotify album          | False             | NaN       |
| spotify artist         | False             | NaN       |
| spotify playlist       | False             | NaN       |
| term search            | False             | NaN       |
| user is not in channel | False             | NaN       |
| queue a song           | False             | NaN       |
| queue a playlist       | False             | NaN       |

> Pause a song

| Feature                       | Covered with Test | Test Name    |
| ----------------------------- | ----------------- | ------------ |
| Pause                         | True              | test_pause   |
| pause when nothing is playing | True              | test_pause_b |
| pause when already paused     | True              | test_pause   |

> Resume a song

| Feature                        | Covered with Test | Test Name    |
| ------------------------------ | ----------------- | ------------ |
| Resume                         | True              | test_unpause |
| resume when nothing is playing | True              | test_resume  |
| resume when nothing is playing | True              | test_pause_b |

> Skip a song

| Feature                      | Covered with Test | Test Name |
| ---------------------------- | ----------------- | --------- |
| Skip                         | True              | test_skip |
| Skip multiple                | False             | NaN       |
| Skip when nothing is running | True              | test_skip |

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

| Feature          | Covered with Test | Test Name |
| ---------------- | ----------------- | --------- |
| show queue       | False             | NaN       |
| show empty queue | False             | NaN       |

> Clear queue

| Feature                        | Covered with Test | Test Name |
| ------------------------------ | ----------------- | --------- |
| Clear Queue                    | False             | NaN       |
| Clear Queue when already empty | False             | NaN       |

> Shuffle Queue

| Feature            | Covered with Test | Test Name |
| ------------------ | ----------------- | --------- |
| Shuffle            | False             | NaN       |
| Shuffle when empty | False             | NaN       |

> Other

| Feature                   | Covered with Test | Test Name              |
| ------------------------- | ----------------- | ---------------------- |
| User not in channel check | True              | test_nobody_in_channel |

# Unit Tests "Geiler-Musik-Bot"

## Details

> RegEX

| Feature | Covered with Test | Test Name |
| ------- | ----------------- | --------- |
| Spotify URL Verification | True | tba |
| Spotify URI Verification | True | tba |
| YouTube URL Verification | True | tba |
| YouTube Title Verification | True | tba |
# Instumentation Tests "Geiler-Musik-Bot"

## Summary:

**Percentage of Coverage: 30%**

## Details:

> Playing Songs

| Feature                | Covered with Test | Test Name |
| ---------------------- | ----------------- | --------- |
| youtube url            | False             | NaN       |
| youtube playlist       | False             | NaN       |
| spotify track          | False             | NaN       |
| spotify album          | False             | NaN       |
| spotify artist         | False             | NaN       |
| spotify playlist       | False             | NaN       |
| term search            | False             | NaN       |
| user is not in channel | False             | NaN       |
| queue a song           | False             | NaN       |
| queue a playlist       | False             | NaN       |

> Pause a song

| Feature                       | Covered with Test | Test Name    |
| ----------------------------- | ----------------- | ------------ |
| Pause                         | True              | test_pause   |
| pause when nothing is playing | True              | test_pause_b |
| pause when already paused     | True              | test_pause   |

> Resume a song

| Feature                        | Covered with Test | Test Name    |
| ------------------------------ | ----------------- | ------------ |
| Resume                         | True              | test_unpause |
| resume when nothing is playing | True              | test_resume  |
| resume when nothing is playing | True              | test_pause_b |

> Skip a song

| Feature                      | Covered with Test | Test Name |
| ---------------------------- | ----------------- | --------- |
| Skip                         | True              | test_skip |
| Skip multiple                | False             | NaN       |
| Skip when nothing is running | True              | test_skip |

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

| Feature          | Covered with Test | Test Name |
| ---------------- | ----------------- | --------- |
| show queue       | False             | NaN       |
| show empty queue | False             | NaN       |

> Clear queue

| Feature                        | Covered with Test | Test Name |
| ------------------------------ | ----------------- | --------- |
| Clear Queue                    | False             | NaN       |
| Clear Queue when already empty | False             | NaN       |

> Shuffle Queue

| Feature            | Covered with Test | Test Name |
| ------------------ | ----------------- | --------- |
| Shuffle            | False             | NaN       |
| Shuffle when empty | False             | NaN       |

> Other

| Feature                   | Covered with Test | Test Name              |
| ------------------------- | ----------------- | ---------------------- |
| User not in channel check | True              | test_nobody_in_channel |

# Unit Tests "Geiler-Musik-Bot"

## Details

> RegEX

| Feature                    | Covered with Test | Test Name |
| -------------------------- | ----------------- | --------- |
| Spotify URL Verification   | True              | tba       |
| Spotify URI Verification   | True              | tba       |
| YouTube URL Verification   | True              | tba       |
| YouTube Title Verification | True              | tba       |