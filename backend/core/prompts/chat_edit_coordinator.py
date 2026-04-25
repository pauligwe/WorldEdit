SYSTEM = """You merge a user's edit request into a building description.
Given the original prompt and the user's edit, produce a SINGLE NEW PROMPT that fully describes the desired final building.
Respond JSON only: {"prompt": "..."}."""

USER_TMPL = """Original prompt:
"{prompt}"

Edit request:
"{edit}"

Output: a new prompt JSON."""
