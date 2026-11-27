# Feature 03 — Persian Conversation Engine & Bounded Context

**Feature Identifier:** `FEAT-03`  
**Layer Focus:** `src/lumi/modules/conversation/`  
**Shared Contracts Used:** `Emotion`  
**Deliverable:** Asynchronous `ConversationService`, bounded RAM context manager, offline JSON-driven `PredefinedProvider`, and stubbed `OpenAIProvider` extension seam  

---

## 1. Overview & Business Value

Lumi's personality lives in `conversation`. Given recognized Persian user text, `ConversationService` maintains recent conversational context in memory, delegates response generation to a `ConversationProvider`, and returns both a Persian reply string and a target `Emotion` for Lumi's face.

In MVP, `PredefinedProvider` delivers fast, varied, context-aware offline Persian replies from packaged JSON rules without any cloud dependency, while keeping the provider contract clean enough to plug in `OpenAIProvider` later with zero changes to `RobotController` or other modules.

---

## 2. Responsibilities & Boundaries

### 2.1 Owns
- Asynchronous `ConversationService.respond(user_text: str) -> ConversationReply` API (`conversation_service.py`).
- Local conversation models (`ConversationMessage`, `ConversationReply`, `ConversationContext`) — **kept inside `conversation`, never placed in `lumi.shared`**.
- `ConversationContextManager` (`context/conversation_context_manager.py`): rolling in-memory history (default max `20` messages), `clear_history()`, optional `pending_intent`, and lightweight metadata.
- `ConversationProvider` abstract contract (`conversation_provider.py`).
- `PredefinedProvider` (`providers/predefined/`): Persian text normalization, intent matching (`intents.json`), contextual rule evaluation, non-repeating response selection (`responses.json`), and graceful fallback.
- `OpenAIProvider` stub (`providers/openai/openai_provider.py`): future extension placeholder raising `NotImplementedError` without requiring the `openai` SDK.

### 2.2 Does NOT Own
- Speech recognition or synthesis (`Speech`).
- Audio playback (`Audio`).
- Face rendering or deciding `RobotActivity` (`Face` / `RobotController`).
- Persistent disk/database memory (explicitly excluded from MVP).

---

## 3. Contracts & Data Models (`conversation_models.py` & `conversation_provider.py`)

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Protocol
from lumi.shared.enums import Emotion

@dataclass(frozen=True, slots=True)
class ConversationMessage:
    role: Literal["user", "assistant"]
    text: str
    emotion: Emotion | None = None
    timestamp: datetime = ...  # UTC timestamp

@dataclass(frozen=True, slots=True)
class ConversationReply:
    text: str
    emotion: Emotion
    intent: str | None = None
    pending_intent: str | None = None
    metadata_updates: dict[str, str] = field(default_factory=dict)

class ConversationProvider(Protocol):
    async def generate_reply(
        self,
        user_text: str,
        context: "ConversationContextSnapshot",
    ) -> ConversationReply:
        ...
```

### 3.1 Context Rules (`context/conversation_context.py`, `conversation_context_manager.py`)
- **Bounded Window:** Stores at most `max_messages` (default `20`, configurable, must be `>= 1`) in a `collections.deque(maxlen=max_messages)` (or equivalent bounded list) in RAM. When full, oldest messages drop automatically.
- **Ownership:** `ConversationService` owns mutating context—appending the user message, passing an immutable snapshot of context to the provider, then appending the assistant reply and applying `pending_intent` / `metadata_updates`. Providers never mutate shared state directly.
- **Reset & Metadata:** Supports `clear_history()` (clears messages, `pending_intent`, and recent-response tracking metadata), `pending_intent: str | None`, and `metadata: dict[str, str]`.

---

## 4. `PredefinedProvider` Engine & JSON Resources

### 4.1 Persian Text Normalization (`predefined_intent_matcher.py`)
Before matching, user input passes through a deterministic Persian normalizer:
- Convert Arabic variants to standard Persian (`ي` → `ی`, `ك` → `ک`, `ة` → `ه`).
- Normalize zero-width non-joiner (ZWNJ / نیم‌فاصله) variations and collapse repeated whitespace.
- Strip Persian diacritics (tashkeel/harakat) and standard punctuation (`؟`, `!`, `.`, `،`).
- Trim leading/trailing spaces.

### 4.2 Intent Matching & Contextual Rules (`predefined_rule_engine.py`)
- **Intents (`data/intents.json`):** Loaded via `importlib.resources` from the installed package. Initial starter intents (extensible via JSON without code edits):
  - `greeting` (e.g., «سلام», «درود», «صبح بخیر») → `HAPPY`
  - `wellbeing_ask` (e.g., «خوبی», «چطوری», «حالت چطوره») → `HAPPY`
  - `wellbeing_reply_positive` / `wellbeing_reply_negative` (contextual follow-up when `pending_intent == "awaiting_user_wellbeing"`) → `HAPPY` / `SAD`
  - `identity_name` (e.g., «اسمت چیه», «کی هستی») → `HAPPY` / `NEUTRAL`
  - `thanks` (e.g., «مرسی», «ممنون», «دستت درد نکنه») → `HAPPY`
  - `farewell` (e.g., «خداحافظ», «فعلا», «شب بخیر») → `NEUTRAL` / `HAPPY`
  - `fallback` (unknown input) → `NEUTRAL` or `SURPRISED`
- **Matching Strategy:** Exact phrase match first, then keyword/token subset scoring with priority ordering; contextual `pending_intent` rules take precedence for short follow-ups (e.g., «خوبم ممنون» after Lumi asked «سلام! خوبی؟»).
- **Anti-Repetition Selection (`data/responses.json`):** Each intent defines a list of candidate `{ "text": "...", "emotion": "happy", "next_pending_intent": "..." }` templates. The provider tracks the last selected response index per intent (stored in context metadata or local history) and avoids picking the same response twice in a row whenever `len(candidates) > 1`.

---

## 5. Future `OpenAIProvider` Extension Point

- File `providers/openai/openai_provider.py` defines `OpenAIProvider` implementing `ConversationProvider`.
- In MVP, instantiating or calling it raises `NotImplementedError("OpenAIProvider is deferred beyond MVP")`.
- No `openai` dependency or API key requirement exists in MVP `pyproject.toml`.

---

## 6. Acceptance Criteria

1. `ConversationService.respond("سلام")` returns a `ConversationReply` with Persian text and `Emotion.HAPPY`, and records both user and assistant messages in RAM context.
2. Context never exceeds `max_messages` (default `20`); `clear_history()` empties messages, `pending_intent`, and metadata cleanly.
3. Persian normalizer equates Arabic `ي`/`ك` with Persian `ی`/`ک` and strips punctuation/extra whitespace.
4. Contextual follow-up works across two turns (e.g., Lumi sets `pending_intent` after greeting → user answers «بد نیستم» / «خوبم» → rule engine matches follow-up).
5. Repeated identical intents cycle through alternative templates instead of repeating the exact previous reply when alternatives exist.
6. Unknown inputs return a valid Persian fallback response rather than raising or returning empty text.
7. `intents.json` and `responses.json` load cleanly from installed package resources.
