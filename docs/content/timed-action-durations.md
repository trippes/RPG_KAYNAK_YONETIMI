# Content-Driven Timed Action Durations

All authored durations are integer simulation ticks. The runtime converts elapsed real time into simulation ticks; content definitions decide how many ticks an action needs.

## Current content fields

### Resource gathering

A gatherable landmark may define:

```json
{
  "id": "old_oak",
  "name": "Yaşlı Meşe",
  "activities": ["gather"],
  "gathering_duration_ticks": 240
}
```

`gathering_duration_ticks` is copied into the runtime `WorldResourceNode`. The activity manager reads that value when gathering starts and schedules completion at the corresponding end tick. Different resource nodes can therefore have different gathering durations without changing gameplay code.

If the field is absent in older content, the compatibility default is 150 ticks. New Content Editor forms should expose this field as a required positive integer for newly authored gatherable content.

### Production recipes

Recipes already expose `processing_time`, stored as a positive `Tick` and serialized with the recipe. The canonical `Recipe.duration_ticks` read-only property exposes the same value under a consistent duration-oriented name.

The Content Editor should present `processing_time` as **Üretim süresi (tick)** and write the entered integer into that field. For example:

```json
{
  "recipe_id": "iron_ingot",
  "processing_time": 360
}
```

Production facilities use the recipe's configured processing time unless an explicit runtime override is supplied.

## Rules for future timed content

- Store authored durations as positive integer tick counts; do not convert them to seconds in content files.
- Use the editor label **Süre (tick)** as the common presentation. Existing domain adapters may retain specific serialized field names such as `gathering_duration_ticks` and `processing_time`.
- A timed action must resolve its duration from its content definition before it is scheduled.
- Do not add per-action duration constants to UI screens, activity managers, or the simulation loop.
- The activity manager owns lifecycle and completion; it does not own balancing values.
- Save data must preserve the resolved duration or enough content identity to resolve it deterministically after loading.
- Missing legacy fields may use documented migration defaults. Newly authored content should be validated by the Content Editor and reject zero, negative, fractional, or non-integer tick values.

This keeps balancing in content data while the simulation remains responsible only for deterministic tick scheduling.
