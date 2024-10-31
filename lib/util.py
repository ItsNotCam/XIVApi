import os, requests, json
from dotenv import load_dotenv

load_dotenv()
private_key = os.getenv("PRIVATE_KEY")

def get_item_id(item_name):
	params = {
		"private_key": private_key,
		"sheets": "Item",
		"query": f'Name~"{item_name}"'
	}
	resp = requests.get("https://beta.xivapi.com/api/1/search", params=params).json()
	return resp["results"][0]["row_id"]


def to_st(r):
	return str(r["count"]) + " "  + r["name"]
	
def build_params(item_id=None, item_name=None):
	return {
		"private_key": private_key,
		"sheets": "Recipe",
		"query": f"ItemResult={item_id}" if item_id else f"ItemResult.Name~\"{item_name}\"",
		"fields": "Ingredient,AmountIngredient,Icon"
	}

def print_item_data(item_data, item_name):
	print("ID", json.dumps(item_data["id"], indent=2))
	print("Resources\n")
	print(f"\"{item_name}\":", json.dumps(item_data, indent=2))