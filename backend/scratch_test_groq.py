import os
import json
from dotenv import load_dotenv

load_dotenv()

from app.ai import CANONICAL_MEALS_SCHEMA, CANONICAL_RECIPE_SCHEMA

print("Checking CANONICAL_MEALS_SCHEMA keys & required:")
print("Root required:", CANONICAL_MEALS_SCHEMA.get("required"))
print("Root additionalProperties:", CANONICAL_MEALS_SCHEMA.get("additionalProperties"))

meals_props = CANONICAL_MEALS_SCHEMA["properties"]["meals"]["items"]["properties"]
meals_req = CANONICAL_MEALS_SCHEMA["properties"]["meals"]["items"]["required"]
print("Meals item props count:", len(meals_props))
print("Meals item req count:", len(meals_req))
print("Props match required:", set(meals_props.keys()) == set(meals_req))

comp_props = CANONICAL_MEALS_SCHEMA["properties"]["meals"]["items"]["properties"]["components"]["items"]["properties"]
comp_req = CANONICAL_MEALS_SCHEMA["properties"]["meals"]["items"]["properties"]["components"]["items"]["required"]
print("Comp item props match required:", set(comp_props.keys()) == set(comp_req))

print("\nChecking CANONICAL_RECIPE_SCHEMA keys & required:")
rec_props = CANONICAL_RECIPE_SCHEMA["properties"]
rec_req = CANONICAL_RECIPE_SCHEMA["required"]
print("Recipe root props match required:", set(rec_props.keys()) == set(rec_req))

rec_comp_props = CANONICAL_RECIPE_SCHEMA["properties"]["components"]["items"]["properties"]
rec_comp_req = CANONICAL_RECIPE_SCHEMA["properties"]["components"]["items"]["required"]
print("Recipe comp props match required:", set(rec_comp_props.keys()) == set(rec_comp_req))
