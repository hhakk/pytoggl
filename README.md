# pytoggl

Minimalist Python [Toggl](https://toggl.com/track) client for quickly creating time entries. No real-time tracking, just simple way to add time entries to your workspaces.

## Features and nonfeatures

* No external dependencies, using `urllib`
* Works in multiple workspaces
* Projects can be added to favorites for quick access
* Sane way to input time entries

## Installation & Usage

As no external dependices are used, you can just run

```
python pytoggl.py
```

or save a script to your `$PATH` to run from anywhere

## API key

Your API key should be stored in `TOGGL_DIR/api_key`, which is `$HOME/.local/share/toggl` by default. This can be customized by specifying an alternative path for `TOGGL_DIR`.
