Destroyman III Desktop Buddy

A chaotic little desktop companion made with PyQt6 that sits on your screen, talks to you, changes skins, bobs around, and updates your Discord Rich Presence. (although only once for now; will be fixed later on)

# Features

- Always-on-top transparent desktop mascot
- Random speech bubbles
- Multiple character skins
- Animated bobbing/squish effect
- Discord Rich Presence integration
- System tray controls
- Online speech fetching with local fallback
- Custom font support
- Special skin-specific animations

# Requirements

Install Python 3.10+ and the following dependencies:

```pip install PyQt6 pystray pillow requests pypresence```

# Controls

Right-click the tray icon to access:

- Quit
- Change Skin (Cycle Forward)
- Change Skin (Cycle Back)

# Packaging

## To build an executable with PyInstaller

```pyinstaller --onefile --windowed main.py```

You may need to manually include:

- resources/
- fonts
- skins
- icon files

# Notes

The window is click-through using:

```QtCore.Qt.WindowType.WindowTransparentForInput```

The mascot automatically talks every 20–30 seconds.
Some skins have unique animations or expressions.
Discord skin includes animated arm movement.
