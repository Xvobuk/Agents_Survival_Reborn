# Advanced Progression Sprite Atlas Prompt

Use this prompt in ChatGPT image generation for the next sprite pass.

```text
Create a transparent PNG sprite atlas for a top-down 2D survival sandbox game.

Style:
- cozy detailed painted pixel art / 32-bit survival RPG sprites
- transparent background with real alpha, no colored background
- no labels, no text, no numbers, no captions
- one isolated sprite per cell
- each sprite centered with padding
- clean 6 columns x 6 rows grid, 36 cells total
- sprites must be readable when resized to 32x32 pixels
- do not draw a scene, do not connect sprites with shadows
- keep silhouettes simple and clear

Canvas:
- square transparent PNG, ideally 1536x1536
- exactly 6 columns and 6 rows
- leave empty transparent cells only where the list says "blank"

Atlas order, left to right, top to bottom:

Row 1:
1. Wolf, gray hostile forest predator, top-down/isometric small animal sprite
2. Bear, large brown hostile predator, compact readable silhouette
3. Snake, green/dark snake, coiled or curved hostile creature
4. Potion stand, small alchemy station with bottles and metal/stone base
5. Glass bottle, empty clear potion bottle inventory icon
6. Hide, rough animal hide / pelt inventory icon

Row 2:
7. Leather, worked brown leather sheet inventory icon
8. Venom sac, small green poisonous sac inventory icon
9. Copper axe, copper-headed axe with wooden handle
10. Copper sword, short copper sword
11. Iron axe, iron-headed axe with wooden handle
12. Iron sword, clean iron sword

Row 3:
13. Diamond-edged pickaxe, iron pickaxe with blue diamond edge
14. Diamond-edged sword, iron sword with blue diamond edge
15. Copper ring, simple copper ring
16. Gold ring, shiny gold ring
17. Gold necklace, gold necklace / chain
18. Diamond ring, gold ring with blue diamond

Row 4:
19. Diamond amulet, gold amulet with blue diamond gem
20. Leather cap, leather head armor
21. Leather gloves, pair of leather gloves
22. Leather tunic, leather chest armor
23. Leather pants, leather leg armor
24. Leather boots, pair of leather boots

Row 5:
25. Iron helmet, iron head armor
26. Iron gauntlets, pair of iron gauntlets
27. Iron chestplate, iron torso armor
28. Iron greaves, iron leg armor
29. Iron boots, pair of iron boots
30. Healing potion, red potion bottle

Row 6:
31. Stamina potion, yellow or blue energetic potion bottle
32. Antidote, green antidote potion bottle
33. Cactus flesh, juicy green cactus slice
34. Cactus spine, sharp pale cactus needles
35. Fishing rod, simple wooden fishing rod with line and hook
36. Chat UI icon, small speech bubble icon

Important:
- Include exactly these 36 sprites.
- Keep every sprite fully inside its own invisible grid cell.
- Do not draw duplicate alternatives.
- Do not draw extra decorations, extra items, background gradients, or scenery.
- Make the transparent alpha clean so the atlas is easy to slice automatically.
```

