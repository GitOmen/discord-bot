# Discord Bot

This is a multi-functional discord bot created with following technologies:

- Python 3.9
- [discord.py](https://github.com/Rapptz/discord.py) 1.7.3
- [lavalink](https://github.com/Devoxin/Lavalink.py) 3.1.4

# Features

- custom command prefix (default: `.`, can be changed with `change_prefix` command)
- voice channel join/leave logs (log channel can be set with `set_log_channel` command)
- `clear` specified amount of recent messages (one if no arguments passed)

## Music Player
- `play` song or playlist from YouTube/SoundCloud/Spotify (for single song both direct link or search query can be used e.g. `.play darude sandstorm`)
- `pause`\ `resume` player
- `disconnect` bot from voice channel and clear player queue
- `skip` specified amount of tracks in queue (one if no arguments passed)
- `shuffle` queue

# To Do

## Music Section

### Single Song
- loop song
- seek point of song
- current song info

### Queue

- show queue
- clear queue
- loop queue
- move song in queue
- remove song from queue
- jump to song in queue
- playlist aliases defined by user