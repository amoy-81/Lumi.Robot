# 04 — Persian Conversation & Geometric Face Engine Guide

This document details Lumi's conversational brain (`modules/conversation`) and expressive geometric eye renderer (`modules/face`), along with how they coordinate via `Emotion` and `RobotActivity`.

---

## 1. Conversation Engine (`modules/conversation/`)

### 1.1 Responsibilities & Context Isolation
- `ConversationService` exposes `async def respond(user_text: str) -> ConversationReply`.
- Conversation history lives in `ConversationContextManager` (inside `conversation`, never `lumi.shared`), storing a rolling window of the **latest 20 messages** in RAM by default (configurable), plus `pending_intent` and lightweight metadata.
- No database or disk persistence exists in MVP. `clear_history()` resets messages, `pending_intent`, and anti-repetition tracking.

### 1.2 Offline `PredefinedProvider` Pipeline
```text
User Text ("سلاااام خوبی؟!")
    │
    ▼  1. Persian Normalization (ي->ی, ك->ک, strip diacritics/punctuation, collapse spaces)
Normalized ("سلام خوبی")
    │
    ▼  2. Contextual Rule Engine (check pending_intent first, then intents.json exact/keyword match)
Matched Intent ("greeting" / "wellbeing_ask")
    │
    ▼  3. Varied Response Selector (responses.json, avoid repeating last used variant)
ConversationReply(text="سلام! ممنون، تو چطوری؟", emotion=Emotion.HAPPY, pending_intent="awaiting_user_wellbeing")
```

- **Starter Intents (`data/intents.json`):** `greeting`, `wellbeing_ask`, contextual `wellbeing_reply_positive` / `wellbeing_reply_negative`, `identity_name`, `thanks`, `farewell`, and `fallback`.
- **Anti-Repetition:** Tracks the last selected variant index per intent in context metadata and excludes it on consecutive matches when alternatives exist.

### 1.3 Future `OpenAIProvider` Extension Seam
- `providers/openai/openai_provider.py` defines `OpenAIProvider` implementing the exact same `ConversationProvider` protocol (`async def generate_reply(user_text, context)`).
- In MVP, calling it raises `NotImplementedError`, and `openai` is omitted from `pyproject.toml` dependencies.

---

## 2. Geometric Face Engine (`modules/face/`)

### 2.1 Asset-Free Geometric Eyes
Lumi draws two procedural geometric eyes using Pygame primitives (`rect`, `ellipse`, `polygon`, `circle`) on a logical `320×240` coordinate space scaled cleanly to the configured window (`480×320` on desktop). No external PNGs or sprite sheets are required.

### 2.2 Separation of `Emotion` and `RobotActivity`
- **Emotion (`NEUTRAL`, `HAPPY`, `SAD`, `ANGRY`, `SURPRISED`)** sets eye shape, brow slant/curve, height ratio, and color accent.
- **RobotActivity (`IDLE`, `LISTENING`, `THINKING`, `SPEAKING`)** layers motion and minimal indicators on top **without erasing the active emotion**:
  - `IDLE`: Natural randomized blinking (`2.5s–6.0s`) + gentle slow gaze drift.
  - `LISTENING`: Slight attentive eye scale boost + centered gaze + subtle pulsing listening indicator.
  - `THINKING`: Smooth side-to-side/upward gaze scan + animated thinking pulse/dots.
  - `SPEAKING`: Rhythmic vertical eye/accent pulse synchronized with speaking state while keeping e.g. `HAPPY` or `SURPRISED` eye geometry intact.

### 2.3 Smooth Interpolation
`FaceAnimations.update(dt, state)` smoothly lerps eye width, height, brow tilt, and pupil offset toward target emotion parameters each frame so transitions look organic rather than snapping abruptly.
