# Aetheria Physics

Optional physics for Wrath 3.3.5a clients built on the Esteria / wowdecomp engine (the Aetheria client): **spring cloaks** on retail-skeleton characters, **soft-tissue jiggle** on the retail female bodies and the Sylvari female, **hair physics** for retail long hair, ponytails and beards, and an **optional add-on of the new female body models** these were made for.

Status words used here: **installed** = applied in the owner's test client; **accepted** = the owner tested it in game and approved it. Compiling is not acceptance.

## What is in this repository

| Folder | What | Status |
| --- | --- | --- |
| `client/Engine/Source/Retail/CapePhysics.h` | Cloak springs: a damped spring on each of the five cape bones (key bones 36-40), wind while running, rest flare for models whose cape chain is appended | accepted on Draenei, Night Elf and Sylvari female |
| `client/Engine/Source/Retail/JigglePhysics.h` | Breast bone springs and a rear spring that drives the rear mesh value | accepted on Human, Blood Elf, Night Elf, Draenei, Void Elf |
| `client/Engine/Source/Retail/HairPhysics.h` | Hair springs: chains of loose hair bones hanging from the head swing on turns and stops; front-hanging chains (beards) are limited so they do not clip the chest | accepted on Blood Elf female and Orc male |
| `patches/client-hair-physics-1.patch`, `-2.patch`, `client-sylvari-jiggle-profile.patch` | Apply in this order after the cloak patch: hair hooks, the hair retune and beard limit, and the Sylvari female body profile for the jiggle sliders | applied, built and accepted |
| `patches/client-cape-physics.patch` | The hooks for the cloak physics (state map in `BodyShape.h`, one call in `Unit_C.cpp`, options page, Lua commands), against the aetheria-client source as it stood on 2026-11-13 (jiggle hooks included) | applied, built and accepted |
| `models/` | Optional add-on: the female body replacers and the Sylvari female body, cape chain and retail cloaks (see below) | accepted |
| `tools/sylvari-model/` | Reference scripts that built the Sylvari female archive (shape transfer, cape chain, cloak shells). They use placeholder paths (`<WORK_DIR>` and so on) and need Kalibros' `wotlkconv` and StormLib; they are for reading, not one-click use | reference |
| `docs/HOW-IT-WORKS.md` | Design, options, console commands, tuned values | |

The physics code is **not** a stand-alone mod: it needs the Aetheria client source (`CM2Model` bone API, `BodyShape`, `Unit_C`). It lives in the main `aetheria-client` repository too; this repository is the physics-only copy with the add-on models.

## How to use it

### Physics only (no models)

1. Build your client from the Aetheria client source (or a tree with the same `CM2Model` bone API). If your tree is the current aetheria-client, the physics is already in it: nothing to copy.
2. Otherwise copy `client/Engine/Source/Retail/CapePhysics.h` and `JigglePhysics.h` into `Engine/Source/Retail/` and apply `patches/client-cape-physics.patch` (it adds the hooks and the options page). Build the client.
3. Start the game and open Interface > Aetheria Physics. Cloak physics is on by default; jiggle is off by default and applies only to retail female bodies, so turn it on there if you want it.
4. Cloaks then move on every character whose model has the retail cape chain: nearly all retail races and sexes, with your own cloak on. Jiggle works on the retail female bodies and does not need any model file.
5. Tune live with `/run CapeSet("gain", 2.5)` and `/run JiggleSet("breastGain", 1.4)`; `/run print(CapeStatus())` shows whether the chain was found on your character.

### Physics plus the add-on models

Do the physics steps above, then copy the archives from `models/` into the client `Data` folder, keeping the file names exactly (the names set the load order, longer names win). Start the game; you need nothing else.

- The replacer archives give the retail female races their new bodies. The physics picks them up with no extra step: jiggle uses the bones those bodies carry, and cloaks use their cape chain.
- The Sylvari archives add the new Sylvari female body, boots and the cape chain with the nine retail cloaks. Without them the Sylvari female keeps the older model, which has no cloaks at all, so there is nothing for the cloak physics to move.
- Install only the archives you want. To remove one, delete the file from `Data`.
- Do not copy the model archives into other places or share them (see Credits).

## Options and commands

Interface > Aetheria Physics (saved in `Config.wtf`):

| CVar | Default | Meaning |
| --- | --- | --- |
| `jigglePhysics` | 0 (off) | Master switch for the jiggle |
| `jiggleButt` | 1 | Include the rear once the master switch is on |
| `jiggleStrength` | 2 | 1 Subtle, 2 Natural, 3 Strong, 4 Exaggerated |
| `capePhysics` | 1 (on) | Cloak springs |
| `capeStrength` | 2 | Same four steps for cloaks |
| `hairPhysics` | 1 (on) | Hair springs |
| `hairStrength` | 2 | Same four steps for hair |

Live tuning from chat: `/run CapeSet("gain", 2.5)`, `/run JiggleSet("breastGain", 1.4)`; `CapeStatus()`, `JiggleStatus()` and `HairStatus()` report; `HairSet(name, value)` tunes the hair (names at the top of `HairPhysics.h`); what the client found on your model. Names are listed in `docs/HOW-IT-WORKS.md`.

## The add-on models (`models/`)

Female body replacers for retail races and the Sylvari female body, as client archives (MPQ) in the retail-ID override layout. **All of these come from the "Idealistic Physics" models by Rwise.** Rwise gave the repository owner permission to use and redistribute them with credit, and asked that they not be redistributed by anyone else: if you download them, please do not re-share them. See `CREDITS.md`.

| Archive | Gives |
| --- | --- |
| `...AetheriaRetailReplacerTest.MPQ` | Human, Blood Elf, Night Elf, Draenei, Nightborne, Void Elf and Lightforged females |
| `...AetheriaRetailReplacerHaranir.MPQ` | Haranir female |
| `...AetheriaRetailReplacerDracthyrTest.MPQ` | Dracthyr visage female |
| `...AetheriaRetailReplacerSkyborneTest.MPQ` | Skyborne female |
| `...AetheriaSylvariFemaleShape.MPQ` | Sylvari female body shape (Rwise's shape transferred onto the custom model) |
| `...AetheriaSylvariFemaleBoots.MPQ` | Sylvari female v6b: breast bones for the jiggle, Draenei-style boots and shin guards, a five-bone cape chain and the nine retail cloak shapes |

Put them in the client `Data` folder. The names sort by length, so later names override earlier ones; keep the names as they are. Remove an archive to go back. They contain no game files of Blizzard's own beyond what the models reference by ID. `MANIFEST.sha256` lists every file hash (text files are hashed in their committed LF form; check a fresh clone with `core.autocrlf=false`).

## Requirements and limits

- The Aetheria client (or another wowdecomp-based client with the same bone API) built from source; nothing here is a drop-in for a stock 3.3.5a client.
- The physics works on models with the retail cape chain (almost every retail race and sex). Models without it (Hozen, Harronir) are left alone.
- Jiggle needs the retail female body profile; it is off by default.
- Not yet done: a Sylvari male, hair physics for Hozen and Sylvari hair.

## Credits

See `CREDITS.md`. Ilusixn (the Hozen and Sylvari races), Rwise (models and the physics reference the jiggle is modelled on), Kalibros / STRHercules (frameworks and help), Medviten, Saty (x64 decompilation work).
