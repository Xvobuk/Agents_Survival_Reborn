# Agents Survival Reborn Development Chronicle

This file is the long-form development memory for the project. Every meaningful future change, QA pass, bug fix, mechanic expansion, and design decision should be appended here so the project has a readable history instead of scattered chat fragments.

## Purpose

Agents Survival Reborn is a PyGame survival sandbox where several AI-controlled player-characters enter the same tile world, believe the others are real players, gather resources, discover hidden recipes, craft tools and stations, talk through local chat, and try to survive and progress. The spectator can move around the map, inspect players, read the full chat, and record gameplay.

The long-term direction is not a scripted toy. The goal is a living sandbox:

- agents make decisions through a local generative model when available;
- agents remember enough context to behave like continuing people;
- chat is occasional, useful, and human-like rather than status spam;
- LLM hallucinations can become new mechanics when they are good ideas;
- bad hallucinations are filtered before they poison memory or chat;
- the world contains resources, biomes, wildlife, crafting, building, eating, cooking, and visible progression;
- placeholder art is acceptable until real sprites are supplied.

## Initial Rebuild

The project was rebuilt in `F:\python_projects\agents_survival_reborn` as a fresh Python/PyGame project. The earlier prototype was considered too chaotic and too visually poor, so the new version was structured around data-driven terrain, features, items, recipes, agents, rendering, and LLM decisions.

Core systems created:

- `run.py` entrypoint.
- `agents_survival_reborn/data.py` for terrain, features, items, recipes, and sprite specs.
- `agents_survival_reborn/world.py` for procedural world generation and tile interactions.
- `agents_survival_reborn/agent.py` for personas, inventory, memory, needs, and tools.
- `agents_survival_reborn/simulation.py` for turn processing, LLM context, action validation, chat, logging, and fallback behavior.
- `agents_survival_reborn/llm.py` for OpenAI-compatible and Ollama/local model calls.
- `agents_survival_reborn/renderer.py` for PyGame world/HUD drawing.
- `agents_survival_reborn/assets.py` for sprite loading, missing sprite reports, asset wizard, and placeholders.
- `agents_survival_reborn/recorder.py` for gameplay video recording.
- `agents_survival_reborn/journal.py` for JSONL logs.

## World And Biomes

The world is a 2D tile grid with procedural terrain. Current terrain includes:

- deep water;
- shallow water;
- coast;
- sand;
- grassland;
- meadow;
- forest floor;
- rocky cliffs;
- hills;
- clay hills;
- swamp;
- snowfield;
- tundra;
- jungle;
- mushroom grove;
- badlands.

The generator uses layered noise for height, moisture, and temperature, then adjusts coasts near water. Feature placement is terrain-aware.

Original feature categories included:

- desert/coast resources: cactus, crab, reeds, sand/coast loot;
- water resources: fish school, kelp, reef;
- plants: tall grass, flower patch, berry bush, herbs, mushrooms;
- trees: birch, oak, pine, fruit tree;
- rock and mining: stone outcrop, cave mouth, coal/copper/iron/gold/diamond veins, clay patch;
- snowdrift;
- stations: workbench, campfire, kiln.

Later, more animals and fish were added:

- rabbit;
- deer;
- fox;
- boar;
- frog;
- duck;
- gull;
- turtle;
- salmon school;
- eel.

Wildlife is still represented as tile features, not a full ECS/entity layer. This was intentional as a compact first step: it keeps interaction, rendering, loot, and sprite handling simple while making the world visibly alive.

## Wildlife Movement

Wildlife movement was added in `World.advance_wildlife`.

Behavior:

- runs after all agents finish their round;
- only moves features tagged as `animal` or `fish`;
- never moves onto an occupied agent tile;
- never moves onto another feature;
- respects terrain constraints;
- has per-species movement probabilities.

Movement rules:

- crabs move on sand/coast;
- fish schools, salmon schools, and eels move in water;
- rabbits move on grass, meadow, forest floor, and tundra;
- deer, foxes, and boars move through forests, jungles, meadows, grass, and mushroom groves;
- frogs and ducks prefer wet zones, swamp, coast, and shallow water;
- gulls and turtles stay near coast/sand.

This made crabs stop behaving like decorative rocks and start wandering on beaches.

## Agents And Personas

Agents are distinct persona-driven player-characters. Current personas include:

- Aiden, builder: ex-carpenter, wants the strongest base and every station.
- Mira, miner: prospector, wants metal tools before everyone else.
- Noah, provider: coastal fisher, wants food security.
- Ivy, explorer: mapmaker, wants rare biomes, caves, and routes.
- Leo, forager: herbalist, wants plant uses and early crafting.
- Zara, solo/competitive: wants to out-progress others.
- Owen, trader: wants trade and recipe knowledge.
- Nia, minmaxer: wants efficient tech progression.
- Caleb, cook: wants cooked food and camp stability.
- Sera, tinkerer: wants utility recipes and clever tool chains.

Earlier issues:

- agents talked constantly;
- agents often said coordinates for no reason;
- agents narrated every move;
- agents repeated the same plan, especially Aiden obsessing over pickaxes/campfires;
- agents did not seem to hear or remember chat well;
- agents invented fake players, professions, map data, and recipes.

Fixes added:

- stronger per-persona prompts;
- recent speech, thoughts, actions, heard chat, and private memory passed into context;
- fresh nearby chat separated from older heard chat;
- fresh questions identified and prioritized;
- speech can accompany useful non-talk actions;
- talking is converted to interact when there is a useful nearby resource;
- useless/vague movement can be converted to nearby interaction;
- invalid craft/place can be replaced with known craft, experiment, or immediate interaction.

## Local LLM Integration

The project supports local models through Ollama. The user has `qwen2.5:7b` available.

The usual command for full game mode:

```powershell
cd F:\python_projects\agents_survival_reborn
.\.venv\Scripts\python.exe run.py --llama --model qwen2.5:7b --agents 2 --round-frames 60 --llm-workers 1 --llm-timeout 120 --llm-max-output-tokens 900 --no-record
```

The usual QA command:

```powershell
.\.venv\Scripts\python.exe tools\run_social_qa.py --rounds 8 --agents 3 --cluster --model qwen2.5:7b --provider ollama --base-url http://localhost:11434 --timeout 120 --workers 1 --max-output-tokens 900
```

Ollama note:

- If `ollama serve` says port `127.0.0.1:11434` is already in use, that usually means the Ollama service is already running.
- `ollama list` confirmed `qwen2.5:7b`.

The user realized the agents were genuinely thinking and acting through a local generative model on the machine, which became an important design direction.

## LLM Output Repair And Filtering

Qwen often returned unwanted JSON-like world-generation blocks instead of decisions. The LLM layer was hardened:

- strict decision schema;
- expected keys: `action`, `dx`, `dy`, `target_dx`, `target_dy`, `recipe_id`, `place_item`, `speech`, `private_memory`, `intent`, `thought`;
- repair/extraction from imperfect JSON;
- fallback behavior if the LLM times out or returns malformed output;
- local model prompts that explicitly say the input is game state, not a request to generate a map.

The system now logs LLM success, fallback count, duration, and last errors in the HUD.

## Chat, Thoughts, And Logs

A run logger was added. Each session writes logs under:

```text
logs/session_YYYYMMDD_HHMMSS/
```

Important files:

- `chat.jsonl`: public chat messages.
- `thoughts.jsonl`: per-agent thought, intent, action, speech filtering result, private memory delta, fresh question context, and recent heard chat.
- `turns.jsonl`: applied action results, inventory, positions, thoughts.

This was added because the user wanted to inspect not only what agents say, but also what they think, and whether the thinking is human-like.

Chat rules evolved heavily:

- no status updates like "I move left" or "I'll gather wood";
- no repeated goal spam;
- no coordinate spam unless useful;
- no AI/bot/prompt/model/schema/NPC mentions;
- no fake roles/players;
- no non-ASCII chat;
- no empty greeting filler;
- no low-value weather/view filler;
- no generic "Need any help?" without concrete help;
- direct questions should be answered directly, not with a similar question back;
- a reply must address the actual question;
- speech is allowed only if someone nearby can hear it, except emergencies;
- recent global chat similarity blocks repeated ideas.

## Private Memory Validation

Private memory is filtered because bad memory poisons later decisions.

Blocked memory examples:

- fake `Player1`;
- fake `nearby player`;
- invented `Woodcutter (Xiao)` or `Miner (Feng)`;
- fake villagers, blacksmiths, cabins;
- unsupported items such as rope, cloth, wool;
- claims about placed/crafted/found/discovered items unless the event actually happened;
- future intentions such as "I will move left later";
- fake coordinates unrelated to current movement/place actions.

Allowed memory examples:

- real recipe discoveries;
- real nearby resource observations;
- actual heard chat;
- actual inventory facts;
- completed recent actions.

## Social QA Tool

`tools/run_social_qa.py` was added for headless testing. It can cluster agents near each other, run rounds without opening PyGame, use local Ollama, and summarize:

- chat lines;
- speakers;
- blocked speech reasons;
- action counts;
- last chat;
- last thoughts.

This tool became the main autonomous QA loop.

## Sprites And Atlas Extraction

The user generated a sprite atlas with ChatGPT Image. It contained terrain tiles, plants, rocks, ores, tools, foods, stations, agents, hearts, stamina-like icons, and many additional items.

A sprite extraction pipeline was created earlier. The first pass had magenta background remnants because ChatGPT varied the exact pink color. The alpha cleanup was improved so near-magenta outlines are removed more robustly.

The asset system:

- loads sprites from `assets/sprites`;
- uses exact filenames from `sprite_specs`;
- falls back to generated placeholders;
- writes `docs/missing_sprites.md`.

The user requested no new sprite work for some later mechanics, so new objects such as tent/animals use placeholders until sprites are supplied.

## Crafting And Items

Recipes are hidden from agents until discovered. Agents can learn through experimentation when ingredients and station availability match undiscovered recipes.

Current recipe categories:

- handcraft basics: Cordage, sticks, planks;
- early tools: stone knife, axe, shovel, pickaxe, spear, fishing rod;
- stations: workbench, campfire, kiln;
- fishing: fish net;
- cooking: cooked fish, cooked crab, cooked meat, fried egg, camp bread, charcoal;
- light: torch;
- smelting: copper/iron ingots;
- building and utility: wooden shield, crate, door, bedroll, sack, bow, arrows;
- advanced pickaxes: copper, iron, diamond;
- shelter: tent.

Important exact recipe added from user request:

```text
Tent: 3 Pine log + 10 Stick -> 1 Tent @ Workbench
```

Campfire already existed:

```text
Campfire: 5 Stone + 3 Stick + 1 any fiber -> 1 Campfire @ handcraft
```

## Placeable Items

A general `PLACEABLE_ITEMS` set was added instead of hardcoding only workbench/campfire/kiln.

Current placeable items:

- workbench;
- campfire;
- kiln;
- tent;
- wooden crate;
- wooden door;
- bedroll.

Changes:

- `world.place_station` now accepts all placeables.
- `simulation._place` validates against `PLACEABLE_ITEMS`.
- LLM `place_item` enum includes all placeables.
- context exposes `placeable_inventory`.
- immediate actions show `place` when an item can be placed on the current tile.

Tent interaction:

- placing creates a `tent` feature;
- interacting with it restores energy and costs a little hunger.

Bedroll interaction:

- restores less energy than tent;
- costs a little hunger.

## Food And Hunger

Food originally existed only as item `food` values plus a late auto-eat threshold. Agents could walk around hungry while carrying food, which looked wrong.

Food mechanics were improved:

- `Agent.eat_best_food` now chooses food smarter;
- it tries not to waste large food when a smaller item is enough;
- cooked food gets preference;
- raw food is allowed but applies a small health/energy penalty;
- cooked food gives a small health/energy benefit;
- hunger restoration is shown in action text;
- auto-eating triggers earlier when hunger is low and food is available;
- fallback/scripted mode eats at a higher threshold;
- `food_inventory` is included in the LLM context;
- `hunger_state` is included in the LLM context;
- `eat` appears in `immediate_actions` when useful;
- LLM prompt says to eat below 60 hunger unless something more urgent is happening;
- LLM prompt says to cook raw fish/meat/crab/eggs at a campfire when possible.

HUD improvements:

- old single text line `HP Hunger Energy` was replaced with icon rows and bars;
- uses `ui_health`, `ui_hunger`, `ui_energy`;
- if sprites are missing, placeholders are used;
- current project has `ui_health.png`, `ui_hunger.png`, `ui_energy.png`, and `ui_unknown.png`.

Validation performed:

- cooked fish chosen before raw meat;
- raw meat works but applies penalty;
- auto-eat interrupts routine movement when hungry;
- LLM context includes `food_inventory`;
- `eat` appears in immediate actions;
- headless PyGame render test succeeded.

## Survival Needs

Agents currently track:

- health;
- hunger;
- energy.

Need ticking:

- hunger slowly decreases every turn;
- energy slowly regenerates passively;
- starvation damages health;
- high hunger slowly heals.

Movement costs energy. Rest features such as tent and bedroll restore energy.

This is still early. Possible future directions:

- thirst;
- temperature;
- sleep cycles;
- injury;
- sickness from raw food;
- morale;
- camp warmth from fire;
- better rest actions.

## HUD And Spectator Experience

The spectator can:

- move around the world;
- select/follow agents;
- read full chat;
- inspect current agent status, origin, goal, intent, thought, last action, and inventory;
- see minimap;
- see LLM status and errors;
- record gameplay video.

The HUD has been gradually improved:

- thought display added;
- LLM status and fallback counters added;
- chat display preserved;
- icon-based stat bars added for health, hunger, and energy.

## Recording

Gameplay video recording exists and saves to `gameplay_videos`. Earlier recording was configured for 30 FPS. No recent changes were made to recording during the food/wildlife/placeable work.

## Known Current Weaknesses

These are not necessarily bugs, but useful future targets.

### Wildlife Is Still Feature-Based

Animals and fish are tile features. This works for movement and interaction but limits:

- multiple entities on one tile;
- animal health state separate from tile HP;
- pathfinding;
- fleeing/chasing;
- reproduction;
- predator behavior;
- smooth independent animation.

A future entity layer would be cleaner if wildlife becomes central.

### Combat/Hunting Is Minimal

Animals can be interacted with and loot drops, but there is no rich combat. Some animals require tools such as spear or bow. There is no fleeing, danger, wound system, or animal aggression yet.

### Cooking Is Recipe-Based But Agent Understanding Needs QA

Cooked recipes exist and LLM is prompted to cook raw food when possible. More QA is needed to ensure agents actually place campfires and cook instead of eating raw food too often.

### Craft Discovery Is Still Hard

Recipes are hidden, as desired, but local models can get stuck repeating guesses. The system partially solves this with `experiment` and productive replacements. More recipe hints, world affordances, and social learning could help.

### Storage Is Cosmetic

Wooden crates can be placed, but they do not yet store items. This is an obvious next mechanic.

### Doors Are Cosmetic

Wooden doors can be placed, but there is not yet wall/base collision or real door behavior.

### Tent And Bedroll Are Simple

They restore energy but do not create a saved camp, sleep cycle, ownership, warmth, or safety.

## Autonomous QA Automation

The heartbeat automation `agent-social-qa-continuation` was updated and renamed to:

```text
Agents Survival Reborn autonomous dev QA
```

The automation now asks future runs to:

- continue autonomous development QA for `F:\python_projects\agents_survival_reborn`;
- run or inspect headless local-Ollama simulations with `qwen2.5:7b` when useful;
- inspect latest `logs/session_*/chat.jsonl`, `thoughts.jsonl`, and `turns.jsonl`;
- evaluate agent behavior, chat realism, memory continuity, survival progress, crafting progression, placeable item usage, hunger/eating decisions, cooking behavior, wildlife movement, fishing, mobs/animals, HUD regressions, and sandbox playability;
- make focused fixes when clear;
- verify with `compileall`, targeted checks, or smoke tests;
- clean `__pycache__`;
- append every meaningful change/test/finding to this file before reporting concise progress.

## Verification Commands Commonly Used

Compile:

```powershell
.\.venv\Scripts\python.exe -m compileall agents_survival_reborn tools\run_social_qa.py
```

Social QA:

```powershell
.\.venv\Scripts\python.exe tools\run_social_qa.py --rounds 6 --agents 3 --cluster --model qwen2.5:7b --provider ollama --base-url http://localhost:11434 --timeout 120 --workers 1 --max-output-tokens 900
```

Clean Python caches:

```powershell
$project = Resolve-Path 'F:\python_projects\agents_survival_reborn'
Get-ChildItem -Path $project -Recurse -Directory -Filter '__pycache__' | ForEach-Object {
    $target = Resolve-Path -LiteralPath $_.FullName
    if ($target.Path.StartsWith($project.Path, [System.StringComparison]::OrdinalIgnoreCase)) {
        Remove-Item -LiteralPath $target.Path -Recurse -Force -ErrorAction SilentlyContinue
    }
}
```

## 2026-06-07: Chronicle Created And Automation Updated

Created this chronicle file at:

```text
F:\python_projects\agents_survival_reborn\docs\development_chronicle.md
```

Updated the heartbeat automation so future autonomous QA explicitly includes:

- survival mechanics;
- food and hunger;
- cooking behavior;
- wildlife/mobs/fish;
- placeable item use;
- crafting progression;
- HUD regressions;
- maintaining this chronicle.

This entry is the baseline. Future changes should be appended below with date, files touched, reason, implementation notes, and verification.

## 2026-06-07: Anti-Grind Progression Breaker

Reason:

The first autonomous development QA pass after the food, wildlife, and placeable work showed a clear sandbox progression problem. A fresh Qwen run completed successfully with no LLM fallbacks, but the agents spent nearly every turn repeatedly foraging meadow/grass ground. They accumulated enough `Grass fiber` and `Stick` to discover or craft useful recipes, yet their vague `move` decisions were repeatedly converted into more `interact` actions. This made them look busy but not meaningfully progressive.

Observed QA session:

```text
logs/session_20260607_002037
```

Symptoms:

- 8 rounds produced 22 `interact` actions and only 2 `move` actions.
- 0 `experiment` actions.
- 0 `craft` actions.
- Aiden reached 17 `Grass fiber` and 5 `Stick` while still foraging.
- Noah and Mira also kept gathering routine ground resources.
- Chat stayed silent because generated speech was mostly correctly blocked status narration.
- Thoughts sometimes contained model-meta phrasing such as "The player wants..." or artificial social intent.

Implementation:

- Added `_should_break_gather_loop` in `simulation.py`.
- If an agent has repeated routine gathering in recent actions and known/discoverable recipes exist, a routine `move`, `interact`, or `talk` decision can be converted into progression via `_productive_replacement`.
- The breaker also triggers when an agent has enough `Grass fiber` to discover `Cordage` but has not learned it yet.
- Added turn guidance telling the LLM not to repeat ground-foraging loops when craft/experiment progression is available.
- Added a local LLM prompt sentence: progression beats another handful of grass.
- Improved thought polishing so spectator thoughts that look like model-meta/user-control text are replaced with in-character useful thoughts.
- Expanded private memory filtering so future-plan notes like "I should explore later" are not stored as factual memory.

Validation:

Controlled test:

- Agent with 9 `Grass fiber` and repeated `foraged ground cover` history had a vague `move` replaced with `experiment`.
- The resulting event discovered `Cordage` and made 1 `Cordage`.
- After discovery, repeated gathering was replaced with `craft cordage_from_fiber`.
- Future private memory line `I should explore later.` was correctly rejected.

Fresh Qwen QA session:

```text
logs/session_20260607_002529
```

Result:

- 8 rounds produced 13 `interact`, 4 `move`, 2 `experiment`, and 5 `craft` actions.
- Agents discovered and crafted `Cordage`.
- Mira interacted with a rabbit and got `Raw meat`, confirming wildlife remains useful in the resource loop.
- Status-update speech was still blocked.

Remaining issue:

The agents can now overproduce `Cordage` if that is the only known craftable recipe. This is acceptable for the moment because Cordage is a core early material, but future crafting priority should account for stockpiles and next-step recipe goals.

## 2026-06-07: Craft Priority And Phantom Place Plan Guard

Reason:

The next heartbeat QA pass focused on the remaining issue from the anti-grind work: agents could still overproduce `Cordage` because the simulation selected the first known craftable recipe without judging stockpiles or strategic value. A fresh Qwen run also revealed a second issue: an agent could spend movement turns planning to place a `Wooden crate` even though it did not own one and did not know/craft it yet.

Observed QA session:

```text
logs/session_20260607_004203
```

Good signs:

- LLM calls were stable: 8 rounds, all ok, no fallback.
- The anti-grind breaker still worked.
- Agents discovered `Cordage`.
- Agents crafted at least one `Cordage`.
- Noah asked a real crafting question instead of only narrating movement.

Problems:

- Craft selection needed a notion of stockpile caps and strategic priority.
- Noah repeatedly generated "place wooden crate" plans without having a crate.

Implementation:

- Added `_best_known_craft` in `simulation.py`.
- Added `_craft_priority` to rank known craftable recipes.
- Priorities now prefer cooked food when relevant, missing stations, missing tools, useful placeables, then bounded intermediate materials.
- Added soft caps:
  - `Cordage` is useful until 4 in inventory.
  - `Stick` is useful until 10.
  - `Plank` is useful until 12.
  - `Arrow` is useful until 16.
- Updated `_productive_replacement` and fallback decisions to use `_best_known_craft` instead of blindly taking the first recipe.
- Added `_looks_like_invalid_place_plan`.
- If an agent attempts to move/interact/talk while its intent/speech/thought/private memory clearly says it will place a specific placeable item it does not own, the decision is redirected into productive replacement.

Validation:

Controlled craft priority test:

- With 9 `Grass fiber` and 0 `Cordage`, best craft is `cordage_from_fiber`.
- With 9 `Grass fiber` and 4 `Cordage`, no more Cordage craft is selected.
- With 4 `Cordage`, 2 `Stone`, and 1 `Stick`, `stone_axe` beats more Cordage.

Controlled phantom-place test:

- A move decision saying "place a wooden crate" without a crate in inventory was replaced with `experiment`.

Verification:

- `compileall` passed.

Remaining issue:

Placeable/base-building goals are still mostly aspirational until agents reliably get logs, planks, workbench, and storage recipes. Next useful direction is either better tree/tool progression or a richer station/base loop.

## 2026-06-07: Wooden Pickaxe And Better Discovery Priority

Reason:

A follow-up Qwen QA pass showed that the model repeatedly fantasized about crafting a `Wooden pickaxe`, especially while trying to progress toward campfires, crates, or mining. Previously this was only an invalid/hallucinated plan. Since a weak early pickaxe is a sensible sandbox item, the idea was promoted into a real mechanic instead of merely being filtered.

Observed QA session:

```text
logs/session_20260607_005028
```

Findings:

- The earlier craft-priority fix reduced blind Cordage overproduction but did not solve early tool progression.
- A status line `Heading north to check the flower patch.` slipped into chat because the status filter covered `heading toward`, but not bare compass directions.
- Agents continued to mention wooden pickaxes, which did not exist.
- Recipe discovery still selected the first discoverable recipe in data order, not the most strategically useful hidden recipe.

Implementation:

- Added `Wooden pickaxe` item in `data.py`.
- Recipe:

```text
Wooden pickaxe: 3 Stick + 1 Cordage + 1 Flint -> 1 Wooden pickaxe @ handcraft
```

- Tool stats:
  - tags: `pickaxe`, `mine`;
  - power: 1;
  - durability: 32.
- Added bare-direction status filtering for phrases such as `Heading north`.
- Added `_best_discoverable` in `simulation.py`.
- Experimenting now chooses hidden recipes through the same priority model used for known craft selection.
- Tool discovery priority now prefers missing pickaxes before less progression-critical tools.
- Fallback decisions now use prioritized discovery too.

Validation:

Controlled test:

- With `3 Stick`, `1 Cordage`, and `1 Flint`, `_best_discoverable` selects `wooden_pickaxe`.
- `_experiment` discovers `Wooden pickaxe` and crafts it immediately.
- The resulting tool is available through `best_tool("pickaxe", 1)`.
- `Heading north to check the flower patch.` is now classified as status-update speech.

Fresh Qwen smoke session:

```text
logs/session_20260607_005459
```

Result:

- 6 rounds completed with no fallbacks.
- Progression through `experiment` and `craft` still works.
- The short run did not reach Flint and therefore did not naturally craft a wooden pickaxe, but the controlled mechanic path is verified.

Remaining issue:

Early progression still depends on finding Flint or Stone. Agents often stay in meadow starts, so the next useful improvement may be stronger exploration pressure toward rock/sand/forest targets once basic fiber resources are stocked.

## 2026-06-07: Progress Exploration Toward Stone, Sand, And Trees

Reason:

After adding `Wooden pickaxe`, the next QA pass showed that agents could still remain in meadow starts for too long. They progressed through `Cordage`, but once the basic fiber loop was mostly exhausted they needed stronger pressure toward Flint, Stone, logs, trees, sand, rock, or forest targets.

Observed QA session:

```text
logs/session_20260607_010211
```

Findings:

- Agents continued to open and craft `Cordage`.
- Bare-direction status speech such as `Heading north...` was correctly blocked after the previous filter update.
- Agents still did not reliably leave meadow starts in short runs.
- One private-memory hallucination slipped through: `Collected some wood from a nearby birch tree` after a meadow foraging action.

Implementation:

- Added `_progress_exploration_move` in `simulation.py`.
- If a vague movement decision happens after the agent has enough basic fiber/Cordage/sticks but lacks progress materials, the movement can be redirected toward the best visible progression target.
- Visible progression targets are ranked:
  - stone/rock/ore feature;
  - tree feature;
  - rock/hill terrain;
  - sand/dry terrain;
  - forest terrain.
- Added `_needs_progress_exploration` and `_best_visible_progress_target`.
- Added `_sign` helper for one-step movement toward a target.
- Tightened private-memory validation:
  - `collected`, `harvested`, `foraged`, and `gathered` claims must match the actual event verb;
  - tree claims are rejected if the event did not involve a tree.

Validation:

Controlled test:

- Agent with `4 Cordage`, `3 Stick`, and meadow-foraging history redirected a vague move toward a visible `Stone outcrop`.
- Fake memory `Collected some wood from a nearby birch tree.` after meadow foraging was rejected.

Qwen smoke:

- `logs/session_20260607_010211` completed 6 rounds, no fallbacks.
- Actions still included `experiment` and `craft`; the new progression redirection is ready for longer runs where agents have exhausted immediate recipe progress.

Remaining issue:

The short clustered QA starts may not expose enough visible rock/sand/forest targets. A future QA tool option could spawn agents near mixed-biome boundaries or run longer travel tests specifically for tech progression.

## 2026-06-07: Mixed-Biome QA Mode And Stricter LLM Sanitization

Reason:

The previous entry identified that the clustered QA start often placed agents in a meadow-heavy pocket. That was useful for chat and early fiber testing, but weak for tech-path QA. A richer test start was needed so the local model could see trees, stone, coast/sand, clay, animals, and ore-adjacent terrain in the same viewing radius.

Implementation:

- Added `--mixed-biome` to `tools/run_social_qa.py`.
- `--mixed-biome` clusters agents near the highest-scoring passable location found on the generated map.
- The score rewards nearby useful terrain and feature tags:
  - grass;
  - forest;
  - rock;
  - sand;
  - hill;
  - clay;
  - coast;
  - water;
  - tree;
  - stone/rock/ore;
  - food;
  - animal;
  - fish.
- Added README documentation for `--mixed-biome`.

Validation:

Offline mixed-biome run:

```text
logs/session_20260607_011118
```

The chosen start had nearby:

- clay hills;
- coast;
- grass;
- meadow;
- birch tree;
- clay patch;
- copper vein;
- flower patch;
- rabbit;
- stone outcrop.

Qwen mixed-biome smoke run:

```text
logs/session_20260607_011128
```

Good signs:

- Qwen completed 6 rounds without fallbacks.
- Agents performed movement, interaction, experiment, and craft.
- `progress exploration` activated and redirected agents toward a `Stone outcrop`.

New issues found:

- The model produced non-English/non-ASCII thoughts and private memory in one turn.
- A fake memory about a found `Wooden crate` slipped through after ordinary foraging.
- Status speech about cutting/chopping wood needed better filtering.

Follow-up implementation:

- Non-ASCII private memory is now rejected.
- Non-ASCII thoughts are replaced with a fallback in-character thought.
- Private memory mentioning a crate is rejected unless the actual event involved a crate.
- Status filtering now catches `chop`, `chopping`, `cut`, and `cutting`.
- Status filtering now catches `before I can place`.

Verification:

- `I will cut some wood to make a wooden crate.` is now status-update speech.
- `I'll need to chop down a birch tree first before I can place the wooden crate.` is status-update speech.
- Non-ASCII private memory is rejected.
- Non-ASCII thought text falls back to an English in-character line.
- `compileall` passed.

Remaining issue:

Mixed-biome QA exposed a strong obsession with crates/campfires before agents have the required placeable item. The current guard prevents bad actions, but a better future step is to teach the context to show missing prerequisites for desired placeables more explicitly.

## 2026-06-07: Mixed-Biome Long QA And Chat Meta Cleanup

Reason:

A longer mixed-biome Qwen run was used to test whether agents could progress beyond meadow foraging into movement toward stone and clay. The run showed good mechanical progress but exposed several accepted chat lines that were still not human-like player communication.

Observed QA session:

```text
logs/session_20260607_012029
```

Good signs:

- 10 rounds completed with no LLM fallbacks.
- Actions included movement, interaction, experiment, and craft.
- Progress exploration repeatedly redirected Noah toward a `Stone outcrop`.
- Mira dug `Clay lump` from clay hills.
- Agents continued to discover and craft `Cordage`.

Problems:

- Accepted chat included status/meta lines:
  - `Let's move east a bit and check if there are any resources nearby.`
  - `I'll plant a birch tree and place a bedroll nearby.`
  - `You are already in the center of the map. What would you like to do?`
- Private memory accepted a future-plan note: `I am moving to the left...`

Implementation:

- Expanded status speech filters to catch:
  - `let's move`;
  - `let's start`;
  - `plant` and `planting`;
  - `what would you like to do`;
  - `center of the map`.
- Added a pre-question meta check in `_is_status_update_speech` so `What would you like to do?` is blocked even though it contains a question mark.
- Expanded private-memory future-plan rejection to catch `I am...` and `I'm...` notes.

Validation:

Targeted tests confirmed:

- `Let's move east a bit and check if there are any resources nearby.` is blocked as status speech.
- `I'll plant a birch tree and place a bedroll nearby.` is blocked as status speech.
- `You are already in the center of the map. What would you like to do?` is blocked as status/meta speech.
- `I am moving to the left...` is rejected from private memory.
- `compileall` passed.

Remaining issue:

Agents still generate these weak lines internally, even though filters now block them. Future prompt/context work should reduce the generation rate, not only filter the output.

## 2026-06-07 01:46 +03: Result-Claim Filter And Place-Action Context

Reason:

The post-filter mixed-biome Qwen run showed that no hard failures occurred, but two bad chat lines still escaped:

- `I've placed a bedroll next to the birch tree. Now I can rest here.`
- `I'll need some wood to make a campfire.`

The first line was especially harmful because the real action was an experiment, not a placement. The agent was narrating an imagined completed action.

Observed QA sessions:

```text
logs/session_20260607_013413
logs/session_20260607_013808
logs/session_20260607_014204
logs/session_20260607_014502
```

Implementation:

- Added a post-action speech truth check in `Simulation._speech_result_block_reason`.
- Blocked speech that claims a completed `placed`, `set up`, `built`, `crafted`, `made`, `found`, `got`, or `caught` action when the actual `RoundEvent` result does not support it.
- Added a specific guard for `Now I can rest here` unless the current turn actually placed something.
- Expanded status speech filters for lines such as `I'll need some wood to make a campfire`.
- Added the bad bedroll and campfire lines to blocked speech examples in the game context.
- Strengthened the LLM developer prompt so agents must not claim placement/crafting/discovery unless `recent_actions` proves it happened.
- Made `available_actions` dynamic: `place` is now omitted when the agent has no placeable item in inventory.
- Added `forbidden_actions` to the per-agent context, currently listing `place` when the action is invalid this turn.
- Added explicit turn guidance: use `place` only when it appears in `available_actions` and the exact item appears in `placeable_inventory`.
- Strengthened the LLM prompt: action must be one of `available_actions`, and anything in `forbidden_actions` must not be chosen.
- Polished fallback thoughts so non-English or meta thoughts no longer become lines like `I am focusing on this next step: move`.
- Expanded meta-thought cleanup for phrases such as `player is already` and `desired location`.

Validation:

- Targeted checks confirmed:
  - `I'll need some wood to make a campfire.` is treated as status speech.
  - `I've placed a bedroll...` is blocked after an unrelated experiment result.
  - The same bedroll line is allowed by the result-claim check when the event result is actually `placed Bedroll`.
  - A starting agent with no placeable inventory no longer receives `place` in `available_actions`.
  - Meta thought `No immediate action needed as the player is already in the desired location.` is replaced with a natural movement thought.
- `logs/session_20260607_013808` after the result-claim filter had zero accepted chat lines; bad placement/status narration was blocked.
- `logs/session_20260607_014204` after dynamic `available_actions` still showed Qwen sometimes narrating imagined placement in speech, but none reached chat.
- `logs/session_20260607_014502` after `forbidden_actions` had no requested `place` action in the first four rounds, though one imagined placement line still appeared inside blocked speech.

Current read:

The visible chat is now much safer: the agents are not broadcasting fake completed actions or constant campfire/bedroll chatter. The model still sometimes generates action narration internally, but the simulator catches it and redirects the actual move into useful interact/experiment behavior. The next worthwhile improvement is not another broad filter; it is probably better progression pressure toward stone/log acquisition so agents can actually craft the campfire/workbench chain they keep wanting.

## 2026-06-07 02:03 +03: Early Stone And Tool Progression Bridge

Reason:

The next QA pass showed that agents were safer in chat but still struggled to turn early junk into actual progression. They wanted campfires, workbenches, doors, and crates, but the stone/wood chain was too brittle:

- `Pebble` was available early but mostly behaved like a dead-end item.
- Trees required an axe for real logs.
- Stone outcrops required a pickaxe for real stone.
- Agents near clay could keep digging clay forever because it was the nearest easy interaction.
- Mira reached `2 Pebble + Cordage` but lacked a `Stick`, so she could not make the new early axe bridge.

Observed QA sessions:

```text
logs/session_20260607_015039
logs/session_20260607_015517
logs/session_20260607_020006
```

Implementation:

- Added `stone_from_pebbles` recipe:
  - `3 Pebble -> 1 Stone`
  - In-game name: `Knapped stone`.
- Added `pebble_axe` recipe:
  - `2 Pebble + 1 Stick + 1 Cordage -> 1 Stone axe`
  - This gives agents a realistic way to reach tree chopping before they have full stone supply.
- Updated craft priority so `Knapped stone` is useful while the agent has fewer than 5 `Stone`.
- Expanded progression exploration:
  - It no longer stops just because the agent found one progress material.
  - It now considers whether the agent still needs material for axe, pickaxe, campfire, workbench, logs, or a missing stick handle.
  - If the agent has a tool head plus `Cordage` but no `Stick`, grass/forest/tree targets become high priority.
- Changed adjacent progress targets:
  - If the best progress target is already adjacent, the agent now `interact`s with it instead of trying to move onto or through it.
  - This fixes nearby trees/rock/forest targets that are useful but not always enterable.
- Improved no-tool feature interaction:
  - Trees without an axe can yield occasional `Stick`.
  - Rock/stone/ore features without a pickaxe can yield occasional `Pebble` and sometimes `Flint`.
  - Full harvesting still requires the proper tool.

Validation:

- Targeted recipe checks confirmed:
  - With `Grass fiber + Stick + Pebble`, agents can discover `Cordage` first.
  - With `Cordage + Stick + Pebble`, agents prefer `pebble_axe`.
- Targeted progression checks confirmed:
  - An agent with `2 Pebble + Cordage` and no `Stick` now enters progress exploration.
  - Adjacent progress targets return an `interact` decision instead of failing movement.
- Targeted world checks confirmed:
  - Stone outcrops without a pickaxe still sometimes say `needs pickaxe`, but can now also yield `Pebble` and `Flint` through weak manual picking.
- `logs/session_20260607_020006` confirmed the adjacent-target change in a real Qwen run: Aiden interacted with a nearby `Stone outcrop` through progression redirection.

Current read:

The early survival chain is more playable now: grass/forest gives sticks, pebbles can become stone or a crude axe, and stone outcrops are no longer absolute dead ends before a pickaxe. The next obvious QA target is whether agents actually craft `Stone axe`, chop logs, then craft/place `Workbench` or `Campfire` in a longer run.

## 2026-06-07 12:14 +03: Inventory Limits, Replay Files, And Sprite Placeholders

Reason:

The user confirmed that agents now communicate and progress better, then requested the next production layer:

- Real stacked inventories for every agent.
- A limit of 15 different item types per agent.
- Replay recording instead of gameplay videos.
- Replay playback where movement can be inspected without LLM delays.
- Sprite files for new NPCs/items/features when final art is not available yet.
- Updated automation instructions for the new QA surface.

Implementation:

- Added `INVENTORY_SLOT_LIMIT = 15`.
- Added inventory slot helpers to `Agent`:
  - `used_inventory_slots`;
  - `free_inventory_slots`;
  - `can_accept_item`;
  - capped `add_items` that respects item `max_stack` and the 15 distinct item limit.
- Updated item insertion so overflow loot is not silently added beyond stack or slot limits.
- Updated world interactions so the returned loot matches what actually fit into inventory.
- Updated craft discovery/craftability to require output inventory space.
- Fixed output-space checks so consumed ingredients can free a slot for the crafted result.
- Added `inventory_rules` to the LLM context so agents can see slot use, slot limit, and stack caps for carried items.
- Updated the LLM developer prompt: if inventory is nearly full, prefer eating, crafting, placing, or using existing stacks over gathering random new item types.
- Replaced default screen-video recording in `main.py` with replay status. The game now writes replay data through the logger rather than capturing frames.
- Extended `RunLogger`:
  - `world.json` contains terrain rows, shade rows, and agent identity/persona metadata.
  - `replay.jsonl` contains one post-round snapshot per round.
- Added replay payloads to `Simulation`:
  - agent positions, previous positions, facing, previous facing, stats, inventory, slot use, thoughts, intents, actions, known recipes;
  - current feature list with hp;
  - recent chat and round events.
- Added `tools/play_replay.py`:
  - opens newest replay by default or a specific `logs/session_*` directory;
  - plays without LLM delays;
  - supports WASD/arrows camera, Tab selected agent, F follow, Space pause, `+`/`-` speed, `[`/`]` stepping.
- Added `tools/generate_missing_sprites.py`:
  - writes transparent PNG placeholders for missing sprite specs;
  - covers terrain, features, items, agents, and UI icons.
- Ran the sprite generator and wrote 37 missing PNG placeholders, including newer wildlife/placeables/tools/UI.
- Updated README:
  - replay workflow;
  - replay controls;
  - missing sprite generator;
  - removed MP4-default wording.
- Updated heartbeat automation `agent-social-qa-continuation`:
  - now explicitly checks `replay.jsonl`, replay playback, inventory stacking, 15-slot limits, overflow behavior, and generated/missing sprites.

Validation:

- Targeted inventory test:
  - A 15-slot inventory refused a new item type.
  - Existing stack insertion capped at the item `max_stack`.
  - A full inventory can still craft if consumed ingredients free a slot for the output.
- Targeted replay test:
  - A simulation wrote `world.json` and non-empty `replay.jsonl`.
  - `tools.play_replay.make_replay_sim` reconstructed a replay sim object from those files.
- Qwen smoke session:

```text
logs/session_20260607_120938
```

  - 6 rounds.
  - 0 LLM fallbacks.
  - `world.json` and `replay.jsonl` were written.
  - Replay frames included agent inventory slot counts.
- Offline smoke session:

```text
logs/session_20260607_121341
```

  - 2 rounds.
  - Replay frame count: 2.
  - Last frame showed stacked inventories and `used_inventory_slots/15`.
- `compileall` and targeted `py_compile` passed for core modules and new tools.

Current read:

This is the first real replay layer: it is data-first rather than video-first, so replays can be inspected at arbitrary speed without waiting for LLM calls. Inventory is now mechanically bounded, not just drawn differently. The next development pass should test a longer replay for usability, then continue toward campfire/workbench placement and richer inventory decisions when bags fill up.

## 2026-06-07 12:24 +03: Replay QA And Axe-To-Logs Priority

Reason:

After adding replay files and inventory limits, the next heartbeat pass tested whether those systems held up in a real Qwen run and whether the early tool bridge actually led into the wood chain.

Observed QA session:

```text
logs/session_20260607_121941
```

Good signs:

- 10 Qwen rounds completed with 0 LLM fallbacks.
- `world.json` and `replay.jsonl` were written.
- Replay had 10 frames matching the turn rounds.
- No replay inventory frame exceeded the 15-slot limit.
- `used_inventory_slots` matched actual distinct inventory item counts in every replay frame.
- Agents performed 17 `interact`, 5 `experiment`, 4 `craft`, and 4 `move` actions.
- Aiden and Mira both discovered and crafted `Stone axe`, proving the early pebble/cordage bridge is working.
- Sprite manifest check found 0 missing sprites.

Problems:

- After crafting a `Stone axe`, agents were not consistently biased toward chopping nearby trees for logs.
- Qwen still internally generated too many invalid place fantasies, though filters blocked them from chat and replacement actions kept turns productive.
- One line used the wrong tool conceptually, mentioning a wooden pickaxe for tree/stone work in a messy way.

Implementation:

- Updated `_best_immediate_interaction` scoring:
  - If an agent has an axe, lacks logs, and has fewer than 4 planks, nearby tree features now get top strategic priority.
  - Forest/wood targets become secondary strategic options.
  - This makes invalid-place replacements and vague-move conversions prefer chopping trees after the axe milestone.
- Strengthened the LLM developer prompt with explicit tool roles:
  - axes chop trees;
  - pickaxes mine stone and ore;
  - shovels dig;
  - fishing rods/nets catch fish.

Validation:

- Targeted scenario:
  - Agent with `Stone axe` near `Birch tree`, grass, and wildlife chose the `Birch tree` as `_best_immediate_interaction`.
- `compileall` passed.
- Targeted `py_compile` passed for `simulation.py`, `llm.py`, `inventory.py`, and `world.py`.

Current read:

The replay and inventory systems look stable enough for continued QA. The next mechanical target remains the base chain after logs: agents should chop enough wood, split logs into planks/sticks, craft `Workbench`, then place it, followed by `Campfire` and cooking.

## 2026-06-07 12:44 +03: Logs-To-Planks Progression And Status Chat Leak

Reason:

A longer Qwen QA run tested whether the post-axe tree priority really advanced into the wood/base chain.

Observed QA session:

```text
logs/session_20260607_123718
```

Good signs:

- 14 Qwen rounds completed with 0 LLM fallbacks.
- Actions included 21 `interact`, 9 `craft`, 4 `experiment`, and 8 `move`.
- Mira crafted `Stone axe`.
- Mira worked a `Birch tree` multiple times and eventually harvested `2 Birch log`, `1 Stick`, and `1 Bark`.
- Replay and turn logs remained readable for progression analysis.

Problems:

- One status line leaked into accepted chat:
  - `I'm currently at the center of this area. Let me explore a bit to see what I can find.`
- After getting logs, Mira still crafted another `Cordage` instead of discovering `Rough planks`.
- Private memory accepted a useless navigation note:
  - `Moved east. No action needed for now.`

Implementation:

- Expanded status speech filters:
  - `center of this area`;
  - `center of the area`;
  - `I'm currently at ... center`.
- Expanded private-memory rejection for:
  - `Moved east/west/north/south/left/right/up/down`;
  - `no action needed`.
- Reprioritized wood-chain recipes:
  - `planks_from_log` now outranks extra `Cordage` when the agent lacks a `Workbench` and has fewer than 4 planks.
  - `sticks_from_log` outranks extra `Cordage` when the agent lacks a `Workbench` and has fewer than 2 sticks.
- Updated `_productive_replacement`:
  - It now compares the best known craft against the best discoverable recipe.
  - If the hidden/discoverable recipe has higher priority, the agent experiments instead of crafting a lower-priority known recipe.

Validation:

- Targeted status check confirmed the leaked `center of this area` line is now blocked.
- Targeted recipe check confirmed:
  - with `Birch log + Cordage + Stick + Grass fiber` and only `Cordage` known, `planks_from_log` is the best discoverable recipe;
  - productive replacement chooses `experiment` for `Rough planks` instead of crafting more `Cordage`.
- `compileall` passed.
- Targeted `py_compile` passed for `simulation.py` and `llm.py`.

Current read:

The survival tech chain now has a clearer next step: once agents chop logs, replacement logic should push them toward discovering and crafting planks before hoarding extra cordage. The next QA target is whether a longer run reaches `Workbench` and then actually places it.

## 2026-06-07 12:54 +03: Post-Axe Tree Targeting Fix

Reason:

A longer Qwen run after the logs-to-planks fix tested whether agents could repeatedly reach the axe/log/plank/workbench chain.

Observed QA session:

```text
logs/session_20260607_124709
```

Good signs:

- 18 Qwen rounds completed with 0 LLM fallbacks.
- No accepted chat lines leaked.
- Replay inventory frames had no 15-slot violations.
- Mira discovered and crafted `Stone axe`.
- Aiden discovered `Wooden pickaxe`.

Problems:

- Mira crafted `Stone axe` but then kept digging `Clay hills` instead of moving toward trees for logs.
- Root cause: `_needs_progress_exploration` still required early basic-material conditions even when the agent already had an axe and needed logs.
- Secondary cause: `_best_visible_progress_target` still allowed nearby rock/stone features to outrank trees even after the axe milestone.

Implementation:

- If an agent has an axe, no logs, and fewer than 4 planks, progress exploration now turns on immediately.
- Progress-target scoring now treats this post-axe/no-log state as a wood milestone:
  - tree features become top priority;
  - rock/stone/ore features are demoted until logs are secured.
- `_productive_replacement` already calls progress exploration before local immediate interactions; this now correctly redirects invalid/vague actions away from clay loops and toward trees.

Validation:

- Targeted snapshot reproduced the bug:
  - agent with `Stone axe`, no logs, and nearby clay/stone/tree previously chose a nearby `Stone outcrop`.
- After the fix:
  - `_needs_progress_exploration` returned `True`;
  - `_best_visible_progress_target` returned `Birch tree`;
  - productive replacement returned a move toward `Birch tree`.
- `compileall` passed.
- Targeted `py_compile` passed for `simulation.py`.

Current read:

The axe milestone now has a stronger mechanical pull toward logs. The next long QA pass should check whether this reliably produces `Birch log`/`Oak log`, then `Rough planks`, then `Workbench` placement.

## 2026-06-07 13:06 +03: Plank Threshold And Scenery Chat Filter

Reason:

A 24-round Qwen run tested the post-axe tree targeting fix and whether agents could advance from logs into planks.

Observed QA session:

```text
logs/session_20260607_125710
```

Good signs:

- 24 Qwen rounds completed with 0 LLM fallbacks.
- Mira crafted `Stone axe`, harvested `Birch log`, discovered `Rough planks`, and made `3 Plank`.
- Noah also reached `Stone axe`, `Knapped stone`, and `Stone shovel`.
- Replay inventory frames had no slot-limit violations.

Problems:

- One accepted chat line was a scenery monologue rather than player dialogue:
  - `I'm standing in the middle of a vast grassland. The air is fresh and the sun shines brightly...`
- Mira reached `3 Plank`, but instead of pushing for one more log/plank toward `Workbench`, replacement logic allowed another low-priority `Cordage` craft.

Implementation:

- Expanded status speech filters for scenery monologues:
  - `I'm standing in the middle`;
  - `vast grassland`;
  - `the air is fresh`;
  - `sun shines`.
- Updated `_productive_replacement`:
  - Known crafts with priority above station/placeable/tool thresholds no longer automatically win.
  - If only a low-priority known craft such as extra `Cordage` is available, progress exploration gets a chance first.
  - This lets agents with `Stone axe`, no logs, and fewer than 4 planks keep targeting trees instead of filling time with spare cordage.

Validation:

- Targeted status check confirmed the scenery line is now blocked.
- Targeted progression snapshot confirmed:
  - with `Stone axe + 3 Plank + Stick + Cordage + Grass fiber`, `Cordage` is known and craftable but priority 6;
  - progress target selects nearby `Birch tree`;
  - productive replacement returns an `interact` with the nearby `Birch tree`, not a `Cordage` craft.
- `compileall` passed.
- Targeted `py_compile` passed for `simulation.py`.

Current read:

The chain now reaches `Rough planks`; the next target is getting agents from `3 Plank` to the fourth plank and then discovering/crafting/placing `Workbench`.

## 2026-06-07 13:28 +03: Urgent Station Progression And Unsupported Planting Guard

Reason:

The next autonomous QA pass inspected the 30-round Qwen workbench-push session:

```text
logs/session_20260607_130757
```

The run had good signs: 30 rounds completed with 0 LLM fallbacks, Mira crafted `Stone axe`, harvested Birch logs, discovered `Rough planks`, and reached `6 Plank + 9 Stick + 1 Cordage`. That inventory is enough to discover and craft `Workbench`.

Problem:

Mira still did not discover/craft/place the `Workbench`. The remaining gap was not the recipe data; it was decision arbitration. The model could choose a valid movement turn, so the existing replacement logic did not always intervene even when a high-value station recipe was immediately discoverable.

Implementation:

- Added `_urgent_progression_decision` to `simulation.py`.
- Movement, interaction, talk, and wait decisions now yield to urgent progression when:
  - a placeable station is already in inventory and the current tile can accept it;
  - a known high-priority craft is available (`Campfire`, `Workbench`, `Kiln`, or plank bridge);
  - a high-priority recipe is discoverable from current materials.
- `_productive_replacement` now also checks urgent progression before lower-value alternatives.
- Added `_best_urgent_placeable` so ready stations are actually placed instead of carried forever.
- Added `_looks_like_unsupported_world_plan` to catch unsupported fantasy actions such as planting Birch/Oak/Pine/Fruit trees through `experiment`, then redirect them into real progression.

Validation:

- Targeted progression snapshot:
  - `6 Plank + 9 Stick + 1 Cordage`, recipe unknown -> adjusted to `experiment` for `Workbench`;
  - same inventory with `workbench` known -> adjusted to `craft workbench`;
  - `Workbench` in inventory on a clear Grass tile -> adjusted to `place workbench`.
- Targeted unsupported-plan snapshot:
  - `experiment` with intent/thought/speech about planting a Birch tree -> replaced with a real `Cordage` discovery experiment.
- Short live Qwen smoke:
  - `logs/session_20260607_132057`;
  - 10 rounds, 3 agents, 0 LLM fallbacks;
  - actions: `move` 11, `interact` 14, `experiment` 5;
  - chat stayed empty because 21 proposed lines were blocked as status/non-dialogue, including unsupported planting chatter.
- `compileall` passed.
- `tools/generate_missing_sprites.py` reported `written=0 skipped=143`.

Current read:

The workbench chain now has explicit mechanical pressure at all three steps: discover, craft, and place. The next longer QA pass should confirm that Mira/Aiden actually leave a placed `Workbench` in replay state once they reach the same material threshold again.

## 2026-06-07 13:44 +03: Workbench Placement Verified And Cordage Bridge Tightened

Reason:

A longer 36-round mixed-biome Qwen run tested the urgent station progression fix:

```text
logs/session_20260607_132609
```

Good signs:

- 36 rounds completed with 0 LLM fallbacks.
- The run produced the first full station chain in live QA:
  - round 33: Aiden discovered `Workbench` and made 1 `Workbench`;
  - round 34: Aiden placed `Workbench`;
  - `replay.jsonl` showed `feature:"workbench"` at `x=35,y=4`.
- Inventory limits stayed within the 15-slot cap in replay state.
- Generated sprite check still reported `written=0 skipped=143`.

Problems:

- Mira reached `6 Plank + 5 Stick + 7 Grass fiber`, which is almost enough for `Workbench`, but kept trying nearby `Stone outcrop` interactions because she had not converted fiber into `Cordage`.
- One private-memory note slipped through as a phantom station plan:
  - `Placing a campfire in a strategic location can provide warmth and light during my exploration...`
  - Noah did not own a `Campfire`, had not placed one, and the note would look like false internal continuity when reviewing thoughts.

Implementation:

- Raised `cordage_from_fiber` to priority 2 when:
  - no `Workbench` item/station is available;
  - the agent already has at least 4 `Plank` and 2 `Stick`;
  - the agent has no `Cordage`.
- This turns `Cordage` into a key bridge craft only when it directly unlocks `Workbench`, without making agents overproduce rope-like materials later.
- Added `_memory_imagines_unowned_placeable` to reject private-memory notes about placing/building/setting up a placeable item when the agent does not own that item and no nearby matching station exists.

Validation:

- Targeted Mira-like snapshot:
  - inventory: `6 Plank + 5 Stick + 7 Grass fiber + Stone axe`;
  - known recipes: `Cordage`, `Pebble axe`, `Rough planks`, `Split sticks`;
  - a movement decision now adjusts to `craft cordage_from_fiber`;
  - `cordage_from_fiber` priority is now `2` in that state.
- Targeted memory snapshot:
  - phantom campfire placement memory with no `Campfire` -> rejected;
  - the same note with `Campfire` in inventory -> accepted.
- `compileall` passed.
- `tools/generate_missing_sprites.py` reported `written=0 skipped=143`.

Current read:

The first station milestone is now proven in replay and the obvious pre-workbench bridge gap is closed. The next QA focus should move one layer up: whether agents actually use the placed `Workbench` to discover/work toward `Fish net`, `Kiln`, better tools, storage, and shelter instead of treating the station as decorative scenery.

## 2026-06-07 14:08 +03: Post-Workbench QA And Anti-Duplicate Station Rules

Reason:

A 46-round mixed-biome Qwen run tested whether placed workbenches become useful progression anchors:

```text
logs/session_20260607_134011
```

Good signs:

- 46 rounds completed with 0 LLM fallbacks.
- Agents produced 25 accepted chat lines; they were actually hearing and answering each other more often.
- Aiden reached the station chain again:
  - discovered `Workbench`;
  - placed `Workbench`;
  - later used the same general progression path around placed workbenches.
- Replay inventory limits stayed valid:
  - max observed used slots: 9;
  - no 15-slot violations.
- Replay contained persistent placed `Workbench` features.

Problems:

- Aiden crafted and placed a second `Workbench` after walking away from the first one. The existing priority check only asked whether a matching station was near the agent, so duplicate station crafting could still look useful once the agent moved.
- Workbench-tier storage/shelter recipes were not being pulled forward strongly enough. `Wooden crate` stayed available as a reasonable idea in chat, but the simulation did not prioritize the first real crate as the next station-era milestone.
- Several accepted chat lines were formulaic observation offers:
  - `I noticed you're near a tree. Do you need help with anything?`
  - `I noticed you're close to a workbench. Would you like me to help you craft something?`
  These are technically dialogue, but they make the agents feel like polite helper scripts instead of people with specific goals.

Implementation:

- Added `_world_has_feature` and `_has_item_or_world_station`.
- Station/placeable craft priority now checks whether a matching feature already exists anywhere in the world, not only adjacent to the agent.
- Duplicate placeable recipes now return priority `999` when every output placeable already exists in the world or inventory.
- `_best_urgent_placeable` now avoids placing a duplicate of an existing world feature.
- Raised first `Wooden crate` priority to `3` when a workbench is nearby.
- Raised first `Tent`/`Bedroll` priority to `4` when a workbench is nearby.
- Added `_is_formulaic_observation_offer` to block bland `I noticed/I see you... do you need help` style lines while still allowing specific questions and trade/resource requests.

Validation:

- Targeted duplicate-station snapshot:
  - existing world `Workbench`;
  - agent with enough materials and known `Workbench`;
  - `workbench` recipe priority is now `999`;
  - `_best_known_craft` returns `None`.
- Targeted crate snapshot:
  - agent near an existing `Workbench` with `5 Plank + 8 Stick`;
  - `wooden_crate` priority is `3`;
  - `_best_discoverable` returns `wooden_crate`.
- Targeted speech snapshot:
  - formulaic `I noticed you're near a tree. Do you need help with anything?` -> blocked as `formulaic observation offer`;
  - concrete `Do you have two spare sticks for a crate?` -> allowed.
- `compileall` passed.
- `tools/generate_missing_sprites.py` reported `written=0 skipped=143`.

Current read:

Workbench duplication is blocked, and the first storage/shelter layer now has enough priority to surface after the station milestone. The next full Qwen pass should check that this produces an actual `Wooden crate` placement and that the stricter chat filter leaves fewer helper-script lines without making agents silent again.

## 2026-06-07 14:34 +03: Settlement Pull Toward Existing Stations

Reason:

A 44-round mixed-biome Qwen run tested the anti-duplicate Workbench and stricter `I noticed...` chat filter:

```text
logs/session_20260607_140044
```

Good signs:

- 44 rounds completed with 0 LLM fallbacks.
- Duplicate Workbench crafting did not recur in this run.
- Aiden discovered and placed `Workbench` by round 17.
- The stricter formulaic observation filter reduced accepted chat from 25 lines in the previous long run to 6 lines.

Problems:

- The first `Wooden crate` still did not appear.
- Root cause: after placing `Workbench`, agents drifted away from it. Once they were no longer adjacent, workbench recipes were not craftable/discoverable, so the priority system could not pull `Wooden crate` forward.
- Several accepted chat lines were still action/status narration:
  - `I'm currently in a good spot...`;
  - `You are already at the chosen location.`;
  - `I'll wait here for now...`;
  - `I'll use the wooden pickaxe to mine a stone and place it as a wooden crate.`
- Mira also entered an idle wait streak near the early base area.

Implementation:

- Added settlement pull toward remote stations:
  - `_needed_remote_station`;
  - `_nearest_needed_station`;
  - `_has_station_locked_progress`;
  - `_move_toward_progress_target`.
- If a placed `Workbench`, `Campfire`, or `Kiln` exists elsewhere and the agent has materials for a recipe locked behind that station, vague progress movement now targets the station first.
- `wait` decisions with vague observe/explore language are now converted through `_productive_replacement`, so idle observation can become useful movement/crafting.
- Expanded status speech filters for:
  - `I'll wait...`;
  - `I'll use...`;
  - `I'll keep...`;
  - `I'm currently in a good spot...`;
  - `You are already at the chosen location.`

Validation:

- Targeted remote-station snapshot:
  - existing world `Workbench` at a distance;
  - agent with `5 Plank + 8 Stick`;
  - idle `wait` now adjusts to `move toward Workbench`.
- Targeted adjacent-station snapshot:
  - same inventory adjacent to `Workbench`;
  - movement now adjusts to `experiment` for `Wooden crate`.
- Targeted speech snapshot:
  - the four bad accepted chat styles above are now blocked as `status update instead of dialogue`;
  - concrete crate request `Do you have two spare sticks for a crate?` remains allowed.
- `compileall` passed.
- Targeted `py_compile` passed for `simulation.py`.
- `tools/generate_missing_sprites.py` reported `written=0 skipped=143`.

Current read:

This is the first small step toward actual settlement behavior: placed stations now act as anchors that agents can return to when their inventory makes station recipes possible. The next Qwen pass should verify whether that finally produces a placed `Wooden crate`, and whether the chat volume remains low-but-human rather than silent.

## 2026-06-07 14:58 +03: Floors, Walls, Houses, And Rest Bonus

Reason:

The user asked for real building mechanics beyond tents:

- placeable floors made from planks or stone;
- placeable walls;
- homes formed by floor spaces enclosed by walls and a door;
- bedroll/rest bonuses when the bed is inside a valid house;
- a new ChatGPT atlas prompt for missing building sprites.

Implementation:

- Added new items:
  - `Wooden floor`;
  - `Stone floor`;
  - `Wooden wall`;
  - `Stone wall`.
- Added new wall features:
  - `wooden_wall`;
  - `stone_wall`.
- Added new recipes:
  - `wooden_floor`: `1 Plank -> 2 Wooden floor`;
  - `stone_floor`: `2 Stone -> 2 Stone floor`;
  - `wooden_wall`: `2 Plank + 1 Stick -> 2 Wooden wall`;
  - `stone_wall`: `3 Stone + 1 Clay lump -> 2 Stone wall`.
- Added all new building pieces to `PLACEABLE_ITEMS`.
- Added a separate `floor` layer to `Tile` so floors can exist underneath features like `Bedroll`, `Workbench`, `Crate`, or `Door`.
- Updated placement:
  - floor items place into `tile.floor`;
  - wall items place as blocking features;
  - doors remain passable features.
- Added house detection:
  - a house is a contiguous floor region;
  - every 4-direction boundary must be closed by `Wooden wall`, `Stone wall`, or `Wooden door`;
  - open edges break the house.
- Added house rest bonus:
  - `Bedroll` inside an enclosed house gives extra energy;
  - larger enclosed floor area gives a higher bonus, capped at 24 bonus energy.
- Updated renderer:
  - floor sprites draw after terrain and before features.
- Updated replay payload:
  - frames now include a `floors` list.
- Updated replay viewer:
  - `tools/play_replay.py` reconstructs the new floor layer correctly.
- Added building sprite prompt:
  - `docs/building_sprite_atlas_prompt.md`.
- Generated placeholders for the six new sprites:
  - `feature_wooden_wall`;
  - `feature_stone_wall`;
  - `item_wooden_floor`;
  - `item_stone_floor`;
  - `item_wooden_wall`;
  - `item_stone_wall`.

Validation:

- Targeted house test:
  - built a 3x3 wooden-floor interior;
  - surrounded it with walls;
  - placed a door on the boundary;
  - placed a `Bedroll` inside;
  - `house_rest_bonus` detected a 9-tile house and returned bonus energy;
  - `Bedroll` interaction produced `rested on bedroll inside a 9-tile house`;
  - wall cells blocked movement;
  - door cell remained passable.
- Targeted replay test:
  - placing `Wooden floor` through `Simulation.apply_round_decisions` produced `placed Wooden floor`;
  - `_replay_payload` included the floor in `floors`.
- `compileall` passed.
- `tools/generate_missing_sprites.py` wrote 6 new placeholders and skipped 143 existing sprites.

Current read:

The mechanical basis for houses now exists. Agents can learn/craft/place floor and wall pieces, and a properly enclosed floor area with a door now matters mechanically. The next AI-behavior challenge is social: agents may still build separate fragments unless we add shared building projects, reserved build sites, and resource contribution memory.

## 2026-06-07 19:35 +03: Building Placement QA And Nearby Walls

Reason:

The first Qwen smoke after adding floors and walls showed a subtle construction blocker:

- Aiden discovered and crafted `Wooden floor`.
- The agent then kept requesting other placeables or returning to crafting instead of turning the ready floor and wall pieces into an actual build site.
- The cause was not the recipe system. The urgent placement heuristic refused to consider placeables whenever the agent's current tile already had a feature, even though floors are a separate layer and can be placed under stations or beds.

Implementation:

- Updated urgent placeable selection so it checks for any valid spot in the agent's current cell or adjacent cells.
- Kept floors as the preferred simple building action when they are already in inventory.
- Added nearby placement fallback for building pieces:
  - if a wall or floor cannot be placed on the current tile;
  - the simulation tries adjacent cells;
  - occupied cells and water are skipped;
  - successful adjacent placement reports `placed ... nearby`.
- Kept non-building placeables conservative:
  - workbenches, campfires, kilns, tents, crates, doors, and bedrolls still require the current tile.

Validation:

- Ran a targeted Python smoke:
  - an agent standing on a workbench tile with `Wooden floor` now still chooses `wooden_floor` as the urgent placeable;
  - `Wooden floor` places on the current tile as a floor layer under the workbench;
  - `Wooden wall` cannot occupy the workbench tile and correctly places on an adjacent valid tile;
  - inventory decrements correctly after both placements.

Current read:

This should make early construction noticeably less brittle. The next useful QA pass is a longer Qwen run that watches whether builders lay floor fragments around a station and eventually start enclosing them with walls rather than stockpiling building pieces forever.

## 2026-06-07 20:12 +03: Imported ChatGPT Building Sprites

Reason:

The user supplied a new building atlas with transparent-looking art for floors, walls, and a door. The previous building pieces were still placeholder PNGs, so houses worked mechanically but looked flat.

Implementation:

- Added `tools/import_building_atlas.py`:
  - reads a ChatGPT-style building atlas;
  - detects 12 large sprite components automatically instead of requiring a perfect grid;
  - falls back to non-black pixel detection when a clipboard/export path loses true alpha;
  - writes game-ready 32x32 PNGs;
  - saves a debug preview with detected boxes when requested.
- Saved the pasted atlas from the Windows clipboard into `assets/generated/building_atlas_clipboard.png`.
- Imported new sprites:
  - `item_wooden_floor`;
  - `item_stone_floor`;
  - `feature_wooden_wall`;
  - `feature_stone_wall`;
  - `feature_wooden_door`;
  - `item_wooden_door`;
  - `item_wooden_wall`;
  - `item_stone_wall`.
- Saved visual QA outputs:
  - `assets/generated/building_atlas_detected.png`;
  - `assets/generated/building_sprites_contact.png`.

Validation:

- The importer detected exactly 12 usable sprite components in the atlas.
- Alpha sanity check confirmed:
  - floor tiles are nearly full-tile sprites;
  - wall and door sprites retain transparent space around the object;
  - no imported sprite remains a fully opaque black square.
- Visual contact sheet confirmed the new floor, wall, and door art is readable at 32x32.

Current read:

The building loop now has both mechanics and real art. The next visual pass should watch a live or replayed settlement build and decide whether the full-height wall sprites read better than the compact wall icons in the world layer.

## 2026-06-07 20:47 +03: Imported Wildlife And Remaining Placeholder Atlas

Reason:

The user supplied a new ChatGPT atlas for the remaining placeholder sprites. The atlas was visually strong, but ChatGPT did not follow the requested 6x6 manifest exactly:

- it left several requested item/UI sprites out;
- it shifted later sprites into a looser layout;
- it used transparency correctly, but individual sprites and shadows crossed the implied grid boundaries.

Implementation:

- Added `tools/import_missing_sprite_atlas.py`:
  - detects visible alpha components globally instead of trusting the 6x6 grid;
  - sorts components top-to-bottom and left-to-right;
  - maps only visually present, useful sprites;
  - skips ambiguous duplicates and unclear tools;
  - writes a contact-sheet preview for QA.
- Imported 26 real sprites:
  - wildlife/features: `feature_salmon_school`, `feature_eel`, `feature_rabbit`, `feature_deer`, `feature_fox`, `feature_boar`, `feature_frog`, `feature_duck`, `feature_gull`, `feature_turtle`;
  - placeables/features: `feature_tent`, `feature_bedroll`, `feature_wooden_crate`;
  - items: `item_copper_ingot`, `item_iron_ingot`, `item_gold_ingot`, `item_plank`, `item_wild_seed`, `item_tent`, `item_stone_knife`, `item_fish_net`, `item_copper_pickaxe`, `item_iron_pickaxe`, `item_diamond_pickaxe`;
  - UI: `ui_selected`, `ui_inventory`.
- Kept generated debug output local:
  - `assets/generated/missing_sprite_atlas_20260607.png`;
  - `assets/generated/missing_sprite_import_contact.png`.

Validation:

- Visual contact sheet showed clean isolated sprites without neighbor slivers after switching from grid slicing to global component detection.
- Placeholder scan dropped from 36 tiny placeholder files to 10.
- Remaining placeholders are:
  - `item_cactus_flesh`;
  - `item_cactus_spine`;
  - `item_crab_meat`;
  - `item_cooked_fish`;
  - `item_cooked_crab`;
  - `item_fried_egg`;
  - `item_resin`;
  - `item_wooden_pickaxe`;
  - `item_fishing_rod`;
  - `ui_chat`.

Current read:

The world should now look much more alive: most animal placeholders are gone, and common early crafting/storage visuals are no longer abstract boxes. One final small atlas focused only on the 10 remaining sprites should finish the placeholder cleanup.

## 2026-06-07 21:35 +03: Advanced Metals, Alchemy, Equipment, And Hostile Wildlife

Reason:

The user asked for a much deeper sandbox progression layer:

- copper, iron, gold, diamond progression;
- missing metal tools and weapons;
- gold and diamond jewelry;
- diamond-coated tools;
- campfire/kiln/alchemy chain with glass bottles and potions;
- hostile predators that can hurt agents;
- equipment slots for armor and rings;
- item durability;
- better crafting output quality when stations are inside larger houses;
- a new prompt for the next sprite atlas.

Implementation:

- Expanded `ItemDef` with:
  - `equip_slot`;
  - `armor`.
- Added hostile features:
  - `Wolf`;
  - `Bear`;
  - `Snake`.
- Added station:
  - `Potion stand`.
- Added materials and alchemy items:
  - `Glass bottle`;
  - `Hide`;
  - `Leather`;
  - `Venom sac`;
  - `Healing potion`;
  - `Stamina potion`;
  - `Antidote`.
- Added tools and weapons:
  - `Copper axe`;
  - `Copper sword`;
  - `Iron axe`;
  - `Iron sword`;
  - `Diamond-edged pickaxe`;
  - `Diamond-edged sword`.
- Added jewelry:
  - `Copper ring`;
  - `Gold ring`;
  - `Gold necklace`;
  - `Diamond ring`;
  - `Diamond amulet`.
- Added armor:
  - leather head/hands/chest/legs/feet set;
  - iron head/hands/chest/legs/feet set.
- Added recipes for:
  - glass from sand in the kiln;
  - glass bottles in the kiln;
  - potion stand;
  - gold ingots;
  - leather;
  - new tools/weapons;
  - jewelry;
  - leather and iron armor;
  - healing/stamina/antidote potions.
- Added `potion_stand` to placeables.
- Updated world behavior:
  - wolves, bears, and snakes can spawn in appropriate biomes;
  - hostile wildlife can move using the existing wildlife movement system;
  - hostile wildlife near agents can deal HP damage.
- Updated agent behavior:
  - agents now have equipment slots: head, hands, chest, legs, feet, neck;
  - agents can wear up to 10 rings;
  - agents auto-equip better armor/jewelry after crafting or when available;
  - armor rating reduces incoming damage;
  - equipped armor loses durability when absorbing damage;
  - potions have direct effects through the existing eat/use-food action.
- Updated crafting quality:
  - crafting at a station inside an enclosed house gives quality bonus based on house size;
  - quality increases tool/armor durability;
  - quality improves crafted food/potion effect through per-agent food quality.
- Updated HUD/replay/context:
  - HUD shows armor and equipped items;
  - LLM context includes armor/equipment/rings;
  - replay frames include armor/equipment/rings.
- Added sprite prompt:
  - `docs/advanced_progression_sprite_prompt.md`.
- Generated 33 new placeholder sprites for the new objects.

Validation:

- `compileall` passed for `agents_survival_reborn` and `tools`.
- `tools/generate_missing_sprites.py` reported `written=0 skipped=182` after placeholders existed.
- Targeted mechanics smoke confirmed:
  - a workbench inside a 3x3 enclosed house gives crafting quality;
  - an `Iron sword` crafted in that house receives boosted durability;
  - `Iron chestplate`, `Iron boots`, and three `Gold rings` auto-equip;
  - armor rating reduces incoming damage;
  - equipped armor durability drops after damage.
- Short fallback simulation smoke:
  - ran 8 rounds on a 50x40 world with 4 agents;
  - replay/logging path did not crash;
  - all agents stayed alive;
  - hostile wildlife spawned in the world.

Current read:

This is the first real vertical progression layer. The next QA pass should watch whether Qwen discovers the kiln/glass/bottle/potion path naturally or whether the recipe-priority heuristics need a nudge toward alchemy after agents stabilize food and tools.

## 2026-06-07 21:58 +03: Imported Advanced Progression Atlas

Reason:

The user supplied a ChatGPT atlas for the new metals/alchemy/equipment pass. The atlas did not follow the prompt exactly, but it produced many usable sprites:

- predators;
- potion stand;
- hide/leather/venom;
- several weapons;
- rings;
- some armor pieces;
- potions;
- cactus spine;
- chat UI icon.

Implementation:

- Added `tools/import_advanced_progression_atlas.py`:
  - detects visible alpha components globally;
  - sorts them by visual row/column;
  - maps only sprites that clearly match game ids;
  - skips ambiguous duplicates or wrong item types;
  - writes contact-sheet and detection previews.
- Imported 25 sprite ids:
  - `feature_wolf`;
  - `feature_bear`;
  - `feature_snake`;
  - `feature_potion_stand`;
  - `item_potion_stand`;
  - `item_hide`;
  - `item_leather`;
  - `item_venom_sac`;
  - `item_copper_axe`;
  - `item_copper_sword`;
  - `item_iron_sword`;
  - `item_stone_knife`;
  - `item_gold_ring`;
  - `item_diamond_ring`;
  - `item_iron_axe`;
  - `item_iron_chestplate`;
  - `item_leather_tunic`;
  - `item_leather_boots`;
  - `item_iron_helmet`;
  - `item_leather_cap`;
  - `item_iron_boots`;
  - `item_healing_potion`;
  - `item_stamina_potion`;
  - `item_cactus_spine`;
  - `ui_chat`.

Validation:

- Visual contact sheet showed clean isolated imports.
- Corrected the first mapping pass:
  - the copper axe is now imported as `item_copper_axe`;
  - an ambiguous alternate iron torso piece is skipped instead of pretending to be gauntlets.
- Placeholder-size scan now reports 19 remaining tiny placeholders:
  - `item_glass_bottle`;
  - `item_cactus_flesh`;
  - `item_crab_meat`;
  - `item_cooked_fish`;
  - `item_cooked_crab`;
  - `item_fried_egg`;
  - `item_resin`;
  - `item_diamond_edged_pickaxe`;
  - `item_diamond_edged_sword`;
  - `item_copper_ring`;
  - `item_gold_necklace`;
  - `item_diamond_amulet`;
  - `item_leather_gloves`;
  - `item_leather_pants`;
  - `item_iron_gauntlets`;
  - `item_iron_greaves`;
  - `item_antidote`;
  - `item_wooden_pickaxe`;
  - `item_fishing_rod`.

Current read:

Most of the new progression layer now has real art. One final small atlas focused only on these 19 leftovers should finish the current placeholder cleanup without asking ChatGPT to juggle the whole progression tree again.

## 2026-06-07 22:12 +03: Imported Final Leftover Atlas

Reason:

The user supplied another ChatGPT atlas for the remaining placeholders. It again ignored the requested strict grid, but it contained enough clear objects to remove most of the remaining abstract placeholder sprites.

Implementation:

- Added `tools/import_final_leftovers_atlas.py`:
  - detects large alpha components globally;
  - sorts by visual row/column;
  - maps only visually clear leftovers;
  - skips duplicate bottle/potion/rod variants;
  - writes contact and detection previews.
- Imported 15 sprite ids:
  - `item_glass_bottle`;
  - `item_cactus_flesh`;
  - `item_crab_meat`;
  - `item_cooked_fish`;
  - `item_fried_egg`;
  - `item_diamond_edged_sword`;
  - `item_gold_necklace`;
  - `item_diamond_amulet`;
  - `item_resin`;
  - `item_leather_gloves`;
  - `item_leather_cap`;
  - `item_iron_boots`;
  - `item_antidote`;
  - `item_wooden_pickaxe`;
  - `item_fishing_rod`.

Validation:

- Visual contact sheet looked clean at 32x32.
- Placeholder-size scan now reports 6 remaining tiny placeholders:
  - `item_cooked_crab`;
  - `item_diamond_edged_pickaxe`;
  - `item_copper_ring`;
  - `item_leather_pants`;
  - `item_iron_gauntlets`;
  - `item_iron_greaves`.

Current read:

The project is now close to full sprite coverage. The remaining six are specific enough that the next prompt should ask only for those six objects, preferably with two rows of three sprites and lots of padding.

## 2026-06-07 22:30 +03: Hover Tooltips For Items, World Objects, And Replays

Reason:

The user asked to inspect item/world-object characteristics while playing or watching replays:

- inventory items should show name, description, stats, durability, stack, equipment slot, food/effect, and tags;
- mobs and placed world objects should show what they are;
- replay playback should support the same hover behavior.

Implementation:

- Updated the shared renderer so tooltips work in both live gameplay and replay playback.
- Added world hover inspection:
  - agents;
  - terrain tiles;
  - floor/building pieces;
  - features and mobs;
  - placed stations/objects.
- Added inventory hover inspection:
  - item name;
  - generated description;
  - tags;
  - stack size;
  - food/effect value and quality bonus;
  - durability;
  - tool tags and power;
  - armor rating;
  - equipment slot;
  - placeable/station/building hints.
- Added feature/terrain descriptions based on tags:
  - hostile wildlife notes;
  - station notes;
  - ore/tool requirements;
  - loot summaries;
  - building/house relevance.
- Updated replay agent reconstruction:
  - equipment;
  - rings;
  - armor rating;
  - empty durability/food-quality maps for tooltip compatibility.

Validation:

- `compileall` passed for `agents_survival_reborn` and `tools`.
- Headless live-render smoke:
  - drew the main game renderer with world hover;
  - drew the main game renderer with inventory hover;
  - tooltip code did not crash.
- Headless replay-render smoke:
  - loaded newest replay session;
  - reconstructed replay sim;
  - drew replay renderer with world hover;
  - tooltip code did not crash.
- Placeholder scan still reports 6 remaining tiny placeholders.

Current read:

The viewer experience is now much more inspectable. The next UI improvement would be a click-to-pin inspection panel, but hover tooltips already cover quick reading during live gameplay and replay review.

## 2026-06-08 00:35 +03: Cleaner Human Chat And Safer Building Tiles

Reason:

The user ran 8 agents for roughly 200 turns and reported three visible problems:

- a pine tree appeared through placed floor tiles;
- a bear killed Leo too abruptly;
- chat still felt unlike real players, with agents saying action narration, assistant-style prompts, and scenic map descriptions.

Implementation:

- Added `World.can_place_station()` and made placement use it consistently.
- Changed floor placement so floors no longer go under natural features such as trees, plants, animals, rocks, and ore.
- Kept floors compatible with already placed human-made camp objects such as workbenches, campfires, crates, tents, bedrolls, and other stations.
- Prevented moving wildlife from stepping onto floor tiles, so animals should not casually wander into player-built interiors.
- Tuned hostile encounter pressure:
  - reduced wolf, bear, snake, and boar damage;
  - reduced base hostile attack chance;
  - lowered attack chance further when the agent has a weapon or armor.
- Expanded chat filtering for unnatural lines:
  - blocked assistant/operator prompts such as "where would you like me to go";
  - blocked narrator/map-guide lines such as "you are currently in a vast landscape";
  - blocked action-status lines such as "I think I can get wood from that nearby tree";
  - blocked self-preservation announcements such as "I need to be more careful" while still allowing direct warnings.
- Added predator words to direct social markers so useful warnings like "wolf by the workbench, back up" can pass.
- Strengthened local-model prompts:
  - speech must be a real line to another nearby player;
  - self-talk, action narration, scenic descriptions, and operator-facing assistant lines must stay out of chat;
  - added examples of good short warnings, recipe questions, trades, and cooperation lines.

Validation:

- `compileall` passed for `agents_survival_reborn` and `tools`.
- Targeted placement test passed:
  - floor cannot be placed under a pine tree;
  - floor can be placed under an existing workbench;
  - moving wildlife avoids floor tiles.
- Targeted chat filter test passed:
  - all bad screenshot-style lines were blocked;
  - direct danger warning and recipe question were allowed.
- Offline social QA passed for 12 rounds / 4 agents:
  - no crashes;
  - crafting, experiments, interactions, movement, logs, and replay output continued working.
- Local Ollama QA passed for 3 rounds / 4 agents:
  - all requests succeeded through `qwen2.5:7b`;
  - Qwen still attempted several status-update lines, but the new filters blocked them from visible chat.

Current read:

The visible chat should now be quieter but less fake. The next useful step is not just more filtering, but stronger positive social scaffolding: agents need concrete shared projects and remembered obligations so they have something human to talk about besides immediate survival chores.

## 2026-06-08 00:55 +03: Gemini Provider And Mixed-Model Agents

Reason:

The user wanted to add Gemini-backed agents alongside the existing local Qwen/Ollama agents, while keeping the current game systems intact.

Implementation:

- Added Gemini as a first-class LLM provider:
  - provider aliases: `gemini` and `google`;
  - default model: `gemini-2.5-flash`;
  - default endpoint: Gemini `generateContent`;
  - API key from `GEMINI_API_KEY` or `AGENTS_SURVIVAL_GEMINI_API_KEY`.
- Implemented Gemini REST calls with the existing standard-library HTTP stack:
  - no new Python package dependency;
  - uses `systemInstruction`, `contents`, `generationConfig`, and `responseMimeType: application/json`;
  - parses returned Gemini candidate text through the existing JSON repair/decision parser.
- Added mixed-provider routing:
  - `--provider gemini` can route every agent through Gemini;
  - `--gemini-agents N` routes the first N agents through Gemini while remaining agents use the primary provider, such as `--llama --model qwen2.5:7b`.
- Added CLI flags:
  - `--gemini-agents`;
  - `--gemini-model`.
- Updated headless QA tooling with the same mixed Gemini options.
- Updated HUD provider display:
  - pure Gemini mode shows Gemini;
  - mixed mode shows the primary provider plus Gemini and the Gemini agent count.
- Kept secrets out of source/docs:
  - docs show placeholder key examples only;
  - no provided key was written to tracked files.
- Updated README with Gemini and mixed Qwen/Gemini launch examples.

Validation:

- `compileall` passed for `agents_survival_reborn` and `tools`.
- Config/routing test passed:
  - provider names are normalized case-insensitively;
  - pure Gemini config resolves Gemini defaults;
  - mixed Qwen/Gemini routes the first N agents to Gemini and the rest to Ollama.
- Gemini response extraction test passed with a mocked Gemini response.
- CLI help prints the new Gemini flags successfully.
- Offline social QA passed for 5 rounds / 4 agents.
- Renderer compatibility smoke passed with a replay-style minimal LLM config, so older replay playback does not break on missing Gemini config fields.
- Secret scan confirmed the provided key prefix is not present in the repository.

Current read:

Gemini is now wired in as a hosted model option without replacing local Qwen. The remaining live check is to set `GEMINI_API_KEY` in the user's shell and run a short mixed QA/game session against the real API.

## 2026-06-08 01:02 +03: Cleaner Intent And Thought Logs

Reason:

The latest autonomous QA log showed two spectator-log quality issues:

- one LLM intent arrived as mojibake/question-mark garbage;
- one thought was pure movement narration: "I am walking to the left."

Implementation:

- Strengthened `clean_inner_text()` for thoughts, intents, and memory notes:
  - drops non-ASCII text, which catches malformed local-model encoding output;
  - drops question-mark garbage strings caused by encoding fallback;
  - drops simple mechanical movement narration such as "I am walking to the left."
- Sanitized LLM `intent` before assigning it to the agent HUD/log state.
- If an LLM intent is invalid after cleaning, the agent falls back to the chosen action name instead of preserving bad text.

Validation:

- Targeted cleaner test passed for:
  - question-mark garbage;
  - "I am walking to the left.";
  - "Walking to the east.";
  - a normal cave-related thought.
- `compileall` passed for `agents_survival_reborn` and `tools`.

Current read:

This does not make agents smarter by itself, but it keeps the observer-facing mind log from being poisoned by malformed local-model output. That matters now that thoughts are part of the actual viewing experience.

## 2026-06-08 01:10 +03: Starting Kit For Long Mixed-Model QA

Reason:

The user wanted a 200-turn comparison run with 2 Qwen agents and 2 Gemini agents, with every agent receiving a starting resource kit:

- 10 wood;
- 10 stone;
- 10 sticks;
- 10 copper.

Implementation:

- Added reusable `parse_start_items()` for comma-separated `item_id=count` kits.
- Added `Simulation.grant_starting_items()` to grant the same kit to every spawned agent.
- Added `--start-items` to the PyGame launcher.
- Added `--start-items` to `tools/run_social_qa.py`.
- Fixed `tools/run_social_qa.py` Gemini key handling:
  - mixed Gemini agents use `GEMINI_API_KEY` or `AGENTS_SURVIVAL_GEMINI_API_KEY`;
  - pure `--provider gemini` also receives the Gemini API key.
- Documented the 200-round mixed Qwen/Gemini QA command in README.

Validation:

- Targeted start-kit test passed:
  - parsed `pine_log=10,stone=10,stick=10,copper_ore=10`;
  - granted the kit to all agents;
  - stayed within the 15 distinct item slot limit.
- `compileall` passed for `agents_survival_reborn` and `tools`.
- Offline headless QA with the starting kit passed for 2 rounds / 4 agents:
  - agents immediately discovered and crafted planks from the supplied logs.
- `python run.py --help` shows the new `--start-items` option.

Current read:

The requested 200-turn test can now be launched repeatably from the command line. I used `pine_log` for "wood" and `copper_ore` for "copper" so agents still need to discover crafting/smelting progression instead of receiving finished copper ingots.

## 2026-06-08 01:20 +03: Gemini Rate Limit Retries

Reason:

The user hit `HTTP Error 429: Too Many Requests` while running mixed Qwen/Gemini QA. This means the Gemini endpoint rejected one or more requests due to rate/quota pressure. The simulation already falls back for failed LLM decisions, but repeated 429s make the Gemini agents behave like fallback agents, which ruins the comparison test.

Implementation:

- Added hosted-API retry support to `LLMConfig`:
  - `retry_count`;
  - environment variable `AGENTS_SURVIVAL_LLM_RETRIES`;
  - CLI flag `--llm-retries` for both PyGame and headless QA.
- Gemini `generateContent` calls now retry transient HTTP failures:
  - 429;
  - 500;
  - 502;
  - 503;
  - 504.
- Retry delay respects `Retry-After` when the provider sends it.
- Without `Retry-After`, retries use short exponential backoff.
- Updated README's 200-round mixed Qwen/Gemini command to use safer `--workers 1` and `--llm-retries 2`.

Validation:

- Mocked 429 retry test passed:
  - first request raised 429 with `Retry-After: 0.5`;
  - retry waited and succeeded on the second request.
- `compileall` passed for `agents_survival_reborn` and `tools`.
- `python tools/run_social_qa.py --help` shows `--llm-retries`.
- `python run.py --help` shows `--llm-retries`.

Current read:

This improves burst-rate handling, but it cannot bypass a real exhausted Gemini daily quota. If 429 persists across retries with `--workers 1`, the test should either reduce `--gemini-agents`, wait for quota reset, or switch Gemini agents to a cheaper/faster model if available.

## 2026-06-08 01:28 +03: Live 200-Round Watch Mode

Reason:

The user clarified that the mixed Qwen/Gemini run should be watched in the PyGame window, not only run as a headless QA script.

Implementation:

- Added `--max-rounds` to the live PyGame launcher.
- When the live simulation reaches the requested round count, it pauses instead of closing the window.
- Documented a live 2 Qwen + 2 Gemini command with the same starting kit:
  - 10 pine logs;
  - 10 stone;
  - 10 sticks;
  - 10 copper ore.

Validation:

- `python run.py --help` shows `--max-rounds`.
- `compileall` passed for `agents_survival_reborn` and `tools`.

Current read:

The user can now watch the agents live and still get a clean stopping point at 200 rounds for inspection.

## 2026-06-08 01:45 +03: Mixed Gemini Fallback To Primary Provider

Reason:

The live mixed Qwen/Gemini run still hit `HTTP Error 429: Too Many Requests` on round 0. Retries help with burst limits, but if Gemini refuses the request immediately, the live window can sit in `THINKING` and the affected agents become ordinary fallback agents.

Implementation:

- Added `gemini_fallback_to_primary` to `LLMConfig`, enabled by default.
- In mixed mode, if a Gemini-routed agent fails and the primary provider is not Gemini, that agent retries the same decision through the primary provider.
- Added `last_provider_fallbacks`:
  - HUD shows `provider swap N`;
  - headless QA prints `provider_swap=N`.
- Replay compatibility updated so replay HUD has the new counter.

Validation:

- Mocked provider-fallback test passed:
  - Gemini route raised mocked 429;
  - primary provider returned a decision;
  - `last_successes` stayed complete;
  - `last_provider_fallbacks` incremented;
  - no game-level fallback was needed.
- `compileall` passed for `agents_survival_reborn` and `tools`.
- Offline smoke QA still runs and prints `provider_swap`.

Current read:

This cannot force Gemini to participate when Google refuses the request, but it prevents the live watch run from becoming a frozen or dumb fallback run. The HUD now makes it obvious when Gemini was swapped out for Qwen.

## 2026-06-08 02:18 +03: Expanded Survival Materials And 256x256 World

Reason:

The user supplied a large new item list covering stone-age resources, plant fibers, animal materials, building parts, production stations, weapons, fishing gear, farming supplies, cooking, medicine, lighting, and late-game non-magical technology. They also asked for a 256x256 regenerated world, a way to obtain or craft every new item, and placeholder art for anything not covered by the latest atlas.

Implementation:

- Expanded the default world size to 256x256.
- Added `expanded_content.py` as a data pack for new terrains, features, materials, tools, foods, stations, machines, placeables, and recipes.
- Added new generated biomes:
  - limestone karst;
  - basalt field;
  - salt flat;
  - flax meadow;
  - willow wetland;
  - chalk downs;
  - bee grove.
- Added harvestable features for the new resource families:
  - flint, obsidian, limestone, granite, slate, basalt, sulfur, saltpeter, kaolin, gypsum, sandstone, rock salt, amber, river pearls;
  - flax, hemp, cotton, willow withes, dry straw, medicinal flowers, mint, nettles, beehives.
- Expanded terrain interaction loot so agents can gather seeds, manure, fibers, salt, wetland plants, forest byproducts, special stones, and volcanic/chalk resources without relying only on caves.
- Expanded cave loot to include new minerals and rare gem-like finds.
- Added new crafting chains for:
  - advanced stone tools;
  - copper and iron construction parts;
  - production stations;
  - leather/fiber processing;
  - ranged weapons and ammunition;
  - fishing traps and hooks;
  - farming inputs;
  - preserved food and simple meals;
  - medicine and ointments;
  - lighting;
  - navigation and late-game machines.
- Added material bridge recipes so rawhide, thick hide, sinew, limestone, granite, slate, sandstone, chalk, and gypsum feed back into useful crafting chains.
- Made new placeable stations/buildings behave like checked world objects instead of being accidentally harvested.
- Allowed `wattle_wall` to count as a valid enclosing house wall.
- Relaxed the LLM `place_item` schema from a hardcoded old enum to a string, so models can place newly introduced objects that the simulation validates locally.
- Added friendly `--start-items` aliases:
  - `wood`, `sticks`, `stones`, `copper`;
  - Russian aliases such as `дерево`, `камни`, `палки`, `медь`.
- Added `tools/import_expanded_survival_atlas.py` to slice the user's new 36-item survival atlas in visual order. It tolerates partial ChatGPT atlases and leaves missing sprites as placeholders.
- Regenerated missing placeholder sprites for the expanded manifest.
- Updated README with the new start-item aliases and expanded atlas importer command.

Validation:

- `python -m compileall agents_survival_reborn tools` passed.
- Data integrity check passed:
  - 272 items;
  - 197 recipes;
  - 89 features;
  - 23 terrains;
  - 31 placeable item types;
  - no missing recipe ingredients, outputs, or station references.
- Generated a 256x256 world with seed 123 and confirmed all new major biomes except none are absent:
  - limestone karst: 254 tiles;
  - basalt field: 325 tiles;
  - salt flat: 342 tiles;
  - flax meadow: 9327 tiles;
  - willow wetland: 427 tiles;
  - chalk downs: 1257 tiles;
  - bee grove: 983 tiles.
- Confirmed representative new feature generation:
  - flint nodules;
  - limestone outcrops;
  - basalt outcrops;
  - saltpeter deposits;
  - rock salt crusts;
  - flax/hemp/cotton patches;
  - willow stands;
  - beehives;
  - pearl mussels.
- Direct no-window simulation smoke test passed:
  - 256x256 world;
  - 4 offline agents;
  - friendly start kit `wood=10,stone=10,sticks=10,copper=10`;
  - 12 rounds advanced;
  - agents crafted/placed progression items without crashing.

Current read:

The game now has a much broader survival progression spine. The next QA focus should be whether LLM agents discover these chains naturally, whether the 256x256 map feels too large for social clustering, and whether new stations should be weighted more aggressively in agent goals so society-building does not dissolve into solo foraging.

## 2026-06-12 03:02 +03: Anti-Craft-Stall And Building Escape QA

Reason:

The user reported that when agents started with 99-resource test kits, they stood almost still and mostly crafted, occasionally placing floor tiles. This was a real behavior bug: abundant resources made almost every recipe available, and the fallback/progression guard treated repeated crafting as productive even when the agents were no longer using the crafted objects.

Findings:

- Initial 99-resource smoke test reproduced the issue:
  - 40 rounds;
  - 8 agents;
  - 208 craft actions;
  - only 4 place actions;
  - every agent had only 1 unique position.
- `recent_actions` entries are stored with round prefixes such as `r7: crafted ...`, so the first craft-streak detector did not see repeated crafting.
- Non-building placeables, such as a workbench, could only be placed under the agent's feet. If a campfire was already there, agents kept crafting instead of placing the workbench nearby.
- Building-piece priority counted floors and walls together. Once agents placed enough floors, wall recipes became low priority, so they kept making/placing floors instead of enclosing rooms.
- Agents could box themselves in with walls, which produced `could not find a move` waits and passive wall/workbench checks.

Implementation:

- Added craft-loop interruption:
  - after repeated craft/experiment actions, agents must place a useful item, work a real nearby resource, move, or open an escape.
- Fixed craft-streak detection for round-prefixed action log entries.
- Changed nearby placement so all placeable objects can be placed in adjacent cells, not only building pieces.
- Added safer wall placement:
  - agents avoid placing walls that remove their last adjacent exit.
- Added wall dismantling:
  - interacting with wooden/stone/wattle walls dismantles them and returns the wall item;
  - fallback movement dismantles an adjacent wall if the agent has no valid movement exit.
- Separated building priorities:
  - floors no longer satisfy the need for walls;
  - walls become important once enough floor exists;
  - doors become useful once wall count is high enough.
- Added stockpile caps for repetitive components and ammunition:
  - copper/iron nails;
  - rivets/brackets;
  - copper/iron wire;
  - arrows and sling stones.
- Stopped full-resource agents from treating ordinary grass/soil interactions as progress.
- Prevented passive station/storage/building checks from being selected as best immediate productive interactions.

Validation:

- `python -m compileall agents_survival_reborn tools` passed.
- Re-ran the exact high-resource stress style:
  - 8 agents;
  - 120 rounds;
  - `wood=99,stone=99,sticks=99,copper=99`;
  - 96x96 smoke map for speed.
- Final action distribution:
  - move: 324;
  - interact: 299;
  - place: 157;
  - craft: 107;
  - experiment: 73;
  - danger: 15.
- Final construction result:
  - 68 floor tiles;
  - 72 wooden walls;
  - workbench, campfire, and crate placed.
- Every agent moved meaningfully:
  - unique positions ranged from 15 to 38 over 120 rounds.
- Final event tail had no passive `checked wall/workbench` spam and no `could not find a move` entries.

Current read:

The 99-resource test kit now produces a builder/explorer rhythm instead of a frozen crafting printer. It is still worth watching a real LLM run because model decisions can add new weirdness, but the deterministic safety rails now push agents away from inventory loops and toward visible world changes.

## 2026-06-12 02:34 +03: Stronger Local Ollama Model And Longer Context

Reason:

The user suspected the current local model was too weak and asked to check disk space, install a stronger Ollama model, connect it to the game, and make agent context longer like a serious generative setup.

Hardware and storage check:

- GPU: NVIDIA GeForce RTX 3060 Ti with 8GB VRAM.
- RAM: 16GB.
- Free space before the model move/download:
  - C: about 2.8GB free;
  - F: about 24GB free.
- Existing Ollama model store was under `C:\Users\vadim\.ollama\models`, which was too tight for larger models.

Machine setup:

- Stopped the running Ollama process.
- Moved the Ollama model store to `F:\ollama_models`.
- Created a Windows junction from `C:\Users\vadim\.ollama\models` to `F:\ollama_models`.
- Restarted `ollama serve` in the background.
- Verified `ollama list` still sees the old `qwen2.5:7b`.
- Pulled `qwen2.5:14b` successfully.
- Final installed local models:
  - `qwen2.5:14b`, about 9.0GB;
  - `qwen2.5:7b`, about 4.7GB.

Implementation:

- Changed the default native local/Ollama model from `llama3.1` to `qwen2.5:14b`.
- Added explicit Ollama context-window support:
  - `LLMConfig.num_ctx`;
  - environment variable `AGENTS_SURVIVAL_NUM_CTX`;
  - live-game CLI flag `--llm-num-ctx`;
  - headless QA flag `--num-ctx`.
- Passed `num_ctx` into Ollama `/api/chat` options when it is greater than zero.
- Updated `tools/run_social_qa.py` to default to `qwen2.5:14b` with an 8192-token context window.
- Increased retained simulation/social memory:
  - chat history limit from 180 to 300;
  - heard-memory limit from 16 to 48;
  - private-memory limit from 16 to 64.
- Fed more conversation context into each model decision:
  - recent heard chat from 10 to 24 messages;
  - new heard chat from 6 to 12 messages.
- Preserved Gemini fallback settings when rebuilding mixed-provider config.
- Updated README commands for the stronger 14B local profile and documented the speed tradeoff.

Validation:

- `python -m compileall agents_survival_reborn tools` passed after cleaning a stale Windows `.pyc` permission issue.
- `python run.py --help` exposes `--llm-num-ctx`.
- `python tools\run_social_qa.py --help` exposes `--num-ctx`.
- Ran a real one-round Ollama QA call:
  - command used `qwen2.5:14b`;
  - context window 8192;
  - one local agent;
  - 240-second timeout;
  - start kit `wood=10,stone=10,sticks=10,copper=10`.
- The model returned a valid structured decision without fallback:
  - `ok=1/1`;
  - `fallback=0`;
  - action was a real interaction;
  - private memory updated naturally.
- `ollama ps` confirmed:
  - `qwen2.5:14b` loaded;
  - context `8192`;
  - processing split roughly across CPU/GPU.

Current read:

This is a meaningful quality upgrade, but not free. On this 8GB VRAM / 16GB RAM machine, the 14B model with 8192 context took about 160 seconds for one agent's decision in the smoke test. For watching the game live, the sane high-quality profile is 1-2 local Qwen agents with `--llm-workers 1`, high timeout, and long `--round-frames`. For more agents, use Gemini for some agents, lower local context to 4096/6144, or fall back to `qwen2.5:7b` for speed. A 32B-class model is likely too painful here unless disk/RAM/VRAM constraints change.

## 2026-06-12 03:25 +03: Spectator Recipe Book

Reason:

The user stopped the C-drive cleanup and asked for a proper in-app recipe book with sprites and a polished, acceptable interface.

Implementation:

- Added `RecipeBookState` to the renderer.
- Added a full-screen spectator recipe book overlay opened with `B`.
- Added `Esc` behavior that closes the recipe book first and only quits when it is already closed.
- Added mouse wheel scrolling, keyboard scrolling, category cycling, clickable categories, and clickable recipe rows.
- Added the recipe book to both live gameplay and replay playback.
- The recipe book shows:
  - all recipes available to the spectator;
  - category counts;
  - output sprites and counts;
  - ingredient sprites or representative sprites for tag ingredients;
  - required station;
  - recipe hint text;
  - whether the selected agent knows the recipe;
  - whether the selected agent currently has enough ingredients;
  - whether the required station is nearby or carried.
- Added HUD and README hints for `B`.
- Kept agent knowledge rules intact:
  - the recipe book is spectator-only;
  - agents still have to discover hidden recipes through gameplay and cannot craft unknown recipe IDs.

Validation:

- `python -m compileall agents_survival_reborn tools` passed.
- Render smoke test with dummy SDL opened the recipe book overlay and selected a recipe successfully.

Current read:

This should make the sandbox much easier to inspect. The viewer can now pause, select an agent, open the book, and see exactly which crafting path exists, which parts the selected agent has, and where the blocker is. The next useful polish pass would be adding a text search box if the recipe count becomes too awkward for category browsing.
