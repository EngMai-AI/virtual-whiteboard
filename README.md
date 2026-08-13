# Virtual Whiteboard using MediaPipe

A real-time virtual whiteboard that lets you draw in the air. A webcam
watches your hand, [MediaPipe Hands](https://developers.google.com/mediapipe)
tracks 21 landmarks on it, and your **index fingertip becomes a pen** —
no mouse, stylus, or touchscreen required.

## Project Overview

The app opens your webcam, detects one hand per frame, and interprets the
shape your hand is making (how many fingers are extended) as one of a
small set of **gestures**. Each gesture maps to an action: draw/erase
with the fingertip, free-erase with a fist, hold an open palm to clear
the board, or hover over the on-screen toolbar to change tools, color,
thickness, undo/redo, toggle shape correction, or save. The toolbar uses
a **dwell-to-click** interaction (hover over a button for about a second)
rather than a pinch gesture, since reliably detecting a thumb-to-index
pinch from a single webcam is noisier than just timing a hover — this
keeps every interaction resting on the same simple, well-separated
finger-count gestures.

All settings live in one place, `config.py`, so tuning behavior (colors,
thresholds, hold times, undo depth, etc.) never requires touching logic
code.

```
virtual_whiteboard/
├── main.py                # app loop: wires everything together
├── config.py               # every tunable constant in one place
├── requirements.txt
├── README.md
├── hand_tracker.py         # MediaPipe Hands wrapper
├── gesture_recognizer.py   # finger state -> named gesture (DRAW, SELECT, ERASE, PALM)
├── canvas.py                # drawing surface: strokes, undo/redo, shape correction hook, save
├── shape_utils.py            # bonus: automatic geometric shape correction
├── toolbar.py                 # on-screen buttons + dwell-time hover-to-click
└── utils.py                    # fingertip smoothing (EMA filter)
```

## How Gesture Recognition Works

Every frame, MediaPipe Hands returns 21 (x, y, z) landmarks for the
detected hand. `gesture_recognizer.py` converts these into a simple
**"which fingers are extended"** list by comparing each fingertip's
position to the joint below it:

- A finger (index/middle/ring/pinky) is **up** if its tip is *higher*
  (smaller y) than its PIP joint.
- The **thumb** is up if its tip is farther out on the x-axis than the
  joint below it — the comparison direction flips depending on whether
  MediaPipe reports a left or right hand, since the webcam feed is
  mirrored for natural interaction.

That five-element `[thumb, index, middle, ring, pinky]` list is then
matched against four hand shapes, chosen to be as different from one
another as possible so misreads are rare:

| Gesture | Hand shape | Action |
|---|---|---|
| **Draw** | ☝️ Index finger only | Draws (or erases, if the Eraser tool is active) with the fingertip |
| **Select** | ✌️ Index + middle | Moves over the toolbar; hover a button ~1s to click it (no drawing happens) |
| **Erase** | ✊ Closed fist (no fingers up) | Frees-erase a wide area, wherever the hand moves — no need to select the Eraser tool first |
| **Palm** | 🖐️ All five fingers up | Hold for ~1.5s to clear the whole canvas |
| *(anything else)* | — | Idle — cursor shown, nothing happens |

Two details make this feel smooth in practice:

1. **Dwell-to-click, not pinch.** Every toolbar action — picking a color,
   switching Brush/Eraser, nudging thickness, Undo, Redo, toggling shape
   correction, Clear, Save — happens by holding the Select gesture over a
   button for `config.DWELL_TIME_SEC` (default 1 second). The button
   fills with a green progress bar while you hold it, so there's always
   visual feedback before an action fires.
2. **Fingertip smoothing.** Raw landmark coordinates jitter a little
   frame to frame. `utils.PointSmoother` applies an exponential moving
   average so both the on-screen line and the toolbar hover stay steady.

### Undo / Redo and history

`canvas.py` keeps `undo_stack` / `redo_stack` lists of full canvas
snapshots (capped at `config.MAX_UNDO_STEPS`, default 20). A snapshot is
pushed before every new stroke and before a clear, so Undo/Redo step
through drawing history one action at a time. Trigger them from the
**Undo** / **Redo** toolbar buttons, or the `z` / `y` keyboard shortcuts.

### Bonus: automatic shape correction

Toggle the **Shapes** button (or press `g`) to turn on shape correction.
While active, `shape_utils.correct_shape()` looks at the raw point path
of each finished stroke and classifies it as a straight line, a
rectangle, a circle, or leaves it as a freehand polygon, then
`render_shape()` redraws a clean version in place of the wobbly original.
An open stroke (start and end far apart) becomes a straight line between
its endpoints; a closed stroke is checked for circularity and corner
count to decide between a circle, a rectangle, or a polygon.

## How to Run the Project

1. **Install dependencies** (Python 3.9–3.11 recommended; MediaPipe does
   not yet support every Python version):

   ```bash
   pip install -r requirements.txt
   ```

2. **Run the app**, with a webcam connected:

   ```bash
   python main.py
   ```

   Camera index, resolution, colors, hold times, and every other
   behavior tweak live in `config.py` — edit values there rather than
   passing flags.

3. **Draw**: point with your index finger only, below the toolbar strip.
4. **Use the toolbar**: hold up index + middle fingers and hover over a
   button (color, Brush/Eraser, Thick+/Thick-, Undo, Redo, Shapes,
   Clear, Save) for about a second until its progress bar fills.
5. **Free-erase**: make a fist and move it over the canvas.
6. **Clear everything at once**: open your whole hand and hold it for
   about 1.5 seconds.
7. **Quit**: press `q`.

### Keyboard Shortcuts (bonus)

| Key | Action |
|---|---|
| `q` | Quit |
| `c` | Clear canvas |
| `s` | Save canvas as PNG |
| `z` | Undo |
| `y` | Redo |
| `b` / `e` | Switch to Brush / Eraser tool |
| `g` | Toggle automatic shape correction |
| `1`–`9` | Select a color directly |
| `+` / `-` | Increase / decrease brush thickness |

## Performance Notes

- MediaPipe Hands tracks a single hand (`config.MAX_HANDS = 1`), which
  keeps per-frame detection cost low enough for smooth real-time use on
  a laptop webcam.
- Fingertip smoothing (`SMOOTHING_FACTOR`) and toolbar dwell timing both
  live in `config.py`, so the trade-off between responsiveness and
  jitter can be tuned without touching any drawing or gesture logic.
- Undo history is capped (`MAX_UNDO_STEPS`) so long sessions don't grow
  memory unbounded — the oldest snapshot is dropped once the cap is hit.

## Screenshots / Demo Video

*Add screenshots or a short screen recording of the app in use here
before submitting — e.g. `docs/demo.gif` or a link to a hosted video —
since this depends on your own webcam and drawing session.*
