# Verifying map changes

Bugs only show with real density: hundreds of markers in one city, pan across neighbourhoods, zoom out to a
country and back.

## Checklist

- First open, no interaction: markers appear (catches view-based stale camera).
- Pan: markers stay; one request per settled pan (log); no duplicates.
- Filter change: list replaced, not merged.
- Fast zoom out/in: no long stall; markers only near the screen.
- Select: grows unclipped, above neighbours, centred above the sheet.
- Dismiss: shrinks back; no mid-animation freeze (rapid select/dismiss).
- Dense area: labels don't overlap; clusters don't pile up.

## adb recipes

```bash
# Multi-display emulators (foldables) print a warning / black PNG; pick a display:
adb shell dumpsys SurfaceFlinger --display-id
adb exec-out screencap -d <display-id> -p > /tmp/shot.png

# Frame stats around an interaction
adb shell dumpsys gfxinfo <package> reset
# ...interact (input swipe / double tap: `adb shell "input tap X Y; input tap X Y"`)...
adb shell dumpsys gfxinfo <package> | grep -E "Total frames|Janky|90th|99th"

# One request per pan (adjust endpoint name)
adb logcat -d | grep -c "event-geolocation"
```

- Emulator frame numbers: before/after on the same machine only. Claim perf wins on a real mid-range device, release build.
- `adb shell input` can't pinch: double tap to zoom in; app camera controls or UiAutomator/Macrobenchmark for zoom-out.
