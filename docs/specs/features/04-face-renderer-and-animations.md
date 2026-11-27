# Feature 04 — Geometric Face Renderer & Animations

**Feature Identifier:** `FEAT-04`  
**Layer Focus:** `src/lumi/modules/face/`  
**Shared Contracts Used:** `RobotState`, `Emotion`, `RobotActivity`  
**Deliverable:** Asset-free Pygame two-eye renderer with smooth emotion transitions, blinking, and distinct activity indicators  

---

## 1. Overview & Business Value

Lumi's personality is communicated visually through an expressive geometric face. Using Pygame without any external PNG/sprite assets, `face` renders two crisp geometric eyes plus subtle activity cues on a desktop window sized proportionally for a future 2–3 inch Raspberry Pi display.

The module keeps **Emotion** (how Lumi feels) cleanly separated from **RobotActivity** (what Lumi is currently doing) and isolates Pygame's main-thread event loop from blocking audio/speech work.

---

## 2. Responsibilities & Boundaries

### 2.1 Owns
- `FaceService` (`face_service.py`): thread-safe `set_state(state: RobotState)`, Pygame window lifecycle, main-thread render loop, and dispatching UI events (window close, `Space` trigger) via lightweight callbacks.
- `FaceRenderer` (`face_renderer.py`): procedural drawing of two geometric eyes, eyelid/brow geometry, and activity indicators on a `pygame.Surface`.
- `FaceAnimations` (`face_animations.py`): delta-time (`dt`) driven blinking, eye gaze micro-saccades, smooth interpolation (lerping) between emotion shapes, and activity motion loops.
- `FaceConfig` (`face_config.py`): window size, logical resolution, FPS target, color palette, blink intervals, and transition speed.

### 2.2 Does NOT Own
- Deciding when to listen/think/speak (`RobotController` owns state transitions).
- Importing `audio`, `speech`, or `conversation`.

---

## 3. Emotion vs. Activity Visual Composition

**Core Rule:** `Emotion` controls **eye geometry & color accent**; `RobotActivity` controls **motion & indicator overlay**. They compose without overwriting each other (e.g., `SPEAKING` + `HAPPY` renders happy curved eyes pulsing rhythmically).

### 3.1 Emotion Targets (Eye Geometry)
| Emotion | Eye Geometry / Shape | Accent / Mood |
|---|---|---|
| `NEUTRAL` | Rounded rectangles / soft ovals, relaxed height | Soft cyan/white (`#E6F4F1` / `#4DD0E1`) |
| `HAPPY` | Upward curved / cheerful squint (`^ ^` style arc or raised lower lid) | Warm cyan/mint glow |
| `SAD` | Inner corners tilted upward, slightly narrowed height, lower gaze | Cool muted blue |
| `ANGRY` | Sharp inward downward brow slant (`\ /` top cut), narrowed height | Warm amber/coral-red |
| `SURPRISED` | Tall wide circular/oval eyes, slightly raised position | Bright sky white-cyan |

### 3.2 Activity Modifiers (Motion & Indicator Overlay)
| Activity | Visual Behavior | Priority / Interaction with Emotion |
|---|---|---|
| `IDLE` | Periodic natural blinks (every `2.5s–6.0s`) + gentle slow gaze drift | Emotion shape stays fully active; defaults to `NEUTRAL` when resting. |
| `LISTENING` | Attentive eye scale boost (`~1.08x`), centered gaze, pulsing outer/bottom listening indicator ring/dot | Keeps active emotion while clearly signaling mic readiness. |
| `THINKING` | Eyes glance upward/side-to-side smoothly + animated 3-dot or orbiting pulse below/between eyes | Temporarily overrides gaze drift; preserves emotion tint/brow shape. |
| `SPEAKING` | Subtle rhythmic vertical eye/mouth-bar pulse synchronized with speaking cadence (`dt`-based sine/envelope) | **Must preserve** the conversation's returned `Emotion` (e.g., `HAPPY` while greeting). |

---

## 4. Concurrency & Rendering Architecture

```text
[Controller Worker Thread] ──(thread-safe lock: update target RobotState)──> [FaceService]
                                                                                  │
[Main Thread: FaceService.run()]                                                  ▼
   1. Poll pygame.event.get() (QUIT -> on_quit(), KEYDOWN SPACE -> on_manual_trigger())
   2. Read latest target RobotState atomically
   3. Advance FaceAnimations.update(dt, state)
   4. FaceRenderer.draw(surface, animated_pose, state)
   5. pygame.display.flip() & clock.tick(target_fps)
```

### 4.1 Threading & Headless Testability
- Pygame initialization, event pumping, and `display.flip()` execute **strictly on the OS main thread**.
- `FaceService.set_state(state)` acquires a lightweight `threading.Lock` and writes an immutable `RobotState`, taking microseconds and never blocking the caller.
- `FaceAnimations` and `FaceRenderer` accept abstract state + `dt` (and a `pygame.Surface` or headless dummy surface under `SDL_VIDEODRIVER=dummy`), allowing deterministic unit tests of blinking, emotion interpolation, and activity composition without an interactive monitor.
- Logical drawing coordinates normalize to `320×240` (or scale cleanly to `FaceConfig.width × height`, default `480×320`) so future 2–3" Raspberry Pi SPI/DSI displays require only config/driver changes.

---

## 5. Risks & Mitigations

- **Risk — Windows/Linux SDL Event Queue Freeze:** If `FaceService.run()` isn't pumped frequently, Windows marks the window "Not Responding". *Mitigation:* Main thread never performs audio, Vosk, or eSpeak calls; loop runs steadily at `30–60 FPS`.
- **Risk — Pi Zero 2 W CPU Overhead from Pygame:** High FPS software blitting can spike CPU on Cortex-A53. *Mitigation:* Configurable `target_fps` (default `30` FPS on low-power profiles, `60` on PC), simple filled geometric primitives (`pygame.draw.rect`/`ellipse`/`polygon`/`circle`), and no per-frame surface allocations.

---

## 6. Acceptance Criteria

1. `FaceService.set_state(RobotState(SPEAKING, HAPPY))` preserves `HAPPY` eye geometry while animating `SPEAKING` pulse.
2. `FaceAnimations.update(dt, state)` smoothly interpolates eye geometry over time rather than snapping abruptly, and triggers periodic blinks without external image files.
3. Passing `SDL_VIDEODRIVER=dummy` allows `FaceRenderer` and `FaceService` tests to execute in CI/headless environments without crashing.
4. `QUIT` and `SPACE` keyboard events trigger registered callbacks cleanly without blocking the render loop.
5. `face` module has zero imports from `audio`, `speech`, `conversation`, or `controller`.
