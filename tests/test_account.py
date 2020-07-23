import os
import unittest

from app import app, db
from app.models import Player, Game, Player_Info

TEST_DB = 'test.db'
TEST_NAME = "test"
TEST_GAME_ID = 1

class AccountTests(unittest.TestCase):
    # Setup: executed before each test
    def setUp(self):
        app.config['TESTING'] = True
        app.config['DEBUG'] = False
        #app.config['LOGIN_DISABLED'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
            os.path.join(app.config['BASEDIR'], TEST_DB)
        self.app = app.test_client()
        db.drop_all()
        db.create_all()

    # Teardown: executed after each test
    def tearDown(self):
        db.session.remove()
        db.drop_all()

    # TESTS
    # def test_login_new_user(self):
    #     # user does't exist
    #     self.login(name=TEST_NAME)
    
    # def test_login_user_exists(self):
    #     # user already exists
    #     p = Player(name=TEST_NAME)
    #     db.session.add(p)
    #     db.session.commit()

    #     self.login(name=TEST_NAME)

    # def test_login_name_none(self):
    #     # cannot have name of 'None'
    #     self.app.post('/', data=dict(name='None'))
    #     p = self.get_player('None')
    #     self.assertEqual(p, None)

    # PROB!
    ## def test_show_player_games(self):
    ##     # show games for this user (both finished and unfinished)
    ##     resp = self.app.get('/player', follow_redirects=True)
    ##     self.assertEqual(resp.status_code, 200)
    ##     self.assertEqual(resp.player.name)

    # def test_start_game(self):
    #     self.login(name=TEST_NAME)
    #     resp = self.app.get('/start_game', data=dict(), follow_redirects=True)
    #     self.assertEqual(resp.status_code, 200)
    #     g = Game.query.filter_by(id=TEST_GAME_ID).first()
    #     self.assertNotEqual(g, None)
    #     p = self.get_player(TEST_NAME)
    #     self.assertEqual(p.cur_game, TEST_GAME_ID)
    #     pi = self.get_player_info(g.id, p.id)
    #     self.assertNotEqual(pi, None)

    # PROB!
    # def test_join_game(self):
    #     self.login(name=TEST_NAME)
    #     self.create_game()
    #     resp = self.app.get('/join_game', data=dict(game_id=TEST_GAME_ID), follow_redirects=True)
    #     self.assertEqual(resp.status_code, 200)
    #     p = self.get_player(name=TEST_NAME)
    #     self.assertEqual(p.cur_game, TEST_GAME_ID)
    #     pi = self.get_player_info(TEST_GAME_ID, p.id)
    #     self.assertNotEqual(pi, None)

    def login(self, name):
        resp = self.app.post('/', data=dict(name=name), follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        p = self.get_player(name=name)
        self.assertEqual(p.name, name)

    def get_player(self, name):
        p = Player.query.filter_by(name=name).first()
        self.assertNotEqual(p, None)
        return p

    def get_player_info(self, gid, pid):
        pi = Player_Info.query.filter_by(game_id=gid, player_id=pid).first()
        self.assertNotEqual(pi, None)
        return pi

    def get_game(self, gid):
        g = Game.query.filter_by(id=gid).first()
        self.assertNotEqual(g, None)
        return g

    def create_game(self):
        g = Game()
        db.session.add(g)
        db.session.commit()
        self.get_game(g.id)




    
#############################333
# u = User(name='test')
        # db.session.add(u1)
        # self.assertEqual(u.avatar(128), ('https://www.gravatar.com/avatar/'
        #                                  'd4c74594d841139328695756648b6bd6'
                                        #  '?d=identicon&s=128'))


        # resp = self.app.get('/', follow_redirects=True)
        # self.assertEqual(resp.status_code, 200)
        # resp = self.app.get('/home', follow_redirects=True)
        # self.assertEqual(resp.status_code, 200)
    
# self.app.post('/path-to-request', data=dict(var1='data1', var2='data2', ...))
# self.app.get('/path-to-request', query_string=dict(arg1='data1', arg2='data2', ...))

if __name__ == "__main__":
    unittest.main()
