from datetime import datetime
from app import db, login
from flask_login import UserMixin

@login.user_loader
def load_user(id):  
    return Player.query.get(int(id))

class Player(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), index=True, unique=True)
    cur_game = db.Column(db.Integer, db.ForeignKey('game.id'), default=-1)
    games = db.relationship('Player_Info', backref='player', lazy='dynamic')

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_started = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    finished = db.Column(db.Boolean, index=True, default=False)
    date_finished = db.Column(db.DateTime, index=True)
    roll_order = db.Column(db.Boolean, default=False)
    ready_to_start = db.Column(db.Boolean, default=False)
    cur_turn = db.Column(db.Integer, default=-1)
    num_players = db.Column(db.Integer, default=0)
    player_infos = db.relationship('Player_Info', backref='game', lazy='dynamic')

class Player_Info(db.Model):
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), primary_key=True)
    active = db.Column(db.Boolean, default=True, index=True)
    ready = db.Column(db.Boolean, default=False, index=True)
    turn_num = db.Column(db.Integer, index=True, default=-1)
    last_card = db.Column(db.String(140), default="???")
    picked_card = db.Column(db.Boolean, default=False)
    done_action = db.Column(db.Boolean, default=False)
    end_of_year = db.Column(db.Boolean, default=False)
    jobs_page_type = db.Column(db.String(20), default="all")
    notes1 = db.Column(db.String(255), default="To-Do:")
    notes2 = db.Column(db.String(255), default="To-Do:")
    notes3 = db.Column(db.String(255), default="To-Do:")
    notes4 = db.Column(db.String(255), default="To-Do:")
    age = db.Column(db.Integer, default=18)
    points = db.Column(db.Integer, default=1000)
    money = db.Column(db.Integer, default=35000)
    path = db.Column(db.String(20), default="college")
    job = db.Column(db.String(64), default="None", index=True)
    num_pay_raises = db.Column(db.Integer, default=0)
    cur_time_til_raise = db.Column(db.Integer, default=0)
    current_salary = db.Column(db.Integer, default=0)
    age_grad = db.Column(db.Integer, default=0)
    grad_school = db.Column(db.Boolean, default=False)
    graduating = db.Column(db.Boolean, default=False)
    car = db.Column(db.String(64), default="None")
    old_car = db.Column(db.String(64), default="None")
    house = db.Column(db.String(64), default="None")
    old_house = db.Column(db.String(64), default="None")
    married = db.Column(db.Boolean, default=False)
    num_kids = db.Column(db.Integer, default=0)
    oldest_child_age = db.Column(db.Integer, default=0)
    have_auto_ins = db.Column(db.Boolean, default=False)
    last_auto_ins = db.Column(db.Integer, default=0)
    have_health_ins = db.Column(db.Boolean, default=True)
    have_home_ins = db.Column(db.Boolean, default=False)
    last_home_ins = db.Column(db.Integer, default=0)
    have_pet = db.Column(db.Boolean, default=False)
    college_loans = db.Column(db.Integer, default=0)
    loans = db.Column(db.Integer, default=0)
    buying_organic = db.Column(db.Boolean, default=False)
    was_janitor = db.Column(db.Boolean, default=False)
    med_prob = db.Column(db.Boolean, default=False)
    depressed = db.Column(db.Boolean, default=False)
    yrs_military = db.Column(db.Integer, default=0) 
    yrs_til_buy_organic = db.Column(db.Integer, default=0)
    bought_appliances = db.Column(db.Boolean, default=False)
    yrs_til_upgrade_appliances = db.Column(db.Integer, default=0)
    yrs_til_change_car = db.Column(db.Integer, default=0)
    yrs_til_change_house = db.Column(db.Integer, default=0)
    yrs_til_buy_clothes = db.Column(db.Integer, default=0)
    yrs_til_travel = db.Column(db.Integer, default=0)
    yrs_til_change_married = db.Column(db.Integer, default=0)
    yrs_til_have_kid = db.Column(db.Integer, default=0)
    yrs_til_have_grandkid = db.Column(db.Integer, default=0)
    yrs_til_switch_jobs = db.Column(db.Integer, default=0)
    yrs_til_rich_action = db.Column(db.Integer, default=0)
    have_pool = db.Column(db.Boolean, default=False)
    major_donor = db.Column(db.Boolean, default=False)
    yrs_til_peace_corps = db.Column(db.Integer, default=0)
    yrs_til_mission_trip = db.Column(db.Integer, default=0)
    yrs_til_invest = db.Column(db.Integer, default=0)
    upgrade_over_40 = db.Column(db.Integer, default=0)
    num_yrs_teacher = db.Column(db.Integer, default=0)
    mil_to_college = db.Column(db.Boolean, default=False)
    mil_start_college = db.Column(db.Integer, default=0)
    need_loan = db.Column(db.Boolean, default=False)
    num_times_travel = db.Column(db.Integer, default=0)
    num_times_buy_organic = db.Column(db.Integer, default=0)
    num_times_invest = db.Column(db.Integer, default=0)
    num_times_buy_clothes = db.Column(db.Integer, default=0)
    num_times_peace_corps = db.Column(db.Integer, default=0)
    num_times_season_tickets = db.Column(db.Integer, default=0)
    num_times_backpacking = db.Column(db.Integer, default=0)
    num_times_mission_trip = db.Column(db.Integer, default=0)
    total_taxes = db.Column(db.Integer, default=0)
    total_insurance = db.Column(db.Integer, default=0)
    total_shopping = db.Column(db.Integer, default=0)
    total_car_maintenance = db.Column(db.Integer, default=0)
    total_maid = db.Column(db.Integer, default=0)
    total_utilities = db.Column(db.Integer, default=0)
    total_dental = db.Column(db.Integer, default=0)
    total_eat_ent = db.Column(db.Integer, default=0)
    total_gas = db.Column(db.Integer, default=0)
    total_tax_prep = db.Column(db.Integer, default=0)
    total_rent = db.Column(db.Integer, default=0)
    total_transit = db.Column(db.Integer, default=0)
    total_organic = db.Column(db.Integer, default=0)
    total_pet = db.Column(db.Integer, default=0)
    total_pool = db.Column(db.Integer, default=0)
    total_depression = db.Column(db.Integer, default=0)
    total_loan = db.Column(db.Integer, default=0)
    num_yrs_college = db.Column(db.Integer, default=0)

class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    regular = db.Column(db.Boolean, index=True)
    text = db.Column(db.String(140), index=True)
    affects_points = db.Column(db.Boolean) 
    amount = db.Column(db.Integer)
    
class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(20), index=True)
    picked = db.Column(db.Boolean, index=True, default=False)
    title = db.Column(db.String(32), index=True, unique=True)
    base_salary = db.Column(db.Integer)
    default_time_til_raise = db.Column(db.Integer)

class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(20), index=True)
    name = db.Column(db.String(32), unique=True, index=True)
    cost = db.Column(db.Integer)
    insurance = db.Column(db.Integer)
    gas = db.Column(db.Integer)
    sell_price = db.Column(db.Integer)

class House(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(20), index=True)
    name = db.Column(db.String(32), unique=True, index=True)
    cost = db.Column(db.Integer)
    minus_points = db.Column(db.Integer)
    insurance = db.Column(db.Integer)
    maid = db.Column(db.Integer)
    sell_price = db.Column(db.Integer)















    