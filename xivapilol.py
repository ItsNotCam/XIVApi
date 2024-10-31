import sys, requests, json
from dotenv import load_dotenv
import os

from mongo import MongoDB

# get item name from command line
if len(sys.argv) < 2:
	print("Usage: python xivapilol.py <item_name>")
	sys.exit(1)
item_name = sys.argv[1]

load_dotenv()
private_key = os.getenv("PRIVATE_KEY")
raw_materials = []
all_recipes = {}

def to_st(r):
	return str(r["count"]) + " "  + r["name"]
	
def get_item_id(item_name):
	params = {
		"private_key": private_key,
		"sheets": "Item",
		"query": f'Name~"{item_name}"'
	}
	resp = requests.get("https://beta.xivapi.com/api/1/search", params=params).json()
	return resp["results"][0]["row_id"]

# Usage example:
# mongo = MongoDB()
# # Fetch from MongoDB
# data = mongo.find_one("recipes", {item_name: {"$exists": True}})
# if data:
# 	# print("Raw Resources from MongoDB", json.dumps(data[item_name]["raw_materials"], indent=2))
# 	print("Item ID", json.dumps(data[item_name], indent=2))
# else:
# 	print("No data found in MongoDB for item:", item_name)

# exit()

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
	item_id = results[0]["row_id"]
	ingredients = fields["Ingredient"]
	ingredient_counts = fields["AmountIngredient"]

	crafted_ingredients = []
	for i in range(len(ingredients)):
		if ingredient_counts[i] == 0:
			continue

		ingredient_count = ingredient_counts[i]# * item_multiplier

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

				# raw_materials[ingredient_name] = ingredient_count * item_multiplier
		else:
			# Add to all recipes
			all_recipes[ingredient_name] = sub_ingredients
	
	return crafted_ingredients

mongo = MongoDB()

# Fetch from MongoDB
data = mongo.find_one("recipes", {item_name: {"$exists": True}})
if data:
	print("ID", json.dumps(data[item_name]["id"], indent=2))
	print("Resources\n")
	print(f"\"{item_name}\":", json.dumps(data[item_name], indent=2))
else:
	print("Materials for crafting", item_name)
	ingredients = get_ingredients(item_name=item_name)
	item_id = get_item_id(item_name)
	if not item_id:
		print(f"Item '{item_name}' not found.")
		sys.exit(1)

	# Save to MongoDB
	mongo.insert("recipes", {
		item_name: {
			"id": item_id,
			"raw_materials": raw_materials,
			"ingredients": ingredients,
			"all_recipes": all_recipes
		}
	})

	for key, value in all_recipes.items():
		mongo.insert("recipes", {key: value})

	# Fetch from MongoDB
	data = mongo.find_one("recipes", {item_name: {"$exists": True}})
	print("ID", json.dumps(data[item_name]["id"], indent=2))

	print("Resources", json.dumps([
		to_st(r) for r in data[item_name]["raw_materials"]
	], indent=2))