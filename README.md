# Salvage

A [Horizon](https://playhorizon.dev) content mod: smelt old gear back into useful materials.

That chest full of leather helmets from zombie drops, the saddle from a horse you never
ride, the wooden pickaxe you outgrew ten minutes in — none of it is trash anymore.
Put it in a furnace with any fuel and get materials back.

| Smelt this | Get this |
| --- | --- |
| Leather helmet / chestplate / leggings / boots | Leather |
| Leather horse armor, saddle | Leather |
| Wooden sword / pickaxe / axe / shovel / hoe | Charcoal |
| Bow, fishing rod | String |

Every recipe takes about 10 seconds and gives a little experience.

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

Version 1.0 is 1 item in, 1 material out — the conservative, verified recipe format.
Vanilla already recycles iron and gold gear; this covers what vanilla leaves behind.

## Build from source

```sh
cargo install --git https://github.com/horizon-rust/horizon cargo-horizon-mod
cargo horizon-mod build
cargo horizon-mod check target/horizon-mod/salvage.hmod
```

The build is deterministic: the same sources produce the same file bytes.

## What's inside

Thirteen furnace smelting recipes under `data/salvage/recipe/`, all using vanilla items
only. No new items, blocks or textures, and no Minecraft assets bundled.

## Uninstall

Remove the `.hmod` from `horizon-mods/` (or disable it in Options → Mods). Materials you
already smelted stay in your world; the recipes simply stop working.

## License

[MIT](LICENSE) — Copyright (c) 2026 CGRLabs.

Not an official Minecraft product. Not approved by or associated with Mojang or Microsoft.