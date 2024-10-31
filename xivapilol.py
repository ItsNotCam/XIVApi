import sys, requests
from lib.mongo import MongoDB
from lib.util import get_item_id, print_item_data, build_params

# get item name from command line
if len(sys.argv) < 2:
	print("Usage: python xivapilol.py <item_name>")
	sys.exit(1)

ITEM_NAME = sys.argv[1]

raw_materials = []
all_recipes = {}

def get_ingredients(item_name=None, item_id=None, depth=0, item_multiplier=1):
	params = build_params(item_id, item_name)

	resp = requests.get("https://beta.xivapi.com/api/1/search", params=params).json()
	results = resp["results"]
	if len(results) == 0:
		return None

	fields = results[0]["fields"]
	item_id = results[0]["row_id"]
	ingredients = fields["Ingredient"]
	ingredient_counts = fields["AmountIngredient"]

	crafted_ingredients = []
	for i in range(len(ingredients)):
		if ingredient_counts[i] == 0:
			continue

		ingredient_count = ingredient_counts[i]

		if depth == 0:
			print(ingredient_count, ingredients[i]["fields"]["Name"])
		else:
			print("  " * (depth-1), ingredient_count, ingredients[i]["fields"]["Name"])

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
			"id": ingredients[i]["row_id"],
			"ingredient": ingredient_name,
			"sub_ingredients": sub_ingredients,
			"icon_url": f"https://beta.xivapi.com/api/1/asset?path={icon_route}&format=png"
		})

		if sub_ingredients is None:
			if ingredient_name in raw_materials:
				for material in raw_materials:
					if material["name"] == ingredient_name:
						material["count"] += ingredient_count * item_multiplier
						break
			else:
				raw_materials.append({
					"name": ingredient_name,
					"id": item_id,
					"count": ingredient_count * item_multiplier,
					"icon_url": f"https://beta.xivapi.com/api/1/asset?path={icon_route}&format=png"
				})
		else:
			all_recipes[ingredient_name] = sub_ingredients
	
	return crafted_ingredients


# Fetch from MongoDB
mongo = MongoDB()
data = mongo.find_one("recipes", {ITEM_NAME: {"$exists": True}})

# Fetch from XIVAPI if not found in MongoDB
if not data:
	print("Materials for crafting", ITEM_NAME)
	ingredients = get_ingredients(item_name=ITEM_NAME)
	item_id = get_item_id(ITEM_NAME)
	if not item_id:
		print(f"Item '{ITEM_NAME}' not found.")
		sys.exit(1)

	# Save to MongoDB
	mongo.insert("recipes", {
		ITEM_NAME: {
			"id": item_id,
			"raw_materials": raw_materials,
			"ingredients": ingredients,
			"all_recipes": all_recipes
		}
	})

	for key, value in all_recipes.items():
		mongo.insert("recipes", {key: value})

	# Fetch from MongoDB
	data = mongo.find_one("recipes", {ITEM_NAME: {"$exists": True}})

print_item_data(data[ITEM_NAME], ITEM_NAME)