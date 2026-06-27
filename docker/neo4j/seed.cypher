// ============================================================
// Seed: Fashion Knowledge Graph (Neo4j)
// Auto-runs via neo4j-seeder container on first docker compose up
// ============================================================

// ── Concepts (existing) ──────────────────────────────────────
MERGE (:Concept {id: 'STYLE_KOREAN_CASUAL',    name: 'Korean Casual',        type: 'style'});
MERGE (:Concept {id: 'STYLE_STREETWEAR',        name: 'Streetwear',           type: 'style'});
MERGE (:Concept {id: 'STYLE_BOHO',              name: 'Bohemian',             type: 'style'});
MERGE (:Concept {id: 'STYLE_MINIMALIST',        name: 'Minimalist',           type: 'style'});
MERGE (:Concept {id: 'BODY_PETITE',             name: 'Petite',               type: 'body_context'});
MERGE (:Concept {id: 'BODY_TALL',               name: 'Tall',                 type: 'body_context'});
MERGE (:Concept {id: 'BODY_CURVY',              name: 'Curvy',                type: 'body_context'});
MERGE (:Concept {id: 'OCCASION_BEACH_TRAVEL',   name: 'Beach Travel',         type: 'occasion'});
MERGE (:Concept {id: 'OCCASION_OFFICE',         name: 'Office',               type: 'occasion'});
MERGE (:Concept {id: 'OCCASION_DATE',           name: 'Date Night',           type: 'occasion'});
MERGE (:Concept {id: 'OCCASION_CASUAL_DAILY',   name: 'Casual Daily',         type: 'occasion'});
MERGE (:Concept {id: 'PREF_MODEST',             name: 'Modest',               type: 'preference'});
MERGE (:Concept {id: 'PREF_SEXY',               name: 'Confident/Sexy',       type: 'preference'});
MERGE (:Concept {id: 'FABRIC_BREATHABLE',       name: 'Breathable',           type: 'material_property'});
MERGE (:Concept {id: 'FABRIC_WARM',             name: 'Warm Fabric',          type: 'material_property'});
MERGE (:Concept {id: 'COLOR_NEUTRAL',           name: 'Neutral Colors',       type: 'color'});
MERGE (:Concept {id: 'COLOR_PASTEL',            name: 'Pastel Colors',        type: 'color'});
MERGE (:Concept {id: 'COLOR_BOLD',              name: 'Bold Colors',          type: 'color'});
MERGE (:Concept {id: 'FIT_HIGH_WAIST',          name: 'High Waist',           type: 'fit'});
MERGE (:Concept {id: 'ITEM_WIDE_LEG_PANTS',     name: 'Wide Leg Pants',       type: 'item_type'});
MERGE (:Concept {id: 'ITEM_MIDI_SKIRT',         name: 'Midi Skirt',           type: 'item_type'});
MERGE (:Concept {id: 'ITEM_MINI_SKIRT',         name: 'Mini Skirt',           type: 'item_type'});
MERGE (:Concept {id: 'ITEM_OVERSIZED_SHIRT',    name: 'Oversized Shirt',      type: 'item_type'});
MERGE (:Concept {id: 'ITEM_CROPPED_TOP',        name: 'Cropped Top',          type: 'item_type'});
MERGE (:Concept {id: 'ITEM_SANDAL',             name: 'Sandal',               type: 'item_type'});
MERGE (:Concept {id: 'NECKLINE_DEEP_V',         name: 'Deep V Neckline',      type: 'neckline'});

// ── Concepts (new items) ─────────────────────────────────────
MERGE (:Concept {id: 'ITEM_BLAZER',             name: 'Blazer',               type: 'item_type'});
MERGE (:Concept {id: 'ITEM_JEANS',              name: 'Jeans',                type: 'item_type'});
MERGE (:Concept {id: 'ITEM_HEELS',              name: 'High Heels',           type: 'item_type'});
MERGE (:Concept {id: 'ITEM_BOOTS',              name: 'Boots',                type: 'item_type'});
MERGE (:Concept {id: 'ITEM_HOODIE',             name: 'Hoodie',               type: 'item_type'});
MERGE (:Concept {id: 'ITEM_WRAP_DRESS',         name: 'Wrap Dress',           type: 'item_type'});
MERGE (:Concept {id: 'ITEM_MAXI_DRESS',         name: 'Maxi Dress',           type: 'item_type'});
MERGE (:Concept {id: 'ITEM_CARGO_PANTS',        name: 'Cargo Pants',          type: 'item_type'});
MERGE (:Concept {id: 'ITEM_TURTLENECK',         name: 'Turtleneck',           type: 'item_type'});
MERGE (:Concept {id: 'ITEM_BODYSUIT',           name: 'Bodysuit',             type: 'item_type'});
MERGE (:Concept {id: 'ITEM_SNEAKERS',           name: 'Sneakers',             type: 'item_type'});
MERGE (:Concept {id: 'ITEM_SHORTS',             name: 'Shorts',               type: 'item_type'});

// ── Concepts (new fits) ──────────────────────────────────────
MERGE (:Concept {id: 'FIT_A_LINE',              name: 'A-Line Silhouette',    type: 'fit'});
MERGE (:Concept {id: 'FIT_FITTED',              name: 'Fitted / Form-fitting', type: 'fit'});
MERGE (:Concept {id: 'FIT_LOOSE',               name: 'Loose / Oversized',    type: 'fit'});

// ── Concepts (new colors) ────────────────────────────────────
MERGE (:Concept {id: 'COLOR_DARK',              name: 'Dark Colors',          type: 'color'});
MERGE (:Concept {id: 'COLOR_EARTH_TONE',        name: 'Earth Tones',          type: 'color'});

// ── Concepts (new occasions) ─────────────────────────────────
MERGE (:Concept {id: 'OCCASION_PARTY',          name: 'Party / Night Out',    type: 'occasion'});
MERGE (:Concept {id: 'OCCASION_SPORT',          name: 'Sport / Gym',          type: 'occasion'});
MERGE (:Concept {id: 'OCCASION_WEDDING_GUEST',  name: 'Wedding Guest',        type: 'occasion'});

// ── Concepts (new styles) ────────────────────────────────────
MERGE (:Concept {id: 'STYLE_OLD_MONEY',         name: 'Old Money',            type: 'style'});
MERGE (:Concept {id: 'STYLE_SPORTY',            name: 'Sporty',               type: 'style'});
MERGE (:Concept {id: 'STYLE_FEMININE',          name: 'Feminine',             type: 'style'});
MERGE (:Concept {id: 'STYLE_DARK_ACADEMIA',     name: 'Dark Academia',        type: 'style'});

// ── Concepts (new body / preference) ────────────────────────
MERGE (:Concept {id: 'BODY_ATHLETIC',           name: 'Athletic',             type: 'body_context'});
MERGE (:Concept {id: 'PREF_COMFORTABLE',        name: 'Comfortable / Casual', type: 'preference'});

// ── Index ────────────────────────────────────────────────────
CREATE INDEX concept_id_index IF NOT EXISTS FOR (c:Concept) ON (c.id);

// ════════════════════════════════════════════════════════════
// Relationships
// ════════════════════════════════════════════════════════════

// ── STYLE_KOREAN_CASUAL ──────────────────────────────────────
MATCH (a:Concept {id: 'STYLE_KOREAN_CASUAL'}), (b:Concept {id: 'ITEM_WIDE_LEG_PANTS'})
MERGE (a)-[:PREFERS {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'STYLE_KOREAN_CASUAL'}), (b:Concept {id: 'ITEM_OVERSIZED_SHIRT'})
MERGE (a)-[:PREFERS {weight: 0.80}]->(b);
MATCH (a:Concept {id: 'STYLE_KOREAN_CASUAL'}), (b:Concept {id: 'ITEM_MIDI_SKIRT'})
MERGE (a)-[:PREFERS {weight: 0.75}]->(b);
MATCH (a:Concept {id: 'STYLE_KOREAN_CASUAL'}), (b:Concept {id: 'ITEM_JEANS'})
MERGE (a)-[:PREFERS {weight: 0.75}]->(b);
MATCH (a:Concept {id: 'STYLE_KOREAN_CASUAL'}), (b:Concept {id: 'ITEM_SNEAKERS'})
MERGE (a)-[:PREFERS {weight: 0.80}]->(b);
MATCH (a:Concept {id: 'STYLE_KOREAN_CASUAL'}), (b:Concept {id: 'COLOR_NEUTRAL'})
MERGE (a)-[:PREFERS {weight: 0.90}]->(b);
MATCH (a:Concept {id: 'STYLE_KOREAN_CASUAL'}), (b:Concept {id: 'COLOR_PASTEL'})
MERGE (a)-[:PREFERS {weight: 0.80}]->(b);
MATCH (a:Concept {id: 'STYLE_KOREAN_CASUAL'}), (b:Concept {id: 'STYLE_MINIMALIST'})
MERGE (a)-[:COMPATIBLE_WITH {weight: 0.85}]->(b);

// ── STYLE_STREETWEAR ─────────────────────────────────────────
MATCH (a:Concept {id: 'STYLE_STREETWEAR'}), (b:Concept {id: 'ITEM_HOODIE'})
MERGE (a)-[:PREFERS {weight: 0.90}]->(b);
MATCH (a:Concept {id: 'STYLE_STREETWEAR'}), (b:Concept {id: 'ITEM_CARGO_PANTS'})
MERGE (a)-[:PREFERS {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'STYLE_STREETWEAR'}), (b:Concept {id: 'ITEM_SNEAKERS'})
MERGE (a)-[:PREFERS {weight: 0.95}]->(b);
MATCH (a:Concept {id: 'STYLE_STREETWEAR'}), (b:Concept {id: 'ITEM_OVERSIZED_SHIRT'})
MERGE (a)-[:PREFERS {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'STYLE_STREETWEAR'}), (b:Concept {id: 'ITEM_JEANS'})
MERGE (a)-[:PREFERS {weight: 0.80}]->(b);
MATCH (a:Concept {id: 'STYLE_STREETWEAR'}), (b:Concept {id: 'COLOR_BOLD'})
MERGE (a)-[:PREFERS {weight: 0.75}]->(b);
MATCH (a:Concept {id: 'STYLE_STREETWEAR'}), (b:Concept {id: 'FIT_LOOSE'})
MERGE (a)-[:PREFERS {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'STYLE_STREETWEAR'}), (b:Concept {id: 'ITEM_HEELS'})
MERGE (a)-[:AVOIDS {weight: 0.80}]->(b);
MATCH (a:Concept {id: 'STYLE_STREETWEAR'}), (b:Concept {id: 'ITEM_MIDI_SKIRT'})
MERGE (a)-[:AVOIDS {weight: 0.65}]->(b);

// ── STYLE_BOHO ───────────────────────────────────────────────
MATCH (a:Concept {id: 'STYLE_BOHO'}), (b:Concept {id: 'ITEM_MAXI_DRESS'})
MERGE (a)-[:PREFERS {weight: 0.95}]->(b);
MATCH (a:Concept {id: 'STYLE_BOHO'}), (b:Concept {id: 'ITEM_WIDE_LEG_PANTS'})
MERGE (a)-[:PREFERS {weight: 0.80}]->(b);
MATCH (a:Concept {id: 'STYLE_BOHO'}), (b:Concept {id: 'ITEM_SANDAL'})
MERGE (a)-[:PREFERS {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'STYLE_BOHO'}), (b:Concept {id: 'COLOR_EARTH_TONE'})
MERGE (a)-[:PREFERS {weight: 0.90}]->(b);
MATCH (a:Concept {id: 'STYLE_BOHO'}), (b:Concept {id: 'FABRIC_BREATHABLE'})
MERGE (a)-[:PREFERS {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'STYLE_BOHO'}), (b:Concept {id: 'FIT_LOOSE'})
MERGE (a)-[:PREFERS {weight: 0.80}]->(b);
MATCH (a:Concept {id: 'STYLE_BOHO'}), (b:Concept {id: 'ITEM_MIDI_SKIRT'})
MERGE (a)-[:PREFERS {weight: 0.75}]->(b);
MATCH (a:Concept {id: 'STYLE_BOHO'}), (b:Concept {id: 'ITEM_BLAZER'})
MERGE (a)-[:AVOIDS {weight: 0.70}]->(b);

// ── STYLE_MINIMALIST ─────────────────────────────────────────
MATCH (a:Concept {id: 'STYLE_MINIMALIST'}), (b:Concept {id: 'COLOR_NEUTRAL'})
MERGE (a)-[:PREFERS {weight: 0.95}]->(b);
MATCH (a:Concept {id: 'STYLE_MINIMALIST'}), (b:Concept {id: 'FIT_FITTED'})
MERGE (a)-[:PREFERS {weight: 0.80}]->(b);
MATCH (a:Concept {id: 'STYLE_MINIMALIST'}), (b:Concept {id: 'ITEM_WIDE_LEG_PANTS'})
MERGE (a)-[:PREFERS {weight: 0.80}]->(b);
MATCH (a:Concept {id: 'STYLE_MINIMALIST'}), (b:Concept {id: 'ITEM_TURTLENECK'})
MERGE (a)-[:PREFERS {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'STYLE_MINIMALIST'}), (b:Concept {id: 'ITEM_BLAZER'})
MERGE (a)-[:PREFERS {weight: 0.80}]->(b);
MATCH (a:Concept {id: 'STYLE_MINIMALIST'}), (b:Concept {id: 'COLOR_BOLD'})
MERGE (a)-[:AVOIDS {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'STYLE_MINIMALIST'}), (b:Concept {id: 'ITEM_HOODIE'})
MERGE (a)-[:AVOIDS {weight: 0.70}]->(b);

// ── STYLE_OLD_MONEY ──────────────────────────────────────────
MATCH (a:Concept {id: 'STYLE_OLD_MONEY'}), (b:Concept {id: 'ITEM_BLAZER'})
MERGE (a)-[:PREFERS {weight: 0.95}]->(b);
MATCH (a:Concept {id: 'STYLE_OLD_MONEY'}), (b:Concept {id: 'ITEM_WIDE_LEG_PANTS'})
MERGE (a)-[:PREFERS {weight: 0.90}]->(b);
MATCH (a:Concept {id: 'STYLE_OLD_MONEY'}), (b:Concept {id: 'ITEM_TURTLENECK'})
MERGE (a)-[:PREFERS {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'STYLE_OLD_MONEY'}), (b:Concept {id: 'ITEM_MIDI_SKIRT'})
MERGE (a)-[:PREFERS {weight: 0.80}]->(b);
MATCH (a:Concept {id: 'STYLE_OLD_MONEY'}), (b:Concept {id: 'ITEM_BOOTS'})
MERGE (a)-[:PREFERS {weight: 0.80}]->(b);
MATCH (a:Concept {id: 'STYLE_OLD_MONEY'}), (b:Concept {id: 'COLOR_NEUTRAL'})
MERGE (a)-[:PREFERS {weight: 0.90}]->(b);
MATCH (a:Concept {id: 'STYLE_OLD_MONEY'}), (b:Concept {id: 'COLOR_EARTH_TONE'})
MERGE (a)-[:PREFERS {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'STYLE_OLD_MONEY'}), (b:Concept {id: 'FABRIC_WARM'})
MERGE (a)-[:PREFERS {weight: 0.70}]->(b);
MATCH (a:Concept {id: 'STYLE_OLD_MONEY'}), (b:Concept {id: 'ITEM_HOODIE'})
MERGE (a)-[:AVOIDS {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'STYLE_OLD_MONEY'}), (b:Concept {id: 'COLOR_BOLD'})
MERGE (a)-[:AVOIDS {weight: 0.70}]->(b);
MATCH (a:Concept {id: 'STYLE_OLD_MONEY'}), (b:Concept {id: 'ITEM_CARGO_PANTS'})
MERGE (a)-[:AVOIDS {weight: 0.90}]->(b);

// ── STYLE_SPORTY ─────────────────────────────────────────────
MATCH (a:Concept {id: 'STYLE_SPORTY'}), (b:Concept {id: 'ITEM_SNEAKERS'})
MERGE (a)-[:PREFERS {weight: 0.95}]->(b);
MATCH (a:Concept {id: 'STYLE_SPORTY'}), (b:Concept {id: 'ITEM_SHORTS'})
MERGE (a)-[:PREFERS {weight: 0.90}]->(b);
MATCH (a:Concept {id: 'STYLE_SPORTY'}), (b:Concept {id: 'ITEM_HOODIE'})
MERGE (a)-[:PREFERS {weight: 0.90}]->(b);
MATCH (a:Concept {id: 'STYLE_SPORTY'}), (b:Concept {id: 'FABRIC_BREATHABLE'})
MERGE (a)-[:PREFERS {weight: 0.95}]->(b);
MATCH (a:Concept {id: 'STYLE_SPORTY'}), (b:Concept {id: 'ITEM_JEANS'})
MERGE (a)-[:PREFERS {weight: 0.70}]->(b);
MATCH (a:Concept {id: 'STYLE_SPORTY'}), (b:Concept {id: 'ITEM_HEELS'})
MERGE (a)-[:AVOIDS {weight: 0.95}]->(b);
MATCH (a:Concept {id: 'STYLE_SPORTY'}), (b:Concept {id: 'ITEM_BLAZER'})
MERGE (a)-[:AVOIDS {weight: 0.80}]->(b);
MATCH (a:Concept {id: 'STYLE_SPORTY'}), (b:Concept {id: 'ITEM_MIDI_SKIRT'})
MERGE (a)-[:AVOIDS {weight: 0.70}]->(b);

// ── STYLE_FEMININE ───────────────────────────────────────────
MATCH (a:Concept {id: 'STYLE_FEMININE'}), (b:Concept {id: 'ITEM_WRAP_DRESS'})
MERGE (a)-[:PREFERS {weight: 0.90}]->(b);
MATCH (a:Concept {id: 'STYLE_FEMININE'}), (b:Concept {id: 'ITEM_MIDI_SKIRT'})
MERGE (a)-[:PREFERS {weight: 0.90}]->(b);
MATCH (a:Concept {id: 'STYLE_FEMININE'}), (b:Concept {id: 'ITEM_MAXI_DRESS'})
MERGE (a)-[:PREFERS {weight: 0.80}]->(b);
MATCH (a:Concept {id: 'STYLE_FEMININE'}), (b:Concept {id: 'ITEM_HEELS'})
MERGE (a)-[:PREFERS {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'STYLE_FEMININE'}), (b:Concept {id: 'FIT_A_LINE'})
MERGE (a)-[:PREFERS {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'STYLE_FEMININE'}), (b:Concept {id: 'COLOR_PASTEL'})
MERGE (a)-[:PREFERS {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'STYLE_FEMININE'}), (b:Concept {id: 'ITEM_CROPPED_TOP'})
MERGE (a)-[:PREFERS {weight: 0.75}]->(b);
MATCH (a:Concept {id: 'STYLE_FEMININE'}), (b:Concept {id: 'ITEM_CARGO_PANTS'})
MERGE (a)-[:AVOIDS {weight: 0.80}]->(b);
MATCH (a:Concept {id: 'STYLE_FEMININE'}), (b:Concept {id: 'ITEM_HOODIE'})
MERGE (a)-[:AVOIDS {weight: 0.65}]->(b);

// ── STYLE_DARK_ACADEMIA ──────────────────────────────────────
MATCH (a:Concept {id: 'STYLE_DARK_ACADEMIA'}), (b:Concept {id: 'ITEM_BLAZER'})
MERGE (a)-[:PREFERS {weight: 0.95}]->(b);
MATCH (a:Concept {id: 'STYLE_DARK_ACADEMIA'}), (b:Concept {id: 'ITEM_TURTLENECK'})
MERGE (a)-[:PREFERS {weight: 0.90}]->(b);
MATCH (a:Concept {id: 'STYLE_DARK_ACADEMIA'}), (b:Concept {id: 'ITEM_MIDI_SKIRT'})
MERGE (a)-[:PREFERS {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'STYLE_DARK_ACADEMIA'}), (b:Concept {id: 'ITEM_BOOTS'})
MERGE (a)-[:PREFERS {weight: 0.90}]->(b);
MATCH (a:Concept {id: 'STYLE_DARK_ACADEMIA'}), (b:Concept {id: 'COLOR_DARK'})
MERGE (a)-[:PREFERS {weight: 0.95}]->(b);
MATCH (a:Concept {id: 'STYLE_DARK_ACADEMIA'}), (b:Concept {id: 'COLOR_EARTH_TONE'})
MERGE (a)-[:PREFERS {weight: 0.80}]->(b);
MATCH (a:Concept {id: 'STYLE_DARK_ACADEMIA'}), (b:Concept {id: 'ITEM_WIDE_LEG_PANTS'})
MERGE (a)-[:PREFERS {weight: 0.75}]->(b);
MATCH (a:Concept {id: 'STYLE_DARK_ACADEMIA'}), (b:Concept {id: 'COLOR_BOLD'})
MERGE (a)-[:AVOIDS {weight: 0.80}]->(b);
MATCH (a:Concept {id: 'STYLE_DARK_ACADEMIA'}), (b:Concept {id: 'ITEM_SNEAKERS'})
MERGE (a)-[:AVOIDS {weight: 0.65}]->(b);
MATCH (a:Concept {id: 'STYLE_DARK_ACADEMIA'}), (b:Concept {id: 'ITEM_SHORTS'})
MERGE (a)-[:AVOIDS {weight: 0.85}]->(b);

// ── BODY_PETITE ──────────────────────────────────────────────
MATCH (a:Concept {id: 'BODY_PETITE'}), (b:Concept {id: 'FIT_HIGH_WAIST'})
MERGE (a)-[:PREFERS {weight: 0.95}]->(b);
MATCH (a:Concept {id: 'BODY_PETITE'}), (b:Concept {id: 'ITEM_MIDI_SKIRT'})
MERGE (a)-[:PREFERS {weight: 0.80}]->(b);
MATCH (a:Concept {id: 'BODY_PETITE'}), (b:Concept {id: 'ITEM_CROPPED_TOP'})
MERGE (a)-[:PREFERS {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'BODY_PETITE'}), (b:Concept {id: 'COLOR_NEUTRAL'})
MERGE (a)-[:PREFERS {weight: 0.70}]->(b);
MATCH (a:Concept {id: 'BODY_PETITE'}), (b:Concept {id: 'ITEM_HEELS'})
MERGE (a)-[:PREFERS {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'BODY_PETITE'}), (b:Concept {id: 'ITEM_WRAP_DRESS'})
MERGE (a)-[:PREFERS {weight: 0.80}]->(b);
MATCH (a:Concept {id: 'BODY_PETITE'}), (b:Concept {id: 'ITEM_OVERSIZED_SHIRT'})
MERGE (a)-[:AVOIDS {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'BODY_PETITE'}), (b:Concept {id: 'ITEM_MAXI_DRESS'})
MERGE (a)-[:AVOIDS {weight: 0.70}]->(b);
MATCH (a:Concept {id: 'BODY_PETITE'}), (b:Concept {id: 'FIT_LOOSE'})
MERGE (a)-[:AVOIDS {weight: 0.75}]->(b);

// ── BODY_TALL ────────────────────────────────────────────────
MATCH (a:Concept {id: 'BODY_TALL'}), (b:Concept {id: 'ITEM_MAXI_DRESS'})
MERGE (a)-[:PREFERS {weight: 0.90}]->(b);
MATCH (a:Concept {id: 'BODY_TALL'}), (b:Concept {id: 'ITEM_WIDE_LEG_PANTS'})
MERGE (a)-[:PREFERS {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'BODY_TALL'}), (b:Concept {id: 'FIT_FITTED'})
MERGE (a)-[:PREFERS {weight: 0.80}]->(b);
MATCH (a:Concept {id: 'BODY_TALL'}), (b:Concept {id: 'COLOR_DARK'})
MERGE (a)-[:PREFERS {weight: 0.75}]->(b);
MATCH (a:Concept {id: 'BODY_TALL'}), (b:Concept {id: 'ITEM_BOOTS'})
MERGE (a)-[:PREFERS {weight: 0.80}]->(b);
MATCH (a:Concept {id: 'BODY_TALL'}), (b:Concept {id: 'ITEM_BLAZER'})
MERGE (a)-[:PREFERS {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'BODY_TALL'}), (b:Concept {id: 'STYLE_OLD_MONEY'})
MERGE (a)-[:COMPATIBLE_WITH {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'BODY_TALL'}), (b:Concept {id: 'STYLE_DARK_ACADEMIA'})
MERGE (a)-[:COMPATIBLE_WITH {weight: 0.80}]->(b);

// ── BODY_CURVY ───────────────────────────────────────────────
MATCH (a:Concept {id: 'BODY_CURVY'}), (b:Concept {id: 'ITEM_WRAP_DRESS'})
MERGE (a)-[:PREFERS {weight: 0.95}]->(b);
MATCH (a:Concept {id: 'BODY_CURVY'}), (b:Concept {id: 'FIT_A_LINE'})
MERGE (a)-[:PREFERS {weight: 0.90}]->(b);
MATCH (a:Concept {id: 'BODY_CURVY'}), (b:Concept {id: 'FIT_HIGH_WAIST'})
MERGE (a)-[:PREFERS {weight: 0.90}]->(b);
MATCH (a:Concept {id: 'BODY_CURVY'}), (b:Concept {id: 'ITEM_MIDI_SKIRT'})
MERGE (a)-[:PREFERS {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'BODY_CURVY'}), (b:Concept {id: 'COLOR_DARK'})
MERGE (a)-[:PREFERS {weight: 0.75}]->(b);
MATCH (a:Concept {id: 'BODY_CURVY'}), (b:Concept {id: 'ITEM_BODYSUIT'})
MERGE (a)-[:PREFERS {weight: 0.80}]->(b);
MATCH (a:Concept {id: 'BODY_CURVY'}), (b:Concept {id: 'FIT_LOOSE'})
MERGE (a)-[:AVOIDS {weight: 0.70}]->(b);
MATCH (a:Concept {id: 'BODY_CURVY'}), (b:Concept {id: 'ITEM_CARGO_PANTS'})
MERGE (a)-[:AVOIDS {weight: 0.65}]->(b);

// ── BODY_ATHLETIC ────────────────────────────────────────────
MATCH (a:Concept {id: 'BODY_ATHLETIC'}), (b:Concept {id: 'ITEM_BODYSUIT'})
MERGE (a)-[:PREFERS {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'BODY_ATHLETIC'}), (b:Concept {id: 'FIT_FITTED'})
MERGE (a)-[:PREFERS {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'BODY_ATHLETIC'}), (b:Concept {id: 'ITEM_WIDE_LEG_PANTS'})
MERGE (a)-[:PREFERS {weight: 0.80}]->(b);
MATCH (a:Concept {id: 'BODY_ATHLETIC'}), (b:Concept {id: 'ITEM_MIDI_SKIRT'})
MERGE (a)-[:PREFERS {weight: 0.75}]->(b);
MATCH (a:Concept {id: 'BODY_ATHLETIC'}), (b:Concept {id: 'ITEM_WRAP_DRESS'})
MERGE (a)-[:PREFERS {weight: 0.80}]->(b);
MATCH (a:Concept {id: 'BODY_ATHLETIC'}), (b:Concept {id: 'STYLE_SPORTY'})
MERGE (a)-[:COMPATIBLE_WITH {weight: 0.90}]->(b);

// ── OCCASION_BEACH_TRAVEL ────────────────────────────────────
MATCH (a:Concept {id: 'OCCASION_BEACH_TRAVEL'}), (b:Concept {id: 'FABRIC_BREATHABLE'})
MERGE (a)-[:PREFERS {weight: 0.95}]->(b);
MATCH (a:Concept {id: 'OCCASION_BEACH_TRAVEL'}), (b:Concept {id: 'ITEM_SANDAL'})
MERGE (a)-[:PREFERS {weight: 0.90}]->(b);
MATCH (a:Concept {id: 'OCCASION_BEACH_TRAVEL'}), (b:Concept {id: 'COLOR_PASTEL'})
MERGE (a)-[:PREFERS {weight: 0.70}]->(b);
MATCH (a:Concept {id: 'OCCASION_BEACH_TRAVEL'}), (b:Concept {id: 'ITEM_MAXI_DRESS'})
MERGE (a)-[:PREFERS {weight: 0.80}]->(b);
MATCH (a:Concept {id: 'OCCASION_BEACH_TRAVEL'}), (b:Concept {id: 'ITEM_SHORTS'})
MERGE (a)-[:PREFERS {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'OCCASION_BEACH_TRAVEL'}), (b:Concept {id: 'FABRIC_WARM'})
MERGE (a)-[:AVOIDS {weight: 0.90}]->(b);
MATCH (a:Concept {id: 'OCCASION_BEACH_TRAVEL'}), (b:Concept {id: 'ITEM_BOOTS'})
MERGE (a)-[:AVOIDS {weight: 0.80}]->(b);
MATCH (a:Concept {id: 'OCCASION_BEACH_TRAVEL'}), (b:Concept {id: 'ITEM_BLAZER'})
MERGE (a)-[:AVOIDS {weight: 0.85}]->(b);

// ── OCCASION_OFFICE ──────────────────────────────────────────
MATCH (a:Concept {id: 'OCCASION_OFFICE'}), (b:Concept {id: 'ITEM_BLAZER'})
MERGE (a)-[:PREFERS {weight: 0.95}]->(b);
MATCH (a:Concept {id: 'OCCASION_OFFICE'}), (b:Concept {id: 'ITEM_WIDE_LEG_PANTS'})
MERGE (a)-[:PREFERS {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'OCCASION_OFFICE'}), (b:Concept {id: 'ITEM_MIDI_SKIRT'})
MERGE (a)-[:PREFERS {weight: 0.90}]->(b);
MATCH (a:Concept {id: 'OCCASION_OFFICE'}), (b:Concept {id: 'ITEM_TURTLENECK'})
MERGE (a)-[:PREFERS {weight: 0.80}]->(b);
MATCH (a:Concept {id: 'OCCASION_OFFICE'}), (b:Concept {id: 'COLOR_NEUTRAL'})
MERGE (a)-[:PREFERS {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'OCCASION_OFFICE'}), (b:Concept {id: 'COLOR_DARK'})
MERGE (a)-[:PREFERS {weight: 0.80}]->(b);
MATCH (a:Concept {id: 'OCCASION_OFFICE'}), (b:Concept {id: 'ITEM_HEELS'})
MERGE (a)-[:PREFERS {weight: 0.75}]->(b);
MATCH (a:Concept {id: 'OCCASION_OFFICE'}), (b:Concept {id: 'STYLE_MINIMALIST'})
MERGE (a)-[:COMPATIBLE_WITH {weight: 0.90}]->(b);
MATCH (a:Concept {id: 'OCCASION_OFFICE'}), (b:Concept {id: 'STYLE_OLD_MONEY'})
MERGE (a)-[:COMPATIBLE_WITH {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'OCCASION_OFFICE'}), (b:Concept {id: 'ITEM_SHORTS'})
MERGE (a)-[:AVOIDS {weight: 0.90}]->(b);
MATCH (a:Concept {id: 'OCCASION_OFFICE'}), (b:Concept {id: 'ITEM_MINI_SKIRT'})
MERGE (a)-[:AVOIDS {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'OCCASION_OFFICE'}), (b:Concept {id: 'ITEM_CROPPED_TOP'})
MERGE (a)-[:AVOIDS {weight: 0.90}]->(b);
MATCH (a:Concept {id: 'OCCASION_OFFICE'}), (b:Concept {id: 'ITEM_HOODIE'})
MERGE (a)-[:AVOIDS {weight: 0.80}]->(b);

// ── OCCASION_DATE ────────────────────────────────────────────
MATCH (a:Concept {id: 'OCCASION_DATE'}), (b:Concept {id: 'ITEM_WRAP_DRESS'})
MERGE (a)-[:PREFERS {weight: 0.90}]->(b);
MATCH (a:Concept {id: 'OCCASION_DATE'}), (b:Concept {id: 'ITEM_MIDI_SKIRT'})
MERGE (a)-[:PREFERS {weight: 0.80}]->(b);
MATCH (a:Concept {id: 'OCCASION_DATE'}), (b:Concept {id: 'ITEM_HEELS'})
MERGE (a)-[:PREFERS {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'OCCASION_DATE'}), (b:Concept {id: 'COLOR_BOLD'})
MERGE (a)-[:PREFERS {weight: 0.75}]->(b);
MATCH (a:Concept {id: 'OCCASION_DATE'}), (b:Concept {id: 'COLOR_PASTEL'})
MERGE (a)-[:PREFERS {weight: 0.70}]->(b);
MATCH (a:Concept {id: 'OCCASION_DATE'}), (b:Concept {id: 'NECKLINE_DEEP_V'})
MERGE (a)-[:PREFERS {weight: 0.70}]->(b);
MATCH (a:Concept {id: 'OCCASION_DATE'}), (b:Concept {id: 'STYLE_FEMININE'})
MERGE (a)-[:COMPATIBLE_WITH {weight: 0.90}]->(b);
MATCH (a:Concept {id: 'OCCASION_DATE'}), (b:Concept {id: 'ITEM_HOODIE'})
MERGE (a)-[:AVOIDS {weight: 0.70}]->(b);
MATCH (a:Concept {id: 'OCCASION_DATE'}), (b:Concept {id: 'ITEM_CARGO_PANTS'})
MERGE (a)-[:AVOIDS {weight: 0.75}]->(b);

// ── OCCASION_CASUAL_DAILY ────────────────────────────────────
MATCH (a:Concept {id: 'OCCASION_CASUAL_DAILY'}), (b:Concept {id: 'ITEM_JEANS'})
MERGE (a)-[:PREFERS {weight: 0.90}]->(b);
MATCH (a:Concept {id: 'OCCASION_CASUAL_DAILY'}), (b:Concept {id: 'ITEM_SNEAKERS'})
MERGE (a)-[:PREFERS {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'OCCASION_CASUAL_DAILY'}), (b:Concept {id: 'ITEM_OVERSIZED_SHIRT'})
MERGE (a)-[:PREFERS {weight: 0.80}]->(b);
MATCH (a:Concept {id: 'OCCASION_CASUAL_DAILY'}), (b:Concept {id: 'ITEM_HOODIE'})
MERGE (a)-[:PREFERS {weight: 0.75}]->(b);
MATCH (a:Concept {id: 'OCCASION_CASUAL_DAILY'}), (b:Concept {id: 'COLOR_NEUTRAL'})
MERGE (a)-[:PREFERS {weight: 0.80}]->(b);
MATCH (a:Concept {id: 'OCCASION_CASUAL_DAILY'}), (b:Concept {id: 'STYLE_KOREAN_CASUAL'})
MERGE (a)-[:COMPATIBLE_WITH {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'OCCASION_CASUAL_DAILY'}), (b:Concept {id: 'STYLE_MINIMALIST'})
MERGE (a)-[:COMPATIBLE_WITH {weight: 0.80}]->(b);

// ── OCCASION_PARTY ───────────────────────────────────────────
MATCH (a:Concept {id: 'OCCASION_PARTY'}), (b:Concept {id: 'ITEM_BODYSUIT'})
MERGE (a)-[:PREFERS {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'OCCASION_PARTY'}), (b:Concept {id: 'ITEM_MINI_SKIRT'})
MERGE (a)-[:PREFERS {weight: 0.80}]->(b);
MATCH (a:Concept {id: 'OCCASION_PARTY'}), (b:Concept {id: 'ITEM_HEELS'})
MERGE (a)-[:PREFERS {weight: 0.90}]->(b);
MATCH (a:Concept {id: 'OCCASION_PARTY'}), (b:Concept {id: 'ITEM_WRAP_DRESS'})
MERGE (a)-[:PREFERS {weight: 0.80}]->(b);
MATCH (a:Concept {id: 'OCCASION_PARTY'}), (b:Concept {id: 'COLOR_BOLD'})
MERGE (a)-[:PREFERS {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'OCCASION_PARTY'}), (b:Concept {id: 'NECKLINE_DEEP_V'})
MERGE (a)-[:PREFERS {weight: 0.75}]->(b);
MATCH (a:Concept {id: 'OCCASION_PARTY'}), (b:Concept {id: 'ITEM_SNEAKERS'})
MERGE (a)-[:AVOIDS {weight: 0.70}]->(b);
MATCH (a:Concept {id: 'OCCASION_PARTY'}), (b:Concept {id: 'ITEM_HOODIE'})
MERGE (a)-[:AVOIDS {weight: 0.85}]->(b);

// ── OCCASION_SPORT ───────────────────────────────────────────
MATCH (a:Concept {id: 'OCCASION_SPORT'}), (b:Concept {id: 'ITEM_SHORTS'})
MERGE (a)-[:PREFERS {weight: 0.90}]->(b);
MATCH (a:Concept {id: 'OCCASION_SPORT'}), (b:Concept {id: 'ITEM_SNEAKERS'})
MERGE (a)-[:PREFERS {weight: 0.95}]->(b);
MATCH (a:Concept {id: 'OCCASION_SPORT'}), (b:Concept {id: 'ITEM_HOODIE'})
MERGE (a)-[:PREFERS {weight: 0.80}]->(b);
MATCH (a:Concept {id: 'OCCASION_SPORT'}), (b:Concept {id: 'FABRIC_BREATHABLE'})
MERGE (a)-[:PREFERS {weight: 0.95}]->(b);
MATCH (a:Concept {id: 'OCCASION_SPORT'}), (b:Concept {id: 'STYLE_SPORTY'})
MERGE (a)-[:COMPATIBLE_WITH {weight: 0.95}]->(b);
MATCH (a:Concept {id: 'OCCASION_SPORT'}), (b:Concept {id: 'ITEM_HEELS'})
MERGE (a)-[:AVOIDS {weight: 0.99}]->(b);
MATCH (a:Concept {id: 'OCCASION_SPORT'}), (b:Concept {id: 'ITEM_BLAZER'})
MERGE (a)-[:AVOIDS {weight: 0.95}]->(b);
MATCH (a:Concept {id: 'OCCASION_SPORT'}), (b:Concept {id: 'ITEM_MIDI_SKIRT'})
MERGE (a)-[:AVOIDS {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'OCCASION_SPORT'}), (b:Concept {id: 'ITEM_JEANS'})
MERGE (a)-[:AVOIDS {weight: 0.80}]->(b);

// ── OCCASION_WEDDING_GUEST ───────────────────────────────────
MATCH (a:Concept {id: 'OCCASION_WEDDING_GUEST'}), (b:Concept {id: 'ITEM_MAXI_DRESS'})
MERGE (a)-[:PREFERS {weight: 0.90}]->(b);
MATCH (a:Concept {id: 'OCCASION_WEDDING_GUEST'}), (b:Concept {id: 'ITEM_MIDI_SKIRT'})
MERGE (a)-[:PREFERS {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'OCCASION_WEDDING_GUEST'}), (b:Concept {id: 'ITEM_HEELS'})
MERGE (a)-[:PREFERS {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'OCCASION_WEDDING_GUEST'}), (b:Concept {id: 'ITEM_WRAP_DRESS'})
MERGE (a)-[:PREFERS {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'OCCASION_WEDDING_GUEST'}), (b:Concept {id: 'COLOR_PASTEL'})
MERGE (a)-[:PREFERS {weight: 0.80}]->(b);
MATCH (a:Concept {id: 'OCCASION_WEDDING_GUEST'}), (b:Concept {id: 'STYLE_FEMININE'})
MERGE (a)-[:COMPATIBLE_WITH {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'OCCASION_WEDDING_GUEST'}), (b:Concept {id: 'ITEM_MINI_SKIRT'})
MERGE (a)-[:AVOIDS {weight: 0.80}]->(b);
MATCH (a:Concept {id: 'OCCASION_WEDDING_GUEST'}), (b:Concept {id: 'ITEM_SHORTS'})
MERGE (a)-[:AVOIDS {weight: 0.90}]->(b);
MATCH (a:Concept {id: 'OCCASION_WEDDING_GUEST'}), (b:Concept {id: 'ITEM_HOODIE'})
MERGE (a)-[:AVOIDS {weight: 0.95}]->(b);
MATCH (a:Concept {id: 'OCCASION_WEDDING_GUEST'}), (b:Concept {id: 'ITEM_SNEAKERS'})
MERGE (a)-[:AVOIDS {weight: 0.80}]->(b);

// ── PREF_MODEST ──────────────────────────────────────────────
MATCH (a:Concept {id: 'PREF_MODEST'}), (b:Concept {id: 'NECKLINE_DEEP_V'})
MERGE (a)-[:AVOIDS {weight: 0.95}]->(b);
MATCH (a:Concept {id: 'PREF_MODEST'}), (b:Concept {id: 'ITEM_MINI_SKIRT'})
MERGE (a)-[:AVOIDS {weight: 0.90}]->(b);
MATCH (a:Concept {id: 'PREF_MODEST'}), (b:Concept {id: 'ITEM_CROPPED_TOP'})
MERGE (a)-[:AVOIDS {weight: 0.70}]->(b);
MATCH (a:Concept {id: 'PREF_MODEST'}), (b:Concept {id: 'ITEM_BODYSUIT'})
MERGE (a)-[:AVOIDS {weight: 0.75}]->(b);
MATCH (a:Concept {id: 'PREF_MODEST'}), (b:Concept {id: 'ITEM_SHORTS'})
MERGE (a)-[:AVOIDS {weight: 0.80}]->(b);
MATCH (a:Concept {id: 'PREF_MODEST'}), (b:Concept {id: 'ITEM_MIDI_SKIRT'})
MERGE (a)-[:PREFERS {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'PREF_MODEST'}), (b:Concept {id: 'ITEM_MAXI_DRESS'})
MERGE (a)-[:PREFERS {weight: 0.90}]->(b);
MATCH (a:Concept {id: 'PREF_MODEST'}), (b:Concept {id: 'ITEM_TURTLENECK'})
MERGE (a)-[:PREFERS {weight: 0.85}]->(b);

// ── PREF_SEXY ────────────────────────────────────────────────
MATCH (a:Concept {id: 'PREF_SEXY'}), (b:Concept {id: 'ITEM_BODYSUIT'})
MERGE (a)-[:PREFERS {weight: 0.90}]->(b);
MATCH (a:Concept {id: 'PREF_SEXY'}), (b:Concept {id: 'ITEM_MINI_SKIRT'})
MERGE (a)-[:PREFERS {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'PREF_SEXY'}), (b:Concept {id: 'NECKLINE_DEEP_V'})
MERGE (a)-[:PREFERS {weight: 0.90}]->(b);
MATCH (a:Concept {id: 'PREF_SEXY'}), (b:Concept {id: 'FIT_FITTED'})
MERGE (a)-[:PREFERS {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'PREF_SEXY'}), (b:Concept {id: 'ITEM_HEELS'})
MERGE (a)-[:PREFERS {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'PREF_SEXY'}), (b:Concept {id: 'ITEM_WRAP_DRESS'})
MERGE (a)-[:PREFERS {weight: 0.80}]->(b);
MATCH (a:Concept {id: 'PREF_SEXY'}), (b:Concept {id: 'FIT_LOOSE'})
MERGE (a)-[:AVOIDS {weight: 0.80}]->(b);

// ── PREF_COMFORTABLE ─────────────────────────────────────────
MATCH (a:Concept {id: 'PREF_COMFORTABLE'}), (b:Concept {id: 'ITEM_SNEAKERS'})
MERGE (a)-[:PREFERS {weight: 0.90}]->(b);
MATCH (a:Concept {id: 'PREF_COMFORTABLE'}), (b:Concept {id: 'ITEM_JEANS'})
MERGE (a)-[:PREFERS {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'PREF_COMFORTABLE'}), (b:Concept {id: 'ITEM_HOODIE'})
MERGE (a)-[:PREFERS {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'PREF_COMFORTABLE'}), (b:Concept {id: 'FIT_LOOSE'})
MERGE (a)-[:PREFERS {weight: 0.85}]->(b);
MATCH (a:Concept {id: 'PREF_COMFORTABLE'}), (b:Concept {id: 'FABRIC_BREATHABLE'})
MERGE (a)-[:PREFERS {weight: 0.80}]->(b);
MATCH (a:Concept {id: 'PREF_COMFORTABLE'}), (b:Concept {id: 'ITEM_HEELS'})
MERGE (a)-[:AVOIDS {weight: 0.85}]->(b);
