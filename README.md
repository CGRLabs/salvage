# Salvage

A [Horizon](https://playhorizon.dev) content mod: the all-recycling mod. Smelt leather,
chainmail, wood, stone, bows, fishing rods, saddles and horse armor back into useful materials.

Nothing in that chest is trash anymore. That leather helmet from a zombie drop, the chainmail
chestplate you never use, the stone pickaxe you outgrew, the saddle from a horse you never
ride — put any of it in a furnace with any fuel and get materials back.

| Smelt this | Get this |
| --- | --- |
| Leather helmet / chestplate / leggings / boots | Leather |
| Leather horse armor | Leather |
| Saddle | Leather |
| Wooden sword / pickaxe / axe / shovel / hoe | Charcoal |
| Stone sword / pickaxe / axe / shovel / hoe | Cobblestone |
| Bow, fishing rod | String |
| Chainmail helmet / chestplate / leggings / boots | Iron nugget |
| Copper horse armor / nautilus armor | Copper nugget |
| Iron horse armor | Iron nugget |
| Golden horse armor | Gold nugget |
| Diamond horse armor | Diamond |
| Turtle Shell (turtle helmet) | Turtle scute |
| Nautilus Shell | Turtle scute |
| Elytra | Phantom membrane |

Every recipe takes about 10 seconds and gives a little experience.
Elytra and diamond horse armor take longer (20 seconds) and give more experience.
Stone tools are quicker (5 seconds).

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

Version 1.1 is 1 item in, 1 material out — the conservative, verified recipe format.
Vanilla already recycles iron and gold gear; this covers what vanilla leaves behind:
chainmail, leather, wooden and stone tools, bows, fishing rods, saddles and horse armor.

## Build from source

```sh
cargo install --git https://github.com/horizon-rust/horizon cargo-horizon-mod
cargo horizon-mod build
cargo horizon-mod check target/horizon-mod/salvage.hmod
```

The build is deterministic: the same sources produce the same file bytes.

## What's inside

Thirty furnace smelting recipes under `data/salvage/recipe/`, all using vanilla items
only. No new items, blocks or textures, and no Minecraft assets bundled.

| Category | Items | Output |
| --- | --- | --- |
| Leather armor | helmet, chestplate, leggings, boots | Leather |
| Leather horse armor | — | Leather |
| Saddle | — | Leather |
| Wooden tools | sword, pickaxe, axe, shovel, hoe | Charcoal |
| Stone tools | sword, pickaxe, axe, shovel, hoe | Cobblestone |
| Bow / fishing rod | — | String |
| Chainmail armor | helmet, chestplate, leggings, boots | Iron nugget |
| Copper horse armor / nautilus armor | — | Copper nugget |
| Iron horse armor | — | Iron nugget |
| Golden horse armor | — | Gold nugget |
| Diamond horse armor | — | Diamond |
| Turtle Shell | turtle helmet | Turtle scute |
| Nautilus Shell | — | Turtle scute |
| Elytra | — | Phantom membrane |

## Uninstall

Remove the `.hmod` from `horizon-mods/` (or disable it in Options → Mods). Materials you
already smelted stay in your world; the recipes simply stop working.

## License

[MIT](LICENSE) — Copyright (c) 2026 CGRLabs.

Not an official Minecraft product. Not approved by or associated with Mojang or Microsoft.