---
name: MUI Slider — drag lands on the step grid, arrow keys accumulate float error
description: Drag a MUI slider (computed x on the root's box); arrow keys give 1.5000000000000004 and mark labels are transform-shifted
type: feedback
aliases: [slider, MuiSlider, drag slider, aria-valuenow, mark label, roundValueToStep]
tags: [area/ui, type/gotcha]
created: 2026-08-29
updated: 2026-08-29
---

## The three facts

1. **Drag is clean, keyboard is not.** MUI v5's pointer path routes through
   `roundValueToStep()` (which applies `toFixed(precision)`); its keyboard handler just adds
   `step`. Five `ArrowRight` presses from `1.0` with `step=0.1` give **`1.5000000000000004`**,
   and MUI paints all 17 digits in the value label. Filed as EliteaAI/elitea-testing-public#1966
   for the Elitea voice sliders — but the mechanism is MUI's, so expect it on *any* slider here.

2. **`input.value` HIDES the artifact.** The DOM normalises `1.5000000000000004` to `"1.5"`,
   so `to_have_value("1.5")` passes either way. Only `aria-valuenow` (or whatever the app
   persists) exposes it. Pin `aria-valuenow` when the exact value matters.

3. **Never drag a thumb onto a MARK LABEL.** The first and last labels are `translateX(0)` /
   `translateX(-100%)`-shifted, so their centre is not the track position they name — dragging
   onto a `100%` label landed on **0.95** (verified live). Interior labels line up by luck.
   The reliable form is a computed x on the slider ROOT's bounding box:
   `box.x + box.width * (target-min)/(max-min)` — and it needs no handle beyond root + thumb.

## Testids to ask for
MUI `Slider` forwards `slotProps={{ input: {...}, thumb: {...} }}`, so a slider needs three
pure-prop testids: `…-slider` (root, for the box + mark-label text), `…-slider-input`
(range/attr assertions), `…-slider-thumb` (drag start). No new DOM node, no new hook.

Related: [[settings_preferences_localstorage_state]]
