import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")

class MongoDB:
	def __init__(self):
		self.client = MongoClient(MONGO_URI)
		self.db = self.client[MONGO_DB_NAME]

	def insert(self, collection_name, data):
		self.db[collection_name].insert_one(data)
	
	def insert_many(self, collection_name, data):
		self.db[collection_name].insert_many(data)

	def get_collection(self, collection_name):
		return self.db[collection_name].find_one()
	
	def find_one(self, collection_name, query):
		return self.db[collection_name].find_one(query)

