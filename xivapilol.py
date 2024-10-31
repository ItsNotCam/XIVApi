import sys, requests, json
from dotenv import load_dotenv
import os



load_dotenv()
private_key = os.getenv("PRIVATE_KEY")
raw_materials = {}
all_recipes = {}

stored_recipes = {}

if not os.path.exists("files/recipes.json"):
	os.makedirs("files", exist_ok=True)

with open("files/recipes.json", "r") as ofile:
	stored_recipes = json.load(ofile)

def build_params(item_id=None, item_name=None):
	return {
		"private_key": private_key,
		"sheets": "Recipe",
		"query": f"ItemResult={item_id}" if item_id else f"ItemResult.Name~\"{item_name}\"",
		"fields": "Ingredient,AmountIngredient,Icon"
	}

def get_ingredients(item_name=None, item_id=None, depth=0, item_multiplier=1):
	params = build_params(item_id, item_name)

	resp = requests.get("https://beta.xivapi.com/api/1/search", params=params).json()
	results = resp["results"]
	if len(results) == 0:
		return None

	fields = results[0]["fields"]
	ingredients = fields["Ingredient"]
	ingredient_counts = fields["AmountIngredient"]

	crafted_ingredients = []
	for i in range(len(ingredients)):
		if ingredient_counts[i] == 0:
			continue

		ingredient_count = ingredient_counts[i]# * item_multiplier

		print("  " * depth, ingredient_count, ingredients[i]["fields"]["Name"])
		sub_ingredients = get_ingredients(
			item_id=ingredients[i]["row_id"], 
			depth=depth+1, 
			item_multiplier=ingredient_count
		)
		
		icon = ingredients[i]["fields"]["Icon"]
		icon_route = icon["path"]
		ingredient_name = ingredients[i]["fields"]["Name"]

		crafted_ingredients.append({
			"count": ingredient_count,
			"ingredient": ingredient_name,
			"sub_ingredients": sub_ingredients,
			"icon_url": f"https://beta.xivapi.com/api/1/asset?path={icon_route}&format=png"
		})

		if sub_ingredients is None:
			if ingredient_name in raw_materials:
				raw_materials[ingredient_name] += ingredient_count * item_multiplier
			else:
				raw_materials[ingredient_name] = ingredient_count * item_multiplier
		else:
			# Add to all recipes
			all_recipes[ingredient_name] = sub_ingredients
	
	return crafted_ingredients

if len(sys.argv) < 2:
	print("Usage: python xivapilol.py <item_name>")
	sys.exit(1)

item_name = sys.argv[1]

print("Materials for crafting", item_name)
ingredients = []
ingredients = get_ingredients(item_name=item_name)

existing_data = {}
with open("files/recipes.json", "r") as ofile:
	try:
		existing_data = json.load(ofile)
	except json.JSONDecodeError:
		existing_data = {}

	existing_data.update({
		item_name: {
			"raw_materials": raw_materials,
			"ingredients": ingredients
		},
		**all_recipes
	})

	with open("files/recipes.json", "w") as ofile:
		json.dump(existing_data, ofile, indent=2)

print("Raw Resources", json.dumps(raw_materials, indent=2))
print("Raw Recipes", json.dumps(all_recipes, indent=2))