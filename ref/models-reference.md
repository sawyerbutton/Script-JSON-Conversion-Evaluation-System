# Data Models Reference

Complete reference for all Pydantic data models in the system.

## Overview

The system uses Pydantic v2 for strict data validation with three main model categories:

1. **Scene Models** - Scene information structures
2. **Evaluation Models** - Evaluation results and configs
3. **Supporting Models** - Info changes, relations, etc.

**File:** `src/models/scene_models.py`

---

## Scene Models

### SceneInfo (Standard Script)

Standard script scene model with strict validation.

```python
class SceneInfo(BaseModel):
    scene_id: str
    setting: str
    characters: List[str]
    scene_mission: str
    key_events: List[str]  # 1-3 items
    info_change: List[InfoChange]
    relation_change: List[RelationChange]
    key_object: List[KeyObject]
    setup_payoff: SetupPayoff
```

#### Field Requirements

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `scene_id` | str | ✅ | Must match `^(E\d{2})?S\d{2}$` (S01, E01S01) |
| `setting` | str | ✅ | Must contain "内", "外", "INT", or "EXT" |
| `characters` | List[str] | ✅ | No empty items, auto-strip whitespace |
| `scene_mission` | str | ✅ | No validation |
| `key_events` | List[str] | ✅ | Min 1, max 3 items |
| `info_change` | List[InfoChange] | ❌ | Default empty |
| `relation_change` | List[RelationChange] | ❌ | Default empty |
| `key_object` | List[KeyObject] | ❌ | Default empty |
| `setup_payoff` | SetupPayoff | ❌ | Default empty |

#### Validators

**scene_id validator:**
```python
# Valid: S01, S02, E01S01, E02S05
# Invalid: S1, scene1, 场景1
```

**setting validator:**
```python
# Valid: "内景 咖啡馆 - 日", "外景 街道 - 夜"
# Invalid: "某个地方", "咖啡馆"
```

**consistency validator:**
- Warns if `relation_change` chars not in `characters`
- Warns if `info_change` char not in `characters` (except "观众")

#### Example

```json
{
  "scene_id": "S01",
  "setting": "内景 咖啡馆 - 日",
  "characters": ["李雷", "韩梅梅"],
  "scene_mission": "展现两人关系的破裂",
  "key_events": ["韩梅梅冷漠地到来", "李雷试图解释", "韩梅梅离开"],
  "info_change": [
    {"character": "观众", "learned": "两人关系出现重大危机"}
  ],
  "relation_change": [
    {"chars": ["李雷", "韩梅梅"], "from": "恋人", "to": "分手"}
  ],
  "key_object": [],
  "setup_payoff": {"setup_for": [], "payoff_from": []}
}
```

---

### OutlineSceneInfo (Story Outline)

Flexible outline model - does NOT inherit from SceneInfo.

```python
class OutlineSceneInfo(BaseModel):
    scene_id: str
    setting: Optional[str]
    characters: List[str]
    scene_mission: str
    key_events: List[str]  # 1-5 items
    info_change: List[InfoChange]
    relation_change: List[RelationChange]
    key_object: List[KeyObject]
    setup_payoff: SetupPayoff
```

#### Key Differences from SceneInfo

| Feature | SceneInfo | OutlineSceneInfo |
|---------|-----------|------------------|
| **Inheritance** | BaseModel | BaseModel (independent) |
| **scene_id** | S01, S02 only | S0, S1, S01 all valid |
| **setting** | Must have "内/外" | Can be None, "推断：...", "背景说明" |
| **key_events** | Max 3 | Max 5 |
| **Validation** | Strict | Flexible (warnings only) |

#### Field Requirements

| Field | Required | Validation |
|-------|----------|------------|
| `scene_id` | ✅ | Must match `^S\d+$` (S0, S1, S01 all OK) |
| `setting` | ❌ | Any string or None (→ "未指定") |
| `characters` | ❌ | Default empty, auto-strip |
| `scene_mission` | ✅ | No validation |
| `key_events` | ✅ | Min 1, max 5 (warns if >5) |

#### Validators

**scene_id validator:**
```python
# Valid: S0, S1, S2, S01, S99
# Invalid: 1, Scene1, 场景1
```

**setting validator:**
```python
# All valid:
# - "推断：城市街道"
# - "背景说明"
# - "2145年时间监察局"
# - None → "未指定"
```

**consistency validator:**
```python
# Only warns, never raises errors
# Helps identify potential issues
```

#### Example

```json
{
  "scene_id": "S0",
  "setting": "背景说明",
  "characters": [],
  "scene_mission": "建立故事世界观",
  "key_events": [
    "介绍时空背景",
    "说明主要设定",
    "引入主角身份"
  ],
  "info_change": [
    {"character": "观众", "learned": "故事发生在未来世界"}
  ],
  "relation_change": [],
  "key_object": [],
  "setup_payoff": {"setup_for": ["S1"], "payoff_from": []}
}
```

---

## Supporting Models

### InfoChange

Information change tracking.

```python
class InfoChange(BaseModel):
    character: str  # Who learns
    learned: str    # What they learn
```

**Validation:**
- `character` cannot be empty
- Auto-strips whitespace

**Example:**
```json
{
  "character": "观众",
  "learned": "主角处境艰难但勇敢"
}
```

---

### RelationChange

Relationship change between two characters.

```python
class RelationChange(BaseModel):
    chars: List[str]         # Exactly 2 characters
    from_relation: str       # Original relation (alias: "from")
    to_relation: str         # New relation (alias: "to")
```

**Validation:**
- `chars` must have exactly 2 items
- `chars[0]` ≠ `chars[1]`

**Field Aliases:**
- Use `"from"` and `"to"` in JSON
- Access as `from_relation` and `to_relation` in Python

**Example:**
```json
{
  "chars": ["主角", "反派"],
  "from": "陌生人",
  "to": "宿敌"
}
```

**Important:** Must use `"chars"` not `"characters"` in JSON!

---

### KeyObject

Important object in the scene.

```python
class KeyObject(BaseModel):
    object: str   # Object name
    status: str   # Object status/role
```

**Validation:**
- `object` cannot be empty
- Auto-strips whitespace

**Example:**
```json
{
  "object": "神秘信封",
  "status": "推动情节的关键物"
}
```

---

### SetupPayoff

Foreshadowing and payoff tracking.

```python
class SetupPayoff(BaseModel):
    setup_for: List[str]     # Scene IDs for future payoff
    payoff_from: List[str]   # Scene IDs being paid off
```

**Validation:**
- Each item must match `^[ES]\d+$`
- Valid: S01, S05, E01

**Example:**
```json
{
  "setup_for": ["S05", "S08"],
  "payoff_from": ["S02"]
}
```

---

## Enums

### TimeOfDay

```python
class TimeOfDay(str, Enum):
    DAY = "日"
    NIGHT = "夜"
    DAWN = "黎明"
    DUSK = "黄昏"
    MORNING = "早晨"
    AFTERNOON = "下午"
    EVENING = "傍晚"
```

### LocationType

```python
class LocationType(str, Enum):
    INT = "内"        # Interior
    EXT = "外"        # Exterior
    INT_EXT = "内/外"  # Both
```

---

## Validation Functions

### validate_script_json()

Main validation function that works with both scene types.

```python
def validate_script_json(
    json_data: Dict[str, Any],
    scene_type: str = "standard"
) -> Dict[str, Any]:
    """
    Validate scene JSON data.

    Args:
        json_data: Scene data to validate
        scene_type: "standard" or "outline"

    Returns:
        {
            "valid": bool,
            "errors": List[str],
            "scene": Optional[SceneInfo | OutlineSceneInfo]
        }
    """
```

**Usage:**

```python
from models.scene_models import validate_script_json

# Standard script
result = validate_script_json(scene_data, "standard")
if result["valid"]:
    scene = result["scene"]  # SceneInfo instance
else:
    print(result["errors"])

# Outline
result = validate_script_json(outline_data, "outline")
if result["valid"]:
    scene = result["scene"]  # OutlineSceneInfo instance
```

---

## Common Validation Errors

### Standard Script Errors

1. **Invalid scene_id format**
   ```
   scene_id: "S1" → Error (must be S01)
   scene_id: "场景1" → Error (must be Latin)
   ```

2. **Missing location type in setting**
   ```
   setting: "咖啡馆 - 日" → Error (missing 内/外)
   setting: "内景 咖啡馆 - 日" → Valid
   ```

3. **Too many key_events**
   ```
   key_events: ["事件1", "事件2", "事件3", "事件4"] → Error (max 3)
   ```

4. **Wrong relation_change format**
   ```json
   // Wrong: uses "characters" instead of "chars"
   {"characters": ["A", "B"], "from": "x", "to": "y"}

   // Correct:
   {"chars": ["A", "B"], "from": "x", "to": "y"}
   ```

### Outline Errors

Outlines are much more forgiving, but can still have errors:

1. **Invalid scene_id pattern**
   ```
   scene_id: "1" → Error (must start with S)
   scene_id: "S1" → Valid
   ```

2. **Too many key_events (warning only)**
   ```
   key_events: [1, 2, 3, 4, 5, 6] → Warning (suggests ≤5)
   ```

3. **Empty key_events**
   ```
   key_events: [] → Error (min 1 required)
   ```

---

## Migration Notes

### Pydantic V1 → V2

The codebase uses Pydantic V2. Key changes:

| V1 | V2 |
|----|-----|
| `@validator` | `@field_validator` |
| `@root_validator` | `@model_validator(mode="after")` |
| `each_item=True` | Loop manually in validator |
| `Config.schema_extra` | `model_config = ConfigDict(json_schema_extra=...)` |
| `allow_population_by_field_name` | `populate_by_name` |

---

## Best Practices

### 1. Always Use validate_script_json()

Don't instantiate models directly:

```python
# Bad
scene = SceneInfo(**data)  # Might raise unclear errors

# Good
result = validate_script_json(data, "standard")
if result["valid"]:
    scene = result["scene"]
else:
    handle_errors(result["errors"])
```

### 2. Choose Right Model

- Standard formatted scripts → `scene_type="standard"`
- Story outlines/梗概 → `scene_type="outline"`

### 3. Handle Warnings

Outline models print warnings - capture them if needed:

```python
import io, sys
from contextlib import redirect_stdout

f = io.StringIO()
with redirect_stdout(f):
    result = validate_script_json(data, "outline")
warnings = f.getvalue()
```

### 4. Respect Field Aliases

Always use JSON field names in data:

```python
# Correct
{"chars": ["A", "B"], "from": "x", "to": "y"}

# Wrong
{"chars": ["A", "B"], "from_relation": "x", "to_relation": "y"}
```

---

## Related Documentation

- [API Reference](./api-reference.md) - Using models in code
- [Scripts Guide](./scripts-guide.md) - How scripts use models
- [Architecture](./architecture.md) - Model role in system
