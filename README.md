# Salvage

A [Horizon](https://playhorizon.dev) content mod: the all-recycling mod. Smelt leather,
wood, stone, diamond gear, saddles and horse armour back into useful materials, and unknot a
bow or a fishing rod at the crafting table for its string.

Nothing in that chest is trash anymore. That leather helmet from a zombie drop, the stone
pickaxe you outgrew, the saddle from a horse you never ride — put any of it in a furnace with
any fuel and get materials back.

| Smelt this | Get this |
| --- | --- |
| Leather helmet / chestplate / leggings / boots | Leather |
| Leather horse armor | Leather |
| Saddle | Leather |
| Wooden sword / pickaxe / axe / shovel / hoe | Charcoal |
| Stone sword / pickaxe / axe / shovel / hoe | 2 Cobblestone |
| Diamond sword / pickaxe / axe / shovel / hoe | Diamond |
| Turtle Shell (turtle helmet) | Turtle scute |
| Nautilus Shell | Turtle scute |
| Elytra | Phantom membrane |

| Craft this | Get this |
| --- | --- |
| Iron horse armor | 3 Iron nuggets |
| Golden horse armor | 3 Gold nuggets |
| Diamond horse armor | 3 Diamonds |
| Bow | 2 String |
| Fishing rod | 2 String |

Every smelting recipe takes about 10 seconds and gives a little experience.
Diamond gear and the elytra take longer (20 seconds) and give more experience.
Stone tools are quicker (5 seconds).

Vanilla already recycles iron, gold and copper gear, chainmail and copper armour into a single
nugget. Salvage covers what vanilla leaves behind and pays better for the heavy pieces — but
the **metal horse armours break down at a crafting table, not in a furnace**: vanilla's own
furnace recipe for them is a single nugget, and a content mod cannot override a vanilla
recipe. Smelting an iron horse armour still gives vanilla's one nugget; the crafting table
gives three.

- Mod id: `salvage`
- Kind: content mod (`.hmod`) — data only, no code, nothing to run
- Content mod API: 0.2, side: both
- Tested on: Horizon 0.2.97 (Nightly 2026-10-30), Minecraft Java Edition 26.3

## Install

1. Download `salvage.hmod` from the [Horizon mod registry](https://playhorizon.dev/mods)
   or the launcher's mod browser.
2. Put it in the `horizon-mods/` folder inside your Horizon install (next to `horizon-client.exe`).
3. Start the game, go to Options → Mods, enable **Salvage**, then restart the game.

Works in single player. On a multiplayer server, the server needs the mod too.

## Ratios

- Leather gear, wooden tools, diamond tools, shells and the elytra: **1 in, 1 out**.
- Stone tools: **1 in, 2 cobblestone out** (in the furnace).
- Iron, golden and diamond horse armour: **1 in, 3 out** (at the crafting table).
- Bow and fishing rod: **1 in, 2 string out** (at the crafting table).

Vanilla already recycles iron, gold and copper gear, chainmail and copper armour into a single
nugget; this covers what vanilla leaves behind and pays better for the heavy pieces.

## Why the metal horse armour is a crafting recipe

Horizon resolves a cooking recipe by scanning the recipe table and taking the **first** match
for the ingredient — and vanilla's recipes are loaded before a content mod's. So a content mod
cannot replace a vanilla furnace recipe, and vanilla already smelts iron and golden horse
armour into one nugget.

The crafting table has no such conflict: no vanilla recipe takes a metal horse armour as an
input, so the mod's recipe is the only match and it wins. This also means the behaviour is the
same on every Horizon version, instead of depending on how the recipe table happens to be
sorted.

## Build from source

```sh
cargo install --git https://github.com/horizon-rust/horizon cargo-horizon-mod
cargo horizon-mod build
cargo horizon-mod check target/horizon-mod/salvage.hmod
```

The build is deterministic: the same sources produce the same file bytes.

## What's inside

Twenty-nine recipes under `data/salvage/recipe/` — 24 furnace smelting recipes and 5
crafting-table recipes — all using vanilla items only. No new items, blocks or textures, and
no Minecraft assets bundled.

| Category | Items | Station | Output |
| --- | --- | --- | --- |
| Leather armor | helmet, chestplate, leggings, boots | furnace | Leather |
| Leather horse armor | — | furnace | Leather |
| Saddle | — | furnace | Leather |
| Wooden tools | sword, pickaxe, axe, shovel, hoe | furnace | Charcoal |
| Stone tools | sword, pickaxe, axe, shovel, hoe | furnace | 2 Cobblestone |
| Diamond tools | sword, pickaxe, axe, shovel, hoe | furnace | Diamond |
| Turtle Shell | turtle helmet | furnace | Turtle scute |
| Nautilus Shell | — | furnace | Turtle scute |
| Elytra | — | furnace | Phantom membrane |
| Iron horse armor | — | crafting table | 3 Iron nuggets |
| Golden horse armor | — | crafting table | 3 Gold nuggets |
| Diamond horse armor | — | crafting table | 3 Diamonds |
| Bow / fishing rod | — | crafting table | 2 String |

## Uninstall

Remove the `.hmod` from `horizon-mods/` (or disable it in Options → Mods). Materials you
already smelted stay in your world; the recipes simply stop working.

## License

[MIT](LICENSE) — Copyright (c) 2026 CGRLabs.

Not an official Minecraft product. Not approved by or associated with Mojang or Microsoft.