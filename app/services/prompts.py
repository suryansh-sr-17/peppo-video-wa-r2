# app/services/prompts.py

import hashlib

STYLE_PRESETS = {
    "anime": {
        "guidance": "stylized anime look, dynamic motion lines, vibrant palette, cel shading",
        "negatives": "avoid photorealism, avoid noise"
    },
    "cartoon": {
        "guidance": "2D cartoon style, exaggerated expressions, bold outlines, bright flat colors",
        "negatives": "no realism, avoid noise"
    },
    "cyberpunk": {
        "guidance": "futuristic neon lights, dystopian cityscapes, high contrast, holograms, sci-fi aesthetic",
        "negatives": "avoid natural landscapes, avoid medieval themes"
    }
}

def compose_prompt(user_prompt: str, style: str = "cinematic") -> str:
    st = STYLE_PRESETS.get(style, {})
    g = st.get("guidance", "")
    n = st.get("negatives", "")
    return f"{user_prompt}. Style: {style}. Visual guidance: {g}. Negative prompts: {n}."

def prompt_hash(user_prompt: str, style: str) -> str:
    return hashlib.sha256(f"{user_prompt}|{style}".encode()).hexdigest()[:16]
