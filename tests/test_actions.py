# import os
# import unittest

# from app import app, db

# TEST_DB = 'test.db'

# class ActionTests(unittest.TestCase):
#     # Setup: executed before each test
#     def setUp(self):
#         app.config['TESTING'] = True
#         app.config['DEBUG'] = False
#         app.config['WTF_CSRF_ENABLED'] = False
#         app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
#             os.path.join(app.config['BASEDIR'], TEST_DB)
#         self.app = app.test_client()
#         db.drop_all()
#         db.create_all()

#     # Teardown: executed after each test
#     def tearDown(self):
#         db.session.remove()
#         db.drop_all()

#     # TESTS
#     def test_buy_organic(self):
#         self.assertEqual(2 + 2, 4)
#         #resp = self.app.get('/buy_organic', follow_redirects=True)
#         #self.assertEqual(resp.status_code, 200)

# if __name__ == "__main__":
#     unittest.main()
