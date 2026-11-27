# 08 — Manual Test & Verification Checklist

Use this checklist to verify Lumi end-to-end on a desktop PC with real audio hardware, offline Persian models, and the Pygame window, and to track future Raspberry Pi Zero 2 W validation gates.

---

## 1. Startup, Packaging & Offline Isolation
- [ ] Run `pip install -e .[dev]` in a clean virtual environment and launch via `lumi` (and `python -m lumi.main`).
- [ ] Disconnect internet / disable Wi-Fi and confirm startup, speech recognition, conversation, and synthesis succeed **100% offline**.
- [ ] Confirm missing Vosk model path or missing `espeak-ng` fails fast at startup with a clear diagnostic message rather than crashing mid-turn.
- [ ] Confirm Pygame window opens at `480×320` showing `IDLE` (`NEUTRAL`) geometric eyes with natural periodic blinking.

---

## 2. Persian Voice Interaction & Quality Corpus (Auto-VAD Mode)
Verify Lumi completes full turns (`IDLE` → `LISTENING` on voice onset → `THINKING` → `SPEAKING` with emotion → `IDLE`) across these representative Persian utterances:
- [ ] **Greeting:** Say «سلام» → Lumi replies warmly (e.g., «سلام! خوبی؟») with `HAPPY` eyes.
- [ ] **Contextual Follow-up:** Reply «خوبم ممنون» right after Lumi asked «خوبی؟» → Lumi recognizes the follow-up context appropriately.
- [ ] **Identity:** Ask «اسمت چیه؟» → Lumi introduces itself with varied phrasing.
- [ ] **Wellbeing:** Ask «چطوری؟» / «حالت چطوره؟» → Lumi responds naturally with `HAPPY` eyes.
- [ ] **Thanks:** Say «مرسی» / «ممنون» → Lumi responds politely.
- [ ] **Anti-Repetition:** Say «سلام» three times across turns → Lumi avoids repeating the exact same reply twice in a row when alternatives exist.
- [ ] **Unknown Input:** Say an unrecognized/out-of-scope sentence → Lumi replies with a polite Persian fallback (`NEUTRAL`/`SURPRISED`) without crashing.
- [ ] **Farewell:** Say «خداحافظ» → Lumi gives a warm farewell.

---

## 3. Manual Trigger, Barge-In & Recovery
- [ ] Switch `LUMI_INTERACTION_MODE=push_to_talk`: verify Lumi stays in `IDLE` until `Space` is tapped, records on tap, and finishes on silence or second `Space` tap.
- [ ] During `SPEAKING` (either mode), tap `Space` → verify audio playback stops within `<150ms` and Lumi immediately enters `LISTENING` for your interrupting utterance.
- [ ] Stay silent through a full `LISTENING` timeout (`8s`) or produce a brief desk tap (`<0.25s`) → verify Lumi ignores noise/empty STT and returns cleanly to `IDLE` without getting stuck.
- [ ] Confirm Lumi does not trigger itself from its own speaker playback (half-duplex isolation).

---

## 4. Clean Shutdown
- [ ] Close the Pygame window (or press `Ctrl+C` in terminal) during `IDLE`, `LISTENING`, and `SPEAKING` → verify process exits cleanly with zero hanging threads or unclosed PortAudio streams.

---

## 5. Future Raspberry Pi Zero 2 W Hardware Gate (Pending Measurement)
*Do not mark Pi support complete until measured on actual hardware:*
- [ ] Measure peak RSS memory with `Vosk small-fa` + `Pygame` (`< 280 MB` target on 512 MB RAM).
- [ ] Measure end-to-end turn latency (STT + Conversation + eSpeak NG) on ARM64 Cortex-A53.
- [ ] Verify Pygame rendering on the 2–3" target display (`kmsdrm`/`fbcon`/X11) at `20–30 FPS`.
- [ ] Verify ALSA/USB/I2S mic & speaker audio stability at `16000 Hz`.
