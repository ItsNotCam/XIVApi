import unittest, os
from unittest.mock import patch, MagicMock
from ..mongo import MongoDB

from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")

class TestMongoDB(unittest.TestCase):

	@patch('mongo.MongoClient')
	def setUp(self, MockMongoClient):
		self.mock_client = MockMongoClient()
		self.mock_db = self.mock_client[MONGO_DB_NAME]
		self.mongo = MongoDB()

	def test_insert(self):
		collection_name = "recipes"
		data = {"name": "oroshigane ingot"}
		self.mongo.insert(collection_name, data)
		self.mock_db[collection_name].insert_one.assert_called_with(data)

	def test_insert_many(self):
		collection_name = "recipes"
		data = [{"name": "oroshigane ingot"}, {"name": "another recipe"}]
		self.mongo.insert_many(collection_name, data)
		self.mock_db[collection_name].insert_many.assert_called_with(data)

	def test_get_collection(self):
		collection_name = "recipes"
		expected_data = {"name": "oroshigane ingot"}
		self.mock_db[collection_name].find_one.return_value = expected_data
		result = self.mongo.get_collection(collection_name)
		self.assertEqual(result, expected_data)

	def test_find_one(self):
		collection_name = "recipes"
		query = {"name": "oroshigane ingot"}
		expected_data = {"name": "oroshigane ingot"}
		self.mock_db[collection_name].find_one.return_value = expected_data
		result = self.mongo.find_one(collection_name, query)
		self.assertEqual(result, expected_data)

if __name__ == '__main__':
	unittest.main()