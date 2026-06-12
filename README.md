# Agents Survival Reborn

New clean-room version of the survival sandbox.

The important difference: chat and decisions are not built from canned phrases.
With `--llm`, every player-character gets its own persona, local perception,
private memory, inventory, nearby chat, known recipes, and asks the model for a
structured decision each round.

## Run

```powershell
cd F:\python_projects\agents_survival_reborn
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py --offline
```

Offline mode is only a smoke-test fallback. For actual generative agents:

Local model through Ollama:

```powershell
ollama pull qwen2.5:14b
ollama serve
python run.py --llama --model qwen2.5:14b --llm-num-ctx 8192 --agents 2 --llm-workers 1 --llm-timeout 240 --llm-max-output-tokens 900 --round-frames 120
```

If Ollama is already running, `ollama serve` can print a port-in-use error.
That is fine; use the exact model name from `ollama list`.
`qwen2.5:14b` gives better decisions than the old 7B default, but it is much
slower on an 8GB GPU. Use 1-2 local agents first, or lower `--llm-num-ctx` to
4096/6144 when you want faster visible turns.

Local model through LM Studio or another OpenAI-compatible server:

```powershell
python run.py --llm --provider compatible --base-url http://localhost:1234/v1 --model local-model-name
```

OpenAI API:

```powershell
$env:OPENAI_API_KEY="sk-..."
python run.py --llm --model gpt-5
```

Gemini API:

```powershell
$env:GEMINI_API_KEY="your-gemini-key"
python run.py --llm --provider gemini --model gemini-2.5-flash
```

Mixed local Qwen/Ollama plus Gemini:

```powershell
$env:GEMINI_API_KEY="your-gemini-key"
python run.py --llama --model qwen2.5:14b --llm-num-ctx 8192 --agents 4 --gemini-agents 2 --round-frames 120 --llm-workers 2 --llm-timeout 240 --llm-max-output-tokens 900
```

In mixed mode, the first `--gemini-agents` agents are routed through Gemini and
the rest use the primary provider (`--llama`, `--provider compatible`,
`--provider openai`, etc.). You can also use `AGENTS_SURVIVAL_GEMINI_API_KEY`,
`AGENTS_SURVIVAL_GEMINI_MODEL`, and `AGENTS_SURVIVAL_GEMINI_AGENTS`.

Live 2 Qwen + 2 Gemini comparison with a starting kit:

```powershell
$env:GEMINI_API_KEY="your-gemini-key"
python run.py --llama --model qwen2.5:14b --llm-num-ctx 8192 --agents 4 --gemini-agents 2 --llm-workers 1 --llm-timeout 240 --llm-retries 2 --llm-max-output-tokens 900 --round-frames 120 --max-rounds 200 --start-items pine_log=10,stone=10,stick=10,copper_ore=10
```

`--max-rounds 200` pauses the live simulation after 200 completed rounds so you
can inspect the world, agents, inventories, chat, and hover tooltips.
`--start-items` also accepts friendly aliases such as
`wood=10,stone=10,sticks=10,copper=10`.

Optional:

```powershell
python run.py --llm --model gpt-5 --round-frames 30 --agents 10
python run.py --asset-wizard
```

For local models, start small:

```powershell
python run.py --llama --model qwen2.5:14b --llm-num-ctx 8192 --agents 2 --round-frames 120 --llm-workers 1 --llm-timeout 240 --llm-max-output-tokens 900 --no-record
```

Every visible round asks every agent for a decision. Local models can be much
slower than a hosted API, especially with 8-10 agents. While the model is
thinking, the game keeps rendering and the HUD shows `THINKING`.
If the HUD shows `timed out`, the affected agents use fallback decisions for
that round. Increase `--llm-timeout`, reduce `--agents`, or use a smaller/faster
local model.
If the HUD reports malformed JSON, the parser will try to repair or field-scan
the model response; unrecoverable raw output is written to
`docs/last_llm_response.txt`.

Headless social QA:

```powershell
python tools\run_social_qa.py --rounds 5 --agents 1 --cluster --model qwen2.5:14b --num-ctx 8192 --workers 1 --timeout 240
```

Mixed Qwen/Gemini social QA:

```powershell
$env:GEMINI_API_KEY="your-gemini-key"
python tools\run_social_qa.py --rounds 4 --agents 4 --cluster --model qwen2.5:14b --num-ctx 8192 --gemini-agents 2 --workers 2 --timeout 240
```

Mixed Qwen/Gemini long tech-progression QA with a starting kit:

```powershell
$env:GEMINI_API_KEY="your-gemini-key"
python tools\run_social_qa.py --rounds 200 --agents 4 --mixed-biome --model qwen2.5:14b --num-ctx 8192 --gemini-agents 2 --workers 1 --timeout 240 --llm-retries 2 --max-output-tokens 900 --start-items pine_log=10,stone=10,stick=10,copper_ore=10 --summary-json logs\mixed_qwen_gemini_200_summary.json
```

`--start-items` grants the listed `item_id=count` kit to every agent after
spawn. The example gives each agent 10 pine logs, 10 stone, 10 sticks, and 10
copper ore.

This runs without the PyGame window, clusters agents for chat testing, and
prints a summary of actions, accepted chat, blocked speech, and recent thoughts.
Use `--mixed-biome` instead of `--cluster` when testing crafting and tech
progression; it starts the group near a more varied area with resources such as
trees, stone, sand/coast, animals, and clay/ore when the generated map permits it.

## Controls

- WASD / arrows: move spectator camera.
- Tab: select next agent and follow.
- F: toggle camera follow.
- Space: pause.
- B: open or close the spectator recipe book.
- R: show current replay file name again.
- Escape: close the recipe book, then quit.

The recipe book is a spectator reference. It shows every recipe with sprites,
ingredients, outputs, required station, category, and whether the selected
agent knows the recipe or currently has enough materials. Agents still discover
hidden recipes through gameplay; the book does not grant them knowledge.

## LLM Design

- All agents decide once per visible round. Model calls run in a background
  worker so the PyGame window stays responsive. OpenAI can use several workers;
  local Ollama defaults to one worker because that is usually smoother.
- The game sends each model only that agent's local observation, memory,
  inventory, known craftable recipes, nearby visible players, and heard chat.
- The model returns JSON: action, target, optional speech, private memory,
  short intent, and a short in-character thought for the spectator log.
- Speech is generated by the model. The local code does not provide phrase
  templates.
- Speech can accompany useful actions. Agents should use chat for replies,
  trades, warnings, blocked-crafting questions, or rare casual remarks, not for
  narrating every step.
- Each run writes JSONL logs to `logs/session_YYYYMMDD_HHMMSS/`:
  `chat.jsonl`, `thoughts.jsonl`, and `turns.jsonl`.
- Hidden recipes remain hidden. Agents can craft only known recipe IDs or choose
  `experiment`.
- Provider modes:
  - `openai`: Responses API, requires `OPENAI_API_KEY`.
  - `ollama` / `--llama`: native Ollama `/api/chat` endpoint with structured
    JSON schema output.
  - `compatible`: Chat Completions endpoint for LM Studio, llama.cpp servers,
    and similar local APIs.
  - `gemini` / `google`: Gemini `generateContent`, requires `GEMINI_API_KEY`
    or `AGENTS_SURVIVAL_GEMINI_API_KEY`.
  - mixed Gemini mode: set `--gemini-agents N` while using another primary
    provider, so only N agents use Gemini and the others keep using the
    existing provider.

## Sprites

Put PNG files in `assets/sprites` using the filenames listed in
[docs/SPRITES.md](docs/SPRITES.md). If a file is missing, the game uses a
readable placeholder and writes `docs/missing_sprites.md`.

Run with `--asset-wizard` if you want the game to ask for sprite file paths at
startup.

To generate the whole sprite set as one ChatGPT image:

```powershell
python tools\make_sprite_atlas_prompt.py
```

The old one-image atlas route is fragile for the expanded sprite manifest. The
preferred route is now several smaller `8x8` ChatGPT batches:

```powershell
python tools\make_sprite_batch_prompts.py
```

Copy prompts from `docs/sprite_batch_prompts.md`, save each generated PNG into
`assets/generated/`, then import one batch like this:

```powershell
python tools\import_sprite_batch_atlas.py 01_terrain_and_nature_features assets\generated\01_terrain_and_nature_features.png --replace-existing --preview
```

The older single-atlas prompt asks for one large atlas. Paste that prompt into
ChatGPT image generation, save the result as `assets/generated/chatgpt_sprite_atlas.png`,
then slice it:

```powershell
python tools\import_sprite_atlas.py assets\generated\chatgpt_sprite_atlas.png --replace-existing --preview
```

If ChatGPT creates a pretty but imperfect atlas like the first pass, salvage the
known cells with:

```powershell
python tools\salvage_chatgpt_atlas.py "C:\path\to\ChatGPT Image.png" --replace-existing
```

If sliced sprites still have pink chroma-key fringes, run:

```powershell
python tools\clean_magenta_fringe.py
```

When new features, NPCs, or items are added and you do not have final art yet,
write simple PNG placeholders for every missing sprite:

```powershell
python tools\generate_missing_sprites.py
```

For the expanded survival item atlas, use the dedicated importer. It writes any
detected sprites in visual order and leaves the rest as placeholders:

```powershell
python tools\import_expanded_survival_atlas.py "C:\path\to\ChatGPT Image.png" --preview
```

## Replays

The game no longer records gameplay as MP4 by default. Every run writes replay
data into its log session:

- `world.json`: terrain, shade, and agent identity metadata.
- `replay.jsonl`: one compact post-round world/agent/chat snapshot per round.

Play the newest replay without LLM delays:

```powershell
python tools\play_replay.py
```

Or open a specific session:

```powershell
python tools\play_replay.py logs\session_YYYYMMDD_HHMMSS --speed 3
```

Replay controls: WASD/arrows move the spectator camera, Tab selects an agent,
F follows the selected agent, Space pauses, `+`/`-` changes speed, `[`/`]`
steps frames, and `B` opens the recipe book.
