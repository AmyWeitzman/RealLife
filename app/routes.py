from flask import render_template, flash, redirect, url_for, request
from app import app, db#, socketio
from app.forms import LoginForm
from flask_login import current_user, login_required, login_user
from app.models import Player, Player_Info, Game, Card, Job, Vehicle, House
from random import randint, sample, shuffle
import math
from datetime import datetime
import json

wait_yrs = 3

@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
def home():
    #if current_user.is_authenticated:
    #    return redirect(url_for('player', name=current_user.name))
    form = LoginForm()
    if form.validate_on_submit():
        if(form.name.data == "None"):
            flash("Name cannot be 'None'.", "error")
            return render_template('homepage.html', page_name='Homepage', form=form)   # name cannot be None
        player = Player.query.filter_by(name=form.name.data).first()  # look for player in database
        if player is None:                        # player does not exist
            player = Player(name=form.name.data)  # create new player
            db.session.add(player)                # add player to database
            db.session.commit()
        login_user(player)                       
        return redirect(url_for('player'))
    return render_template('homepage.html', page_name='Homepage', form=form)   # invalid entry on homepage for sign-in

@app.route('/player')
@login_required
def player():
    player = get_cur_player()
    games = Game.query.join(Player_Info, (Player_Info.game_id == Game.id)).filter_by(player_id=player.id, active=True)  # find all of this player's games
    num_incomplete = len([g for g in list(games) if g.finished==False])  # split games by complete and in-progress
    num_complete = len([g for g in list(games) if g.finished==True])
    return render_template('player_account.html', player=player, games=games, num_incomplete=num_incomplete, num_complete=num_complete)

@app.route('/start_game')
@login_required
def start_game():
    game = Game()  # create new game (default vals)
    db.session.add(game)
    db.session.commit()
    player = get_cur_player()
    player.cur_game = game.id
    player_info = Player_Info(game_id=game.id, player_id=player.id)  # create a player info for this player in this game
    db.session.add(player_info)
    db.session.commit()
    return redirect(url_for('player_info'))

@app.route('/join_game')
@login_required
def join_game():
    game_id = request.args.get('game_id', type=int)  # get the game id the player specified
    if((game_id == None) or (Game.query.filter_by(id=game_id).first() == None)):
        flash("Invalid Game ID")
        return redirect(url_for('player'))
    player = get_cur_player()
    player_info = Player_Info.query.filter_by(game_id=game_id, player_id=player.id).first()
    if(player_info):   # player was once in this game, but removed it
        if(not player_info.active):  # reactivate the player_info
            player_info.active = True
            db.session.commit()
        return redirect(url_for('player_info'))
    player.cur_game = game_id
    player_info = Player_Info(game_id=game_id, player_id=player.id)  #  create new player info
    db.session.add(player_info)
    db.session.commit()
    return redirect(url_for('player_info'))

@app.route('/resume_game/<game_id>')
@login_required
def resume_game(game_id):
    player = get_cur_player()
    player.cur_game = game_id
    db.session.commit()
    return redirect(url_for('player_info'))

@app.route('/remove_game/<game_id>')
@login_required
def remove_game(game_id):
    player = get_cur_player()
    player_info = Player_Info.query.filter_by(game_id=game_id, player_id=player.id).first()
    player_info.active = False  # keep the player info in the database in case the user wants to re-join
    db.session.commit()
    return redirect(url_for('player'))

@app.route('/delete_game/<game_id>')
@login_required
def delete_game(game_id):
    game = get_game(game_id)
    player_infos = get_all_player_infos(game_id)
    for player_info in player_infos:
        db.session.delete(player_info)  # delete the game entirely, remove all player infos (maybe error = bad game)
    db.session.delete(game)
    db.session.commit()
    return redirect(url_for('player'))

@app.route('/view_game/<game_id>')
@login_required
def view_game(game_id):
    return redirect(url_for('player_info'))

@app.route('/player_info')
@login_required
def player_info():
    player, player_info = get_cur_player_info()
    game = get_game(player.cur_game)
    if(player_info.job.lower() != "none"):
        job = get_job(player_info.job)
        taxes = get_taxes(player_info.current_salary, job.title, player_info.married)
        benefits = check_eligibility(player_info.path, player_info.yrs_military, player_info.age_grad, player_info.age)
    else:
        job = "None"
        taxes = 0
        benefits = False
    num_people = get_num_people(player_info.married, player_info.num_kids)
    college_loan_int = get_college_loan_int(player_info.college_loans, player_info.age, player_info.age_grad)
    loans_int = get_loan_int(player_info.loans)
    announcements = get_announcements(player_info)

    if((player_info.mil_to_college) and (player_info.mil_start_college == 0)):
        flash("You have enrolled. You may get a job in college if desired.")
    return render_template('player_info.html', page_name='Player Info', 
            game=game, name=current_user.name, player_info=player_info, job=job,
            taxes=taxes, benefits=benefits, num_people=num_people, college_loan_int=college_loan_int,
            loans_int=loans_int, announcements=announcements)

@app.route('/set_roll_order')
@login_required
def set_roll_order():
    player = get_cur_player()
    game = get_game(player.cur_game)
    player_infos = get_all_player_infos(player.cur_game)
    players = [p.player_id for p in player_infos]
    shuffle(players)
   
    # set turn number for all players
    for num, pid in enumerate(players, start=1):
        player_infos.filter_by(player_id=pid).first().turn_num = num
    game.roll_order = True
    game.num_players = len(players)
    game.cur_turn = 1

    db.session.commit()
    return redirect(url_for('player_info'))

@app.route('/set_ready')
@login_required
def set_ready():
    player, player_info = get_cur_player_info()
    player_info.ready = True

    game = get_game(player.cur_game)
    switch_turn(game)

    db.session.commit()
    return redirect(url_for('player_info'))

@app.route('/cards')
@login_required
def cards():
    return render_template('cards.html', page_name='Cards')

@app.route('/pick_card/<game_id>')
@login_required
def pick_card(game_id):
    player = get_cur_player()
    player_info = Player_Info.query.filter_by(game_id=game_id, player_id=player.id).first()
    card_type_regular = False if (player_info.path == "college") else True  # only college picks college cards
    cards = list(Card.query.filter_by(regular=card_type_regular))  # get all cards from the appropriate category
    card = cards[randint(0, len(cards) - 1)]  # pick a random card
    while(not is_valid_card(player_info, card)):  # check if card is valid (no car cards if no have car, etc...)
        card = cards[randint(0, len(cards) - 1)]  # pick a new random card
    player_info.last_card = card.text   # keep track of card text to show on card when leave and return to page
    if(card.text in ["Family issue", "Mental illness"]):
        if(not player_info.have_health_ins):
            player_info.money -= 5000 # pay $5000 to psychologist
            flash("Not covered by health insurance", "info")
        else:
            flash("Covered by health insurance", "info")
        job = get_job("Psychologist")
        if(job.picked):  # someone is the psychologist, gets paid $5000
            psychologist = get_player_with_job(game_id, job)
            psychologist.money += 5000
    elif(card.text == "Car accident"):
        # since can't get insurance for car bought at beginning of game, no accidents
        if((player_info.age > 18) and (player_info.car != "None") and (not player_info.path == "college")):  # must have car/not in college for car accident
            num_people = get_num_people(player_info.is_married, player_info.num_kids)
            if(not player_info.have_auto_ins):
                player_info.money -= 50000  # pay $50,000
            else:
                flash("Covered by auto insurance.", "info")
            if(not player_info.have_health_ins):
                player_info.money -= (50 * num_people)
            else:
                flash("Chiropractor fees covered by health insurance.", "info")
            job = get_job("Mechanic")
            if(job.picked):  # someone is the mechanic, gets paid $5000
                mechanic = get_player_with_job(game_id, job)
                mechanic.money += 5000
            job = get_job("Chiropractor")
            if(job.picked):  # someone is the chiropractor, gets paid $50/person
                chiro = get_player_with_job(game_id, job)
                chiro.money += (50 * num_people)
    elif(card.text == "Earthquake damage"):
        if(player_info.house != "None"):
            if(not player_info.have_home_ins):
                player_info.money -= 50000  # pay $50,000
            job = get_job("Carpenter")
            if(job.picked):  # someone is the carpenter, gets paid $5000
                carpenter = get_player_with_job(game_id, job)
                carpenter.money += 5000  
    elif(card.text == "Fire damage"):
        if(player_info.house != "None"):
            if(not player_info.have_home_ins):
                player_info.money -= 50000  # pay $50,000
            job = get_job("Firefighter")
            if(job.picked):  # someone is the firefighter, gets paid $5000
                firefighter = get_player_with_job(game_id, job)
                firefighter.money += 5000  
    elif(card.text == "Pest problem"):
        if(player_info.house != "None"):
            player_info.money -= 5000  # pay $5000, no insurance coverage
            job = get_job("Exterminator")
            if(job.picked):  # someone is the exterminator, gets paid $5000
                exterminator = get_player_with_job(game_id, job)
                exterminator.money += 5000 
    elif(card.text == "Tech problems"):
        player_info.money -= 100  # pay $100
        job = get_job("Software Developer")
        if(job.picked):  # someone is the software developer, gets paid $100
            developer = get_player_with_job(game_id, job)
            developer.money += 100 
    elif(card.text == "Lawsuit"):
        roll = simulateRoll()
        flash("You rolled a " + str(roll), "info")
        payment = (500 * roll)  # pay $500 * roll
        player_info.money -= payment
        job = get_job("Lawyer")
        if(job.picked):  # someone is the lawyer, gets paid 50% of payment
            lawyer = get_player_with_job(game_id, job)
            lawyer.money += (0.5 * payment)
    elif(card.text == "Speeding"):
        if(player_info.car != "None"):  # must have car for speeding
            car = get_car(player_info.car)
            if(car.category != "no-family"):  # must have at least small family car for speeding
                roll = simulateRoll()
                if((roll % 2) == 0):  # even: car accident
                    flash("You were in a CAR ACCIDENT.", "info")
                    num_people = get_num_people(player_info.is_married, player_info.num_kids)
                    if(not player_info.have_auto_ins):
                        player_info.money -= 50000  # pay $50,000
                    else:
                        flash("Covered by auto insurance.", "info")
                    if(not player_info.have_health_ins):
                        player_info.money -= (50 * num_people)
                    else:
                        flash("Chiropractor fees covered by health insurance.", "info")
                    job = get_job("Mechanic")
                    if(job.picked):  # someone is the mechanic, gets paid $5000
                        mechanic = get_player_with_job(game_id, job)
                        mechanic.money += 5000
                    job = get_job("Chiropractor")
                    if(job.picked):  # someone is the chiropractor, gets paid $50/person
                        chiro = get_player_with_job(game_id, job)
                        chiro.money += (50 * num_people)
                else:
                    flash("Ineligible vehicle for speeding","info")
        else:
            flash("You were NOT in a car accident", "info")
    elif(card.text[:5] == "Baker"):  # baker cards
        player_infos = get_all_player_infos(game_id)
        for player_info in player_infos:
            player_info.money -= 10  # everyone pay $10
        job = get_job("Baker")
        if(job.picked):  # someone is the baker, gets paid $10,000
            baker = get_player_with_job(game_id, job)
            baker.money += 10010  # gets paid $10,000 + $10 already taken out above 
    elif(card.text[:6] == "Animal"):  # animal trainer cards
        player_infos = get_all_player_infos(game_id)
        for player_info in player_infos:
            player_info.money -= 10  # everyone pay $10
        job = get_job("Animal Trainer")
        if(job.picked):  # someone is the animal trainer, gets paid $10,000
            trainer = get_player_with_job(game_id, job)
            trainer.money += 10010  # gets paid $10,000 + $10 already taken out above 
    elif(card.text[:8] == "Reporter"):  # reporter cards
        player_infos = get_all_player_infos(game_id)
        for player_info in player_infos:
            player_info.money -= 10  # everyone pay $10
        job = get_job("Reporter")
        if(job.picked):  # someone is the reporter, gets paid $10,000
            reporter = get_player_with_job(game_id, job)
            reporter.money += 10010  # gets paid $10,000 + $10 already taken out above 
    elif(card.text[:6] == "Author"):  # author cards
        player_infos = get_all_player_infos(game_id)
        for player_info in player_infos:
            player_info.money -= 10  # everyone pay $10
        job = get_job("Author")
        if(job.picked):  # someone is the author, gets paid $10,000
            author = get_player_with_job(game_id, job)
            author.money += 10010  # gets paid $10,000 + $10 already taken out above 
    elif(card.text[:6] == "Singer"):  # singer card
        player_infos = get_all_player_infos(game_id)
        for player_info in player_infos:
            player_info.money -= 10  # everyone pay $10
        job = get_job("Singer")
        if(job.picked):  # someone is the singer, gets paid $10,000
            singer = get_player_with_job(game_id, job)
            singer.money += 10010  # gets paid $10,000 + $10 already taken out above 
    elif(card.text[:5] == "Actor"):  # actor card
        player_infos = get_all_player_infos(game_id)
        for player_info in player_infos:
            player_info.money -= 10  # everyone pay $10
        job = get_job("Actor")
        if(job.picked):  # someone is the actor, gets paid $10,000
            actor = get_player_with_job(game_id, job)
            actor.money += 10010  # gets paid $10,000 + $10 already taken out above 
    elif(card.text[:8] == "Engineer"):  # engineer card
        player_infos = get_all_player_infos(game_id)
        for player_info in player_infos:
            player_info.money -= 10  # everyone pay $10
        job = get_job("Engineer")
        if(job.picked):  # someone is the engineer, gets paid $10,000
            engineer = get_player_with_job(game_id, job)
            engineer.money += 10010  # gets paid $10,000 + $10 already taken out above 
    elif(card.text[:8] == "Athlete"):  # athlete card
        player_infos = get_all_player_infos(game_id)
        for player_info in player_infos:
            player_info.money -= 10  # everyone pay $10
        job = get_job("Athlete")
        if(job.picked):  # someone is the athlete, gets paid $50,000
            athlete = get_player_with_job(game_id, job)
            athlete.money += 50010  # gets paid $50,000 + $10 already taken out above 
    elif(card.text == "Lose job"):
        if(player_info.path == "military"):  # demoted
            job = get_job("Military")
            if(player_info.current_salary == player_info.base_salary):
                flash("You have been kicked out of the military!", "info")
                db.session.commit()
                return redirect(url_for('jobs')) # kicked out of military
            else:  # demoted
                flash("You have been demoted!", "info")
                player_info.num_pay_raises -= 1
                player_info.current_salary /= 2  # b/c salary doubles each raise, previous salary was half of current
                player_info.cur_time_til_raise = job.default_time_til_raise
        else:
            if(player_info.job == "Teacher"):
                player_info.num_yrs_teacher = 0  # no longer teacher, make sure not get promoted to principal
            db.session.commit()
            return redirect(url_for('jobs'))
    elif(card.text == "Birthday party"): 
        player_infos = get_all_player_infos(game_id)
        num_players = len(list(player_infos))
        for player_info in player_infos:
            player_info.money -= 20  # everyone pay $20
        job = get_job("Hair Stylist")
        if(job.picked):  # someone is the hair stylist, gets paid $20/player
            stylist = get_player_with_job(game_id, job)
            stylist.money += (20 * num_players)  # gets paid $20 per other player + $20 already taken out above 
    elif(card.text in ["Graduation party", "Anniversary party"]): 
        player_infos = get_all_player_infos(game_id)
        num_players = len(list(player_infos))
        for player_info in player_infos:
            player_info.money -= 100  # everyone pay $100
        job = get_job("Hair Stylist")
        if(job.picked):  # someone is the hair stylist, gets paid $100/player
            stylist = get_player_with_job(game_id, job)
            stylist.money += (100 * num_players)  # gets paid $100 per other player + $100 already taken out above 
    elif(card.text == "Work dinner"): 
        player_infos = get_all_player_infos(game_id)
        num_players = len(list(player_infos))
        for player_info in player_infos:
            player_info.money -= 50  # everyone pay $50
        job = get_job("Hair Stylist")
        if(job.picked):  # someone is the hair stylist, gets paid $50/player
            stylist = get_player_with_job(game_id, job)
            stylist.money += (50 * num_players)  # gets paid $50 per other player + $50 already taken out above 
    elif(card.text == "Wedding"): 
        player_infos = get_all_player_infos(game_id)
        num_players = len(list(player_infos))
        for player_info in player_infos:
            player_info.money -= 150  # everyone pay $150
        job = get_job("Hair Stylist")
        if(job.picked):  # someone is the hair stylist, gets paid $150/player
            stylist = get_player_with_job(game_id, job)
            stylist.money += (150 * num_players)  # gets paid $150 per other player + $150 already taken out above 
    elif(card.text == "Minor medical problems"):
        if(player_info.job == "Athlete"):
            player_info.med_prob = True
        if((not player_info.have_pet) and (not player_info.path == "college")):
            player_info.money += card.amount
        else:
            flash("No charge if in college or have a pet", "info")
    elif(card.text == "Major medical problems"):
        if(player_info.job == "Athlete"):
            player_info.med_prob = True
        if((not player_info.have_health_ins) and (not player_info.path == "college")):
            player_info.money += card.amount
        else:
            flash("Covered by health insurance", "info")
    else: # normal, simple card
        if(card.affects_points):
            player_info.points += card.amount
        else:
            player_info.money += card.amount

    db.session.commit()
    return redirect(url_for('player_info'))

@app.route('/actions')
@login_required
def actions():  # actions can only be done every x yrs
    player, player_info = get_cur_player_info()
    if(player_info.house != "None"):
        house = get_house(player_info.house)
    if(player_info.car != "None"):
        car = get_car(player_info.car)
    disabled = {}  # keep track of which actions player is not eligible to do and disable the button for them
    if(player_info.upgrade_over_40 == 0):  # not stuck in upgrade over 40
        if((player_info.path == "college") or (player_info.buying_organic == True) or (player_info.yrs_til_buy_organic > 0)):
            disabled["buy_organic"] = True  # cannot buy organic in college
        if((player_info.house.lower() == "none") or (house.category == "no-family") or(player_info.yrs_til_upgrade_appliances > 0) or (player_info.bought_appliances)):
            disabled["upgrade_appliances"] = True  # must have at least small family house to upgrade appliances
        if(player_info.yrs_til_change_car > 0):
            disabled["change_car"] = True
        if(player_info.yrs_til_change_house > 0):
            disabled["change_house"] = True
        if((player_info.job == "None") or (player_info.yrs_til_buy_clothes > 0)):  # need job since based on salary
            disabled["buy_clothes"] = True
        if(player_info.yrs_til_travel > 0):
            disabled["local_travel"] = True
            disabled["domestic_travel"] = True
            disabled["international_travel"] = True
        if((player_info.married) or ((player_info.house.lower() == "none") or (house.category == "no-family") or (player_info.car.lower() == "none") or (car.category == "no-family")) or (player_info.yrs_til_change_married > 0)):
            disabled["get_married"] = True  # must have at least small family house/car to get married
        if((not player_info.married) or (player_info.yrs_til_change_married > 0)):
            disabled["get_divorced"] = True  # must be married to get divorced
        if((not player_info.married) or (player_info.age > 40) or (player_info.yrs_til_have_kid > 0)):
            disabled["have_kid"] = True  # must be married to have kids and under 40
        if((player_info.oldest_child_age < 18) or (player_info.yrs_til_have_grandkid > 0)):
            disabled["have_grandkid"] = True  # oldest child must be at least 18 to try for grandchild
        if(player_info.have_pet):   # can only have one pet so no need to keep track of years since action done
            disabled["have_pet"] = True  
        if((player_info.job.lower() == "none") or (player_info.yrs_til_switch_jobs > 0)): 
            disabled["switch_jobs"] = True  # must have job for x yrs to switch jobs
        if((player_info.house.lower() == "none") or (player_info.have_pool) or (player_info.yrs_til_rich_action > 0)):
            disabled["buy_pool"] = True  # must have a house to buy a pool, can only have one pool
        if((player_info.house.lower() == "none") or (not player_info.have_pool) or (player_info.yrs_til_rich_action > 0)):
            disabled["sell_pool"] = True  # must have a house and pool to sell pool
        if((player_info.major_donor) or (player_info.yrs_til_rich_action > 0)):
            disabled["major_donor"] = True  # can only be major donor once
        if(player_info.yrs_til_rich_action > 0):
            disabled["season_tickets"] = True
            disabled["backpacking"] = True
        if((player_info.married) or (player_info.age > 40) or (player_info.yrs_til_peace_corps > 0)):
            disabled["peace_corps"] = True  # must be single and <= 40 to do peace corps
        if((player_info.married) or (player_info.age <= 40) or (player_info.yrs_til_mission_trip > 0)):
            disabled["mission_trip"] = True  # must be single and over 40 to do mission trip
        if(player_info.yrs_til_invest > 0):
            disabled["invest"] = True
    else:  # stuck in upgrade over 40, ineligible to do action
        action_options = ["buy_organic", "upgrade_appliances", "change_car", "change_house", "buy_clothes", "local_travel", "domestic_travel", "international_travel", "get_married", "get_divorced", "have_kid", "have_grandkid", "buy_pet", "switch_jobs", "buy_pool", "sell_pool", "major_donor", "season_tickets", "backpacking", "peace_corps", "mission_trip", "invest"]
        disabled = {action: True for action in action_options}
    
    num_people = get_num_people(player_info.married, player_info.num_kids)
    
    house = "None"
    houses = []
    house_costs = []
    if(player_info.house != "None"):
        house = get_house(player_info.house)
        houses = House.query.filter(House.name != house.name)
        house_costs = {house.name: house.cost for house in houses}
    
    car = "None"
    cars = []
    car_costs = []
    if(player_info.car != "None"):
        car = get_car(player_info.car)
        cars = Vehicle.query.filter(Vehicle.name != car.name)
        car_costs = {car.name: car.cost for car in cars}
  
    return render_template('actions.html', page_name='Actions', player_info=player_info, disabled=disabled, num_people=num_people, house=house, houses=houses, house_costs=house_costs, car=car, cars=cars, car_costs=car_costs)

@app.route('/no_action')
@login_required
def no_action():
    player, player_info = get_cur_player_info()
    game = get_game(player.cur_game)
    player_info.done_action = True
    switch_turn(game)
    db.session.commit()
    return redirect(url_for('player_info'))

@app.route('/jobs')
@login_required
def jobs():
    player, player_info = get_cur_player_info()
    if(player_info.jobs_page_type == "all"):
        jobs = Job.query.all()
        picked = {job.title.lower(): job.picked for job in jobs}  # mark picked jobs so can't be chosen by others
    else:
        jobs = Job.query.filter_by(category=player_info.jobs_page_type)  # allow player to filter jobs by category
        picked = {job.title.lower(): job.picked for job in jobs}  # mark picked jobs so can't be chosen by others
    return render_template('jobs.html', page_name='Jobs', player_info=player_info, category=player_info.jobs_page_type, picked=picked, job_options=None)

@app.route('/filter_jobs')
@login_required
def filter_jobs():
    player, player_info = get_cur_player_info()
    player_info.jobs_page_type = request.args.get("job-types")
    db.session.commit()
    return redirect(url_for('jobs'))

@app.route('/get_job_options')
@login_required
def get_job_options():
    job_type = request.args.get('job-dropdown')  # pick type of job getting
    all_jobs = Job.query.all()
    picked = {job.title.lower(): job.picked for job in all_jobs}
    player_info = get_cur_player_info()
    if(job_type == None):
        flash("You must specify a job type.", "error")
        return redirect(url_for('jobs'))
    jobs = list(Job.query.filter_by(category=job_type, picked=False))  # only show jobs that are in the category and unpicked
    while(len(jobs) == 0):  # in case no jobs left in category
        job_type = get_next_job_type(job_type)  # move down to next category
        jobs = list(Job.query.filter_by(category=job_type, picked=False))
    if(job_type == "military"):
        return redirect(url_for("pick_job", job_name="Military"))
    if(job_type in ["job-in-college", "grad-school-1", "grad-school-2"]):
        # only get one option so whatever is picked is your job
        job = jobs[randint(0, len(jobs) - 1)]  # get random job
        return redirect(url_for("pick_job", job_name=job.title))
    elif(job_type == "grad-school-6"):
        # only 1 choice
        return redirect(url_for("pick_job", job="Doctor"))
    elif(job_type == "regular"):
        # get 2 options
        job_options = sample(jobs, 2)  # randomly pick 2 jobs
        job_option_titles = [j.title for j in job_options]
        return  render_template('jobs.html', page_name='Jobs', jobs=job_options, picked=picked, job_option_titles=job_option_titles, category="regular", player_info=player_info)  # show options
    elif(job_type == "college-grad"):
        # get 3 options
        job_options = sample(jobs, 3)  # randomly pick 3 jobs
        job_option_titles = [j.title for j in job_options]
        return  render_template('jobs.html', page_name='Jobs', jobs=job_options, job_option_titles=job_option_titles, picked=picked, category="college-grad", player_info=player_info)  # show options
    else:   # problem!
        return redirect(url_for('jobs'))

@app.route('/pick_job/<job_name>')
@login_required
def pick_job(job_name):  # set up job on player info
    job = get_job(job_name)
    if(job.category not in ["military", "job-in-college"]):
        job.picked = True  # multiple players can do military and jobs in college
    player, player_info = get_cur_player_info()
    player_info.job = job.title
    player_info.cur_time_til_raise = job.default_time_til_raise
    player_info.current_salary = job.base_salary
    player_info.path = get_path(job.title)

    if(job.title.lower() == "janitor"):
        player_info.was_janitor = True

    if(player_info.graduating):
        player_info.graduating = False
    else:
        player_info.yrs_til_switch_jobs = wait_yrs  # changed job as action

    if(player_info.mil_to_college and (player_info.mil_start_college == 0)):  # get job not count as action
        pass
    elif((player_info.ready) and (not player_info.graduating)):  # doing an action
        game = get_game(player.cur_game)
        switch_turn(game)

    db.session.commit()
    return redirect(url_for('player_info'))

@app.route('/pick_job_from_options')
@login_required
def pick_job_from_options():
    job = request.args.get("jobs")
    if(job == None):
        flash("You must select a job.", "error")
        return
    return redirect(url_for('pick_job', job_name=job))

@app.route('/vehicles')
@login_required
def vehicles():
    player, player_info = get_cur_player_info()
    num_people = get_num_people(player_info.married, player_info.num_kids)
    return render_template('vehicles.html', page_name='Vehicles', player_info=player_info, num_people=num_people)

@app.route('/buy_car/<car>')
@login_required
def buy_car(car):
    player, player_info = get_cur_player_info()
    if(player_info.car != "None"):  # handle selling old car
        old_car = get_car(player_info.car)
        player_info.old_car = old_car.name
        player_info.money += player_info.old_car.sell_price
    vehicle = get_car(car)
    player_info.car = vehicle.name
    player_info.money -= vehicle.cost
    if(player_info.old_car != "None"):
        change_in_price = abs(vehicle.cost - old_car.cost)  # calculate points for upgrade/downgrade
        downgrade = -1 if (vehicle.cost - old_car.cost) < 0 else 1
        if(change_in_price <= 10000): player_info.points += (10 * downgrade)
        elif(change_in_price <= 20000): player_info.points += (20 * downgrade)
        elif(change_in_price <= 50000): player_info.points += (35 * downgrade)
        elif(change_in_price <= 80000): player_info.points += (55 * downgrade)
        else: player_info.points += 80
        if(player_info.points < 0):  # depressed
            player_info.depressed = True
        if((downgrade == 1) and (player_info.age >= 40)):  # upgrade over 40 takes wait_yrs
            player_info.upgrade_over_40 = wait_yrs
    player_info.yrs_til_change_car = wait_yrs

    if(player_info.ready):  # doing an action
        game = get_game(player.cur_game)
        player_info.done_action = True
        switch_turn(game)

    db.session.commit()
    return redirect(url_for('player_info'))

@app.route('/houses')
@login_required
def houses():
    player = get_cur_player()
    player_infos = get_all_player_infos(player.cur_game)
    disabled = {}  # only one of each house, once taken other players cannot have
    for player_info in player_infos:
        house = player_info.house.lower()
        if(house != "none"):
            disabled[house] = True  # house is already owned
    return render_template('houses.html', page_name='Houses', disabled=disabled, player_info=player_info)

@app.route('/buy_house/<house>')
@login_required
def buy_house(house):
    player, player_info = get_cur_player_info()
    if(player_info.house != "None"):  # handle selling old house
        old_house = get_house(player_info.house)
        player_info.old_house = old_house.name
        player_info.money += old_house.sell_price
    new_house = get_house(house)
    player_info.house = new_house.name
    cost = new_house.cost
    if(player_info.job == "Carpenter"):
        cost *= 0.75   # carpenter gets 25% off house cost
    if(player_info.job == "Realtor"):
        cost *= 0.9   # realtor gets 10% off house cost
    player_info.money -= cost
    player_info.bought_appliances = False
    if(player_info.old_house != "None"):
        change_in_price = abs(new_house.cost - old_house.cost)  # points for upgrade/downgrade
        downgrade = -1 if (new_house.cost - old_house.cost) < 0 else 1
        if(change_in_price <= 50000): player_info.points += (35 * downgrade)
        elif(change_in_price <= 100000): player_info.points += (55 * downgrade)
        elif(change_in_price <= 250000): player_info.points += (80 * downgrade)
        elif(change_in_price <= 500000): player_info.points += (110 * downgrade)
        else: player_info.points += 150
        if(player_info.points < 0):  # depressed
            player_info.depressed = True
        if((downgrade == 1) and (player_info.age >= 40)):  # upgrade over 40 takes wait_yrs
            player_info.upgrade_over_40 = wait_yrs
    player_info.yrs_til_change_house = wait_yrs

    if(player_info.ready):  # doing an action
        game = get_game(player.cur_game)
        player_info.done_action = True
        switch_turn(game)

    db.session.commit()
    return redirect(url_for('player_info'))

@app.route('/expenses/<testing>/<data>')
@login_required
def expenses(testing, data):
    is_testing = True if testing.lower() == "true" else False

    player, player_info = get_cur_player_info()

    if(is_testing):  # get new data to test
        data = json.loads(data)
        my_job = data['job']
        my_house = data['house']  
        my_car = data['car']
        my_home_ins = True if data['home_ins'] != None else False
        my_auto_ins = True if data['auto_ins'] != None else False
        my_health_ins = True if data['health_ins'] != None else False
        my_married = True if data['married'] != None else False
        my_num_kids = (1 + player_info.num_kids) if data['kids'] == "test-single-child" else (2 + player_info.num_kids) if data['kids'] == "test-twins" else (0 + player_info.num_kids)
        my_loans = player_info.loans + (int(data['loan']) if data['loan'] != None and data['loan'] != '' else 0)
        my_path = get_path(my_job)
    else:  # data is real current player info
        my_job = player_info.job
        my_house = player_info.house
        my_car = player_info.car
        my_home_ins = player_info.have_home_ins
        my_auto_ins = player_info.have_auto_ins
        my_health_ins = player_info.have_health_ins
        my_married = player_info.married
        my_num_kids = player_info.num_kids
        my_loans = player_info.loans
        my_path = player_info.path
 
    job = "None"
    job_stress = 0
    if(my_job != "None"):
        job = get_job(my_job)
        if(is_testing):
            job_stress = int(job.base_salary / 1000)  # current salary = base salary since if got new job would start over salary
        else:
            job_stress = int(player_info.current_salary / 1000) if player_info.path == "military" else int(job.base_salary / 1000)
    jobs = Job.query.filter(Job.title != my_job)  # get all jobs except player's current job for dropdown

    house = "None"
    house_stress = 0
    houses = House.query.all()
    rent = 0
    if(my_house != "None"):  # player has a house
        if((not is_testing) and (player_info.yrs_til_change_house == wait_yrs)):  # bought new house on last turn, use old house for expenses calcs
            if(player_info.old_house != "None"): # not buying first house
                house = get_house(player_info.old_house)
                houses = House.query.filter(House.name != player_info.old_house) 
            else:
                house = get_house(player_info.house)  
                houses = House.query.filter(House.name != my_house) # get all houses except player's current house for dropdown 
        else:
            house = get_house(my_house)    
        house_stress = house.minus_points
        if(house.category == "no-family"):
            rent = house.cost
    
    car = "None"
    cars = Vehicle.query.all()
    if(my_car != "None"):
        if((not is_testing) and (player_info.yrs_til_change_car == wait_yrs)):  # bought new car on last turn, use old car for expenses calcs
            if(player_info.old_car != "None"): # not buying first car
                car = get_car(player_info.old_car)
                cars = Vehicle.query.filter(Vehicle.name != player_info.old_car) 
            else:
                car = get_car(player_info.car) 
                cars = Vehicle.query.filter(Vehicle.name != player_info.car) # get all cars except player's current car for dropdown
        else:
            car = get_car(my_car) 
        
    taxes = get_taxes(player_info.current_salary if not is_testing else job.base_salary if my_job != "None" else 0, my_job, my_married)
    player_info.total_taxes = taxes
    num_people = get_num_people(my_married, my_num_kids)
    benefits = check_eligibility(my_path, player_info.yrs_military, player_info.age_grad, player_info.age)

    if(not is_testing):
        auto_ins = 0 if player_info.last_auto_ins == 0 else player_info.last_auto_ins
    else:
        auto_ins = 0 if not my_auto_ins else car.insurance
    if(my_job == "Mechanic"):
        auto_ins = 0  # mechanic gets free auto insurance

    if(not is_testing):
        home_ins = 0 if player_info.last_home_ins == 0 else player_info.last_home_ins
    else:
        home_ins = 0 if not my_home_ins else house.insurance
    if(my_job == "Firefighter"):
        home_ins = 0  # firefighter gets free home insurance

    health_ins = 0 if not my_health_ins else 500 * num_people
    if(player_info.age < 26):
        health_ins = 0
    if(benefits):
        health_ins = 0  # eligible for military benefits: free health insurance
    if(my_job == "Doctor"):
        health_ins = health_ins * 0.9  # doctor gets 10% off health insurance

    player_info.total_insurance = auto_ins + health_ins + home_ins

    shopping = 1000 * num_people
    if(my_path == "college"):
        shopping *= 0.5  # college students get 50% off shopping b/c eat at dining hall/student discount
    player_info.total_shopping = shopping

    utilities = 0 if house == "None" else 50 + 0.1 * house.cost
    if(my_job in ["Plumber", "Electrician"]):
        utilities *= 0.5  # get 50% utilities expense
    player_info.total_utilities = utilities

    maid = 0 if house == "None" else house.maid
    if((player_info.was_janitor) or (is_testing and (my_job == "Janitor"))):
        maid = 0  # janitor learned cleaning skills so no pay maid
    player_info.total_maid = maid

    car_maintenance = 0 if (car == "None" or car.category == "no-family") else 100
    if(my_job == "Mechanic"):
        car_maintenance = 0  # mechanic no pay car maintenance expense
    player_info.total_car_maintenance = car_maintenance

    dental_fees = 10 * num_people
    if(my_job == "Dentist"):
        dental_fees = 0  # dentist no pay dental fees
    player_info.total_dental = dental_fees

    eat_ent = 0 
    if(my_job != "None"):
        cur_salary = player_info.current_salary if not is_testing else job.base_salary
        if cur_salary < 50000:
            eat_ent = 0.01 * cur_salary
        elif cur_salary < 100000:
            eat_ent = 0.05 * cur_salary
        else: 
            eat_ent = 0.1 * cur_salary

        if(my_job in ["Cashier", "Barista"]):
            eat_ent *= 0.5  # 50% off
        if(benefits):  # military benefits also for veterans (job not currently military)
            eat_ent *= 0.5  # 50% off
    player_info.total_eat_ent = eat_ent

    gas = 0 if car == "None" or car.category == "no-family" else car.gas
    if(my_job == "Truck Driver"):
        gas = 0  # truck driver no pay for gas
    player_info.total_gas = gas

    college_loans_int = get_college_loan_int(player_info.college_loans, player_info.age, player_info.age_grad)
    loans_int = get_loan_int(my_loans)

    misc_points = 0
    if player_info.buying_organic:
        misc_points += (50 * num_people)
    if player_info.have_pet:  
        misc_points += 10
    if player_info.have_pool:  
        misc_points += 250
    if((player_info.points < 0) or player_info.depressed):
        misc_points += abs(player_info.points * 0.1)  # get 10% of negative points back
    if my_job == "Teacher":
        misc_points += 100  # teacher appreciation
    if((my_path == "college") and (my_job != "None")):  
        misc_points -= 50  # job in college = minus points
    if(my_loans > 0):
        misc_points -= math.ceil(my_loans / 10000)  # if loan, lose points -> incentive to pay off

    rent_cost = 0
    transit_fee = 0
    org_cost = 0
    pet_cost = 0
    pool_cost = 0
    depressed_cost = 0
    loans_cost = 0
    misc_fees = 0
    if(rent != 0):
        rent_cost = rent
    if(car == "Public Transit"):  # yearly expense
        fee = get_car("Public Transit").cost 
        transit_fee = fee
    if(player_info.buying_organic):
        org_cost = (1000 * num_people)
        if(my_job == "Farmer"):
            org_cost *= 0.75  # farmer gets 25% off buying organic
    if player_info.have_pet:  # pet fees
        pet_cost = (100 if my_job != "Veterinarian" else 0)
    if player_info.have_pool:  # pool fees
        pool_cost = 20000
    if((player_info.points < 0) or player_info.depressed): # depression fee
        depressed_cost = 1000  
    if(my_loans > 0):
        loans_cost = (0.005 * loans_int)  # automatically pay back 0.5% of loans
    if(my_job == "Waiter"): # waiter gets $2000 in tips
        misc_fees -= 2000 

    misc_fees += rent + transit_fee + org_cost + pet_cost + pool_cost + depressed_cost + loans_cost

    player_info.total_rent = rent_cost
    player_info.total_transit = transit_fee
    player_info.total_organic = org_cost
    player_info.total_pet = pet_cost
    player_info.total_pool = pool_cost
    player_info.total_depression = depressed_cost
    player_info.total_loans = loans_cost

    new_auto_ins = get_new_auto_ins(player_info)
    new_home_ins = get_new_home_ins(player_info)
    new_health_ins = 500 * num_people
    if(player_info.age < 26):
        new_health_ins = 0
    if(benefits):
        new_health_ins = 0  # eligible for military benefits: free health insurance
    if(my_job == "Doctor"):
        new_health_ins = new_health_ins * 0.9  # doctor gets 10% off health insurance

    no_fam_car = True
    if(my_car != "None"):  # will have a car next year
        next_car = get_car(my_car)
        if(next_car.category != "no-family"):
            no_fam_car = False

    no_fam_house = True
    if(my_house != "None"):  # will have a car next year
        next_house = get_house(my_house)
        if(next_house.category != "no-family"):
            no_fam_house = False

    tax_prep = 100
    if(player_info.job == "Accountant"):
        tax_prep = 0
    player_info.total_tax_prep = tax_prep

    all_tax_prep_fees = get_all_tax_prep_fees(player.cur_game)
    all_dental_fees = get_all_dental_fees(player.cur_game)
    all_pet_fees = get_all_pet_fees(player.cur_game)
    all_depression_fees = get_all_depression_fees(player.cur_game)

    loan_pts = math.ceil(my_loans / 10000)

    db.session.commit()
    return render_template('expenses.html', page_name='Expenses', player_info=player_info, job=job, job_stress=job_stress, house=house, house_stress=house_stress, car=car, jobs=jobs, taxes=taxes, num_people=num_people, houses=houses, cars=cars, college_loans_int=college_loans_int, loans_int=loans_int, auto_ins=auto_ins, health_ins= health_ins, home_ins=home_ins, shopping=shopping, car_maintenance=car_maintenance, maid=maid, utilities=utilities, dental_fees=dental_fees, eat_ent=eat_ent, gas=gas, new_auto_ins=new_auto_ins, new_home_ins=new_home_ins, new_health_ins=new_health_ins, misc_points=misc_points, misc_fees=misc_fees, rent=rent, transit_fee=transit_fee, no_fam_car=no_fam_car, no_fam_house=no_fam_house, benefits=benefits, all_dental_fees=all_dental_fees, all_pet_fees=all_pet_fees, all_depression_fees=all_depression_fees, tax_prep=tax_prep, all_tax_prep_fees=all_tax_prep_fees, my_job=my_job, cur_house=my_house, cur_car=my_car, my_home_ins=my_home_ins, my_auto_ins=my_auto_ins, my_health_ins=my_health_ins, my_married=my_married, my_num_kids=my_num_kids, my_loans=my_loans, my_path=my_path, testing=is_testing, loan_pts=loan_pts)

@app.route('/test_expenses')
@login_required
def test_expenses():
    job = request.args.get("job")
    house = request.args.get("house")
    home_ins = request.args.get("test-home-ins")
    car = request.args.get("car")
    auto_ins = request.args.get("test-auto-ins")
    health_ins = request.args.get("test-health-ins")
    married = request.args.get("test-married")
    kids = request.args.get("test-kids")
    loan = request.args.get("test-loans-amount")

    data = {'job': job, 'house': house, 'home_ins': home_ins, 'car': car, 'auto_ins': auto_ins, 'health_ins': health_ins, 'married': married, 'kids': kids, 'loan': loan}
    data_str = json.dumps(data)
    return redirect(url_for('expenses', testing="true", data=data_str))
    #return render_template('expenses.html', page_name='Expenses', player_info=player_info, jobs=jobs, houses=houses, cars=cars)

@app.route('/scoreboard')
@login_required
def scoreboard():
    scores = []
    player = get_cur_player()
    players_infos = Player_Info.query.filter_by(game_id=player.cur_game, active=True).join(Player, Player_Info.player_id==Player.id).add_columns(Player.name, Player_Info.points, Player_Info.money).order_by(Player_Info.points.desc())

    for player_info in players_infos:  # show players ordered by highest -> lowest points
        scores.append({"name": player_info.name, "points": player_info.points, "money": player_info.money})
  
    return render_template('scoreboard.html', page_name='Scoreboard', scores=scores)

@app.route('/stats')
@login_required
def stats():
    player, player_info = get_cur_player_info()
    return render_template('stats.html', page_name='Stats', player_info=player_info)

@app.route('/get_loan')
@login_required
def get_loan():
    player, player_info = get_cur_player_info()
    amount = request.args.get('amount')
    if(not amount.isnumeric()):
        flash("You must specify a numeric amount.", "error")
        return redirect(url_for('player_info'))
    player_info.loans += int(amount)
    player_info.need_loan = False
    db.session.commit()
    return redirect(url_for('player_info'))

@app.route('/save_notes/<notepad>')
@login_required
def save_notes(notepad):
    sticky_note = request.args.get("notepad")  # get which sticky note to save
    player, player_info = get_cur_player_info()
    if(int(notepad) == 1): player_info.notes1 = sticky_note
    elif(int(notepad) == 2): player_info.notes2 = sticky_note
    elif(int(notepad) == 3): player_info.notes3 = sticky_note
    elif(int(notepad) == 4): player_info.notes4 = sticky_note
    db.session.commit()
    return redirect(url_for('player_info'))

@app.route('/save_allnotes')
@login_required
def save_allnotes():
    print("Saving...")
    sticky_notes = request.args.get("notepad")
    for sticky_note in sticky_notes:
        print(sticky_note)

@app.route('/go_to_card')
@login_required
def go_to_card():
    text = request.args.get("card")
    return redirect(url_for('cards',  _anchor=text))

@app.route('/database')
@login_required
def database():  # personal, internal use to view current state of database
    players = Player.query.all()
    games = Game.query.all()
    cards = Card.query.all()
    jobs = Job.query.all()
    vehicles = Vehicle.query.all()
    houses = House.query.all()
    return render_template('database.html', players=players, games=games, cards=cards, jobs=jobs, vehicles=vehicles, houses=houses)

@app.route('/reset')
@login_required
def reset():
    player, player_info = get_cur_player_info()
    game = get_game(player.cur_game)
    game.roll_order = False
    game.cur_turn = 0

    db.session.delete(player_info)
    db.session.commit()
    return redirect(url_for('join_game', game_id=player.cur_game))

@app.route('/buy_organic')
@login_required
def buy_organic():
    player, player_info = get_cur_player_info()
    player_info.buying_organic = True
    player_info.yrs_til_buy_organic = wait_yrs
    player_info.num_times_buy_organic += 1

    game = get_game(player.cur_game)
    player_info.done_action = True
    switch_turn(game)

    db.session.commit()
    return redirect(url_for('player_info'))

@app.route('/upgrade_appliances')
@login_required
def upgrade_appliances():
    player, player_info = get_cur_player_info()
    house = get_house(player_info.house)
    cost = house.cost * 0.01  # cost 1% of house cost
    player_info.money -= cost
    player_info.points += 100  # get 100 points
    player_info.yrs_til_upgrade_appliances = wait_yrs
    player_info.bought_appliances = True

    game = get_game(player.cur_game)
    player_info.done_action = True
    switch_turn(game)

    db.session.commit()
    return redirect(url_for('player_info'))

@app.route('/change_car')
@login_required
def change_car():
    return redirect(url_for('vehicles'))

@app.route('/change_house')
@login_required
def change_house():
    return redirect(url_for('houses'))

@app.route('/buy_clothes')
@login_required
def buy_clothes():
    player, player_info = get_cur_player_info()
    cost = player_info.current_salary * 0.01  # cost 1% of current salary
    player_info.money -= cost
    player_info.points += (50 * get_num_people(player_info.married, player_info.num_kids))  # get 50 points per person
    player_info.yrs_til_buy_clothes = wait_yrs
    player_info.num_times_buy_clothes += 1

    game = get_game(player.cur_game)
    player_info.done_action = True
    switch_turn(game)

    db.session.commit()
    return redirect(url_for('player_info'))

@app.route('/travel/<loc>')
@login_required
def travel(loc):
    player, player_info = get_cur_player_info()
    num_people = get_num_people(player_info.married, player_info.num_kids)
    if(loc == "local"):
        points = (10 + (20 * num_people))  # get 10 + 20 per person points
        # check job for travel benefits: 2 people free for local travel
        if(player_info.job != "None"):
            job = get_job(player_info.job)
            if((job.title.lower() in ['military', "flight attendant", "pilot"]) or check_eligibility(player_info.path, player_info.yrs_military, player_info.age_grad, player_info.age)):
                num_people -= 2
        if(num_people < 0): 
            num_people = 0  # just in case 1 person buy took off 2 people for discount
        cost = 500 * num_people
    elif(loc == "domestic"):
        points = (40 + (30 * num_people))  
        cost = 1000 * num_people  
    else:  # international
        points = (60 + (40 * num_people)) 
        cost = 5000 * num_people  
    player_info.money -= cost
    player_info.points += points  
    player_info.yrs_til_travel = wait_yrs
    player_info.num_times_travel += 1

    game = get_game(player.cur_game)
    player_info.done_action = True
    switch_turn(game)

    db.session.commit()
    return redirect(url_for('player_info'))

@app.route('/change_marriage/<type>')
@login_required
def change_marriage(mtype):
    player, player_info = get_cur_player_info()
    if(mtype.lower() == "marriage"):
        player_info.married = True
        player_info.points += 50
    else: # "divorce"
        player_info.married = False
        player_info.points *= 0.99  # lose 1% of points
        player_info.money -= 1000  # pay lawyer $1000

        # lawyer collect $1000 fee
        all_players = get_all_player_infos(player.cur_game)
        for p in all_players:
            if(p.job == "Lawyer"):
                p.money += 1000

    player_info.yrs_til_change_married = wait_yrs

    game = get_game(player.cur_game)
    player_info.done_action = True
    switch_turn(game)

    db.session.commit()
    return redirect(url_for('player_info'))

@app.route('/have_kids')
@login_required
def have_kids():
    player, player_info = get_cur_player_info()
    roll = simulateRoll()
    num_babies = 1 if roll < 6 else 2
    points = (100 * num_babies) if (player_info.num_kids + num_babies) <= 4 else (-50 * num_babies) if (player_info.num_kids + num_babies) >= 6 else -50 if (num_babies == 1) else 50  # last one is for twins where one is +50 and one is -50
    school_fees = 1500 * num_babies
    job = get_job(player_info.job)
    if(job.lower() == "teacher"):
        school_fees = 0  # teacher doesn't pay school fees
    
    # teacher collect all school fees
    all_players = get_all_player_infos(player.cur_game)
    for p in all_players:
        if(p.job == "Teacher"):
            p.money += school_fees

    player_info.num_kids += num_babies
    player_info.points += points
    player_info.money -= school_fees
    player_info.yrs_til_have_kid = wait_yrs

    game = get_game(player.cur_game)
    player_info.done_action = True
    switch_turn(game)

    db.session.commit()
    flash("You had " + ("a single child." if num_babies == 1 else "twins!"), "info")
    return redirect(url_for('player_info'))

@app.route('/have_grandkids')
@login_required
def have_grandkids():
    player, player_info = get_cur_player_info()
    roll = simulateRoll()
    nums_needed = (player_info.num_kids / 2) + 1
    if(nums_needed > 5): nums_needed = 5  # max of 5 nums on die
    if(roll <= nums_needed):  # had grandchild
        player_info.points += 200
        flash("You had a grandchild!", "info")
    else:  # no grandchild
        flash("You did not have a grandchild.", "info")
    player_info.yrs_til_have_grandkid = wait_yrs

    game = get_game(player.cur_game)
    player_info.done_action = True
    switch_turn(game)

    db.session.commit()
    return redirect(url_for('player_info'))

@app.route('/buy_pet')
@login_required
def buy_pet():
    player, player_info = get_cur_player_info()
    player_info.money -= 100
    player_info.have_pet = True

    game = get_game(player.cur_game)
    player_info.done_action = True
    switch_turn(game)

    db.session.commit()
    return redirect(url_for('player_info'))

@app.route('/switch_jobs')
@login_required
def switch_jobs():
    return redirect(url_for('jobs'))

@app.route('/pool/<type>')
@login_required
def pool(ptype):
    player, player_info = get_cur_player_info()
    if(ptype == "buy"):
        player_info.money -= 100000
        player_info.have_pool = True
    else:  # "sell"
        player_info.have_pool = False
    player_info.yrs_til_rich_action = wait_yrs

    game = get_game(player.cur_game)
    player_info.done_action = True
    switch_turn(game)

    db.session.commit()
    return redirect(url_for('player_info'))

@app.route('/major_donor')
@login_required
def major_donor():
    player, player_info = get_cur_player_info()
    player_info.money -= 1000000
    player_info.points += 5000
    player_info.major_donor = True
    player_info.yrs_til_rich_action = wait_yrs

    game = get_game(player.cur_game)
    player_info.done_action = True
    switch_turn(game)

    db.session.commit()
    return redirect(url_for('player_info'))

@app.route('/season_tickets')
@login_required
def season_tickets():
    player, player_info = get_cur_player_info()
    num_people = get_num_people(player_info.is_married, player_info.num_kids)
    player_info.money -= (50000 - (10000 * num_people))
    player_info.points += (20  * num_people)
    player_info.yrs_til_rich_action = wait_yrs
    player_info.num_times_season_tickets += 1

    game = get_game(player.cur_game)
    player_info.done_action = True
    switch_turn(game)

    db.session.commit()
    return redirect(url_for('player_info'))

@app.route('/peace_corps')
@login_required
def peace_corps():
    player, player_info = get_cur_player_info()
    player_info.money -= 1000
    player_info.points += 75
    player_info.yrs_til_peace_corps = wait_yrs
    player_info.num_times_peace_corps += 1

    game = get_game(player.cur_game)
    player_info.done_action = True
    switch_turn(game)

    db.session.commit()
    return redirect(url_for('player_info'))

@app.route('/mission_trip')
@login_required
def mission_trip():
    player, player_info = get_cur_player_info()
    player_info.money -= 10000
    player_info.points += 500
    player_info.yrs_til_mission_trip = wait_yrs
    player_info.num_times_mission_trip += 1

    game = get_game(player.cur_game)
    player_info.done_action = True
    switch_turn(game)

    db.session.commit()
    return redirect(url_for('player_info'))

@app.route('/backpacking')
@login_required
def backpacking():
    player, player_info = get_cur_player_info()
    num_people = get_num_people(player_info.is_married, player_info.num_kids)
    player_info.money -= (5000 * num_people)
    player_info.points += 250
    player_info.yrs_til_rich_action = wait_yrs
    player_info.num_times_backpacking += 1

    game = get_game(player.cur_game)
    player_info.done_action = True
    switch_turn(game)

    db.session.commit()
    return redirect(url_for('player_info'))

@app.route('/invest')
@login_required
def invest():
    amount = request.args.get('amount')
    if(not amount.isnumeric()):
        flash("You must specify a numeric amount.", "error")
        return redirect(url_for('actions'))
    player, player_info = get_cur_player_info()
    if(amount > player_info.money):
        flash("You do not have enough money for that investment.", "error")
        return redirect(url_for('actions'))
    roll = simulateRoll()
    if((roll % 2) == 0):  # even: gain
        amount = int(amount) * 0.25  
        flash("Your investment resulted in a GAIN.", "info")
    else:  # odd: loss
        amount = int(amount) * -0.1
        flash("Your investment resulted in a LOSS.", "info")
    player_info.money += amount
    player_info.yrs_til_invest = wait_yrs
    player_info.num_times_invest += 1

    game = get_game(player.cur_game)
    player_info.done_action = True
    switch_turn(game)

    db.session.commit()
    return redirect(url_for('actions'))

@app.route('/mil_to_college')
@login_required
def mil_to_college():
    player, player_info = get_cur_player_info()
    player_info.mil_to_college = True

    # remove military job info
    player_info.path = college
    player_info.job = "None"
    player_info.num_pay_raises = 0
    player_info.cur_time_til_raise = 0
    player_info.current_salary = 0
 
    return redirect(url_for('player_info'))

def get_cur_player():
    player = Player.query.filter_by(name=current_user.name).first_or_404()
    return player

def get_cur_player_info():
    player = get_cur_player()
    player_info = Player_Info.query.filter_by(game_id=player.cur_game, player_id=player.id).first_or_404()
    return (player, player_info)

def get_game(id):
    game = Game.query.filter_by(id=id).first_or_404()
    return game

def get_all_player_infos(game_id):
    player_infos = Player_Info.query.filter_by(game_id=game_id)
    return player_infos

def get_player_with_job(game_id, job):
    player = Player_Info.query.filter_by(game_id=game_id).join(job, Player_Info.job == job.title).first_or_404()
    return player

def get_job(title):
    job = Job.query.filter_by(title=title).first_or_404()
    return job

def get_car(name):
    car = Vehicle.query.filter_by(name=name).first_or_404()
    return car

def get_house(name):
    house = House.query.filter_by(name=name).first_or_404()
    return house

def simulateRoll():
    roll = randint(1, 6)
    return roll

def is_valid_card(player_info, card):
    if((player_info.age == 18) or (player_info.car == "None")):  # no car (no insurance in first year so no probs)
        if(card.text in ["Stuck in traffic", "Car accident", "Speeding", "Car repairs"]):
            return False
    if((player_info.age == 18) or (player_info.house == "None")):  # no house (no insurance in first year so no probs)
        if(card.text in ["Earthquake damage", "Fire damage", "Pest problem"]):
            return False
    if(player_info.job == "None"):  # no job
        if(card.text in ["Lost job"]):
            return False
    return True

def get_taxes(cur_salary, job, married):
    percent = 0
    if(cur_salary < 40000): percent = 0.1
    elif(cur_salary < 80000): percent = 0.2
    elif(cur_salary < 200000): percent = 0.3
    else: percent = 0.4  
    taxes = percent * cur_salary
    if(job.lower() == "accountant"):
        taxes = 0
    if(married):
        taxes /= 2
    return int(taxes)

def get_path(job):
    if(job == "None"):
        return "college"  # default
    elif(job == "Military"): 
        return "military"
    elif(job in ["Cashier", "Barista", "Waiter", "Janitor"]): 
        return "college"
    else:
        return "regular"  

def check_eligibility(path, yrs_military, age_grad, age):
    if(path.lower() == "military"): return True
    if((yrs_military != 0) and ((age - age_grad) < yrs_military)): return True
    return False

def get_num_people(is_married, num_kids):
    return 1 + num_kids + (1 if is_married else 0)

def get_college_loan_int(college_loans, age, age_grad):
    if(age_grad == 0):  # not yet graduated
        return int(college_loans * 1.05)
    if((age - age_grad) <= 5): return int(college_loans * 1.05)
    elif((age - age_grad) <= 10): return int(college_loans * 1.1)
    else: return int(college_loans * 1.2)

def get_loan_int(loans):
    return int(loans * 1.05)

def get_next_job_type(job_type):
    if(job_type == "grad-school-6"): return "grad-school-2"
    if(job_type == "grad-school-2"): return "grad-school-1"
    if(job_type == "grad-school-1"): return "college-grad"
    if(job_type == "college-grad"): return "regular"
    if(job_type == "regular"): return "job-in-college"
    else: return "regular"  # military???

def get_new_auto_ins(player_info):
    new_auto_ins = 0
    if(player_info.yrs_til_change_car == wait_yrs):  # just bought new car, show new insurance
        t_car = get_car(player_info.car)
        new_auto_ins = t_car.insurance
    elif((player_info.car != "None") and (not player_info.have_auto_ins)):  # have car but no insurance
        t_car = get_car(player_info.car)
        new_auto_ins = t_car.insurance
    if(player_info.job == "Mechanic"):
        new_auto_ins = 0  # mechanic gets free auto insurance
    return new_auto_ins

def get_new_home_ins(player_info):
    new_home_ins = 0
    if(player_info.yrs_til_change_house == wait_yrs):  # just bought new house, show new insurance
        t_house = get_house(player_info.house)
        new_home_ins = t_house.insurance
    elif((player_info.house != "None") and (not player_info.have_home_ins)):  # have home but no insurance
        t_house = get_house(player_info.house)
        new_home_ins = t_house.insurance
    if(player_info.job == "Firefighter"):
        new_home_ins = 0  # firefighter gets free home insurance
    return new_home_ins

def get_announcements(player_info):
    announcements = {}
    player = get_cur_player()
    player_infos = get_all_player_infos(player.cur_game)
    game = Game.query.filter_by(id=player.cur_game)   # not get_game() !
    if(game.first().cur_turn == -1):  # game not started yet, no announcements
        return announcements
    else:
        if(player_info.money < 0):  # automatically need to get a loan
            announcements["NEED TO GET A LOAN"] = "urgent"
            player_info.need_loan = True

        if((game.first().cur_turn == 1) and (player_info.done_action)):    # already went through a round a turns, end of year
            announcements["End of year"] = "end_of_year"
        else:  # don't really want/need these to show up at end of year
            cur_turn = game.join(Player_Info, Player_Info.turn_num == Game.cur_turn).add_columns(Player_Info.player_id).join(Player, Player.id == Player_Info.player_id).add_columns(Player.name).first().name
            announcements[cur_turn + "'s turn"] = "turn"
        
            if((player_info.path == "military") and (player_info.age == 20)):
                announcements["Eligible for college with free tuition for 4 yrs"] = "fyi"
            if((player_info.path == "college") and (player_info.age >= 20) and (player_info.age < 22) and (player_info.car in ["None", "Skateboard", "Bike"])):
                announcements["Need non-college vehicle by graduation"] = "fyi"
            if((player_info.path == "college") and (player_info.age == 22) and (player_info.car in ["None", "Skateboard", "Bike"]) and (not player_info.mil_to_college)):
                announcements["Need non-college vehicle by graduation"] = "urgent"
            if((player_info.path != "military") and (player_info.age >= 20) and (player_info.age < 22) and (player_info.house == "None")):
                announcements["Need house before 23"] = "fyi"
            if((player_info.path != "military") and (player_info.age == 22) and (player_info.house == "None")):
                announcements["Must buy house this year"] = "urgent"
            if(player_info.age == 25):
                announcements["Next year no longer covered by parents' health insurance"] = "fyi"
            if((player_info.path == "military") and (player_info.num_pay_raises == 4)):
                announcements["Only one more pay raise"] = "fyi"
            if((player_info.age >= 35) and (player_info.age < 40)):
                announcements["Last age to have kids is 40"] = "fyi"
            if(player_info.age == 40):
                announcements["Last year to have kids"] = "urgent"
            if(player_info.age == 64):  # retirement = game over
                announcements["Retiring next year"] = "fyi"
            if(get_college_loan_int(player_info.college_loans, player_info.age, player_info.age_grad) != get_college_loan_int(player_info.college_loans, player_info.age + 1, player_info.age_grad)):
               announcements["Next year college loan interest rate will increase"] = "urgent"   # interest rate about to increase
            if(check_eligibility(player_info.path, player_info.yrs_military, player_info.age_grad, player_info.age) != check_eligibility(player_info.path, player_info.yrs_military, player_info.age_grad, player_info.age + 1)):
               announcements["Uneligible for military benefits next year"] = "urgent"   # benefits run out
            if((player_info.num_kids == 3) or (player_info.num_kids == 4)):
                announcements[">= 5 kids = -50 points each"] = "fyi"
            num_people = get_num_people(player_info.married, player_info.num_kids)
            if(num_people == 4):  # can assume already have house and car
                car = get_car(player_info.car)
                house = get_house(player_info.house) 
                if((car.category != "large-family") or (house.category != "large-family")):
                    announcements["Reached max family size for small car/house"] = "fyi"

        db.session.commit()
        return announcements

def get_id(text):
    words = text.split(" ")
    page_id = ""
    for word in words: 
        page_id += word.lower() + "-";
    page_id = page_id[:-1] 
    return page_id;

def switch_turn(game):
    next_turn = game.cur_turn + 1
    if(next_turn > game.num_players):  # circle back to first player
        next_turn = 1
    game.cur_turn = next_turn

    db.session.commit()
    return redirect(url_for('player_info'))

def get_dental_fees(num_people):
    return 10 * num_people

def get_all_tax_prep_fees(game_id):
    all_players = get_all_player_infos(game_id)
    tax_prep_fees = 0
    for p in all_players:
        if(p.job != "Accountant"):
            tax_prep_fees += 100
    return tax_prep_fees

def get_all_dental_fees(game_id):
    all_players = get_all_player_infos(game_id)
    num_people = 0
    for p in all_players:
        num_people += get_num_people(p.married, p.num_kids)
    dental_fees = get_dental_fees(num_people)
    return dental_fees

def get_all_pet_fees(game_id):
    all_players = get_all_player_infos(game_id)
    num_pets = 0
    for p in all_players:
        if(p.have_pet):
            num_pets += 1
    pet_fees = 100 * num_pets
    return pet_fees

def get_all_depression_fees(game_id):
    all_players = get_all_player_infos(game_id)
    num_depressed = 0
    for p in all_players:
        if(p.depressed):
            num_depressed += 1
    depression_fees = 1000 * num_depressed
    return depression_fees

def end_game(game_id):
    game = get_game(game_id)
    game.finished = True
    game.date_finished = datetime.utcnow()
    db.session.commit()

@app.route('/temp')
@login_required
def temp():
    want_auto_ins = request.args.get("auto-ins")
    
@app.route('/end_of_year')
@login_required
def end_of_year():
    if(request.args.get("btn") == "done"):  # not paying, just ending test, go back to real expenses
        return redirect(url_for('expenses', testing="false", data="none"))

    player, player_info = get_cur_player_info()
    
    expenses = int(request.args.get("total-expenses").replace(",", ""))
    
    net_points = int(request.args.get("net-points").replace(",", ""))
    player_info.points += net_points

    college_loans_payment = request.args.get("college-loans-amount")
    if((player_info.college_loans > 0) and (college_loans_payment not in ["None", None, ""])):
        player_info.college_loans -= int(college_loans_payment)

    loans_payment = request.args.get("loans-amount")
    if((player_info.loans > 0) and (loans_payment not in ["None", None, ""])):
        player_info.loans -= int(loans_payment)

    # update pay raises: check time til raise b/c grad school = regular path, but can have job in college
    if((player_info.path == "college") or (player_info.job == "YouTuber") or (player_info.cur_time_til_raise == 0)):
        pass  # no pay raises in college, YouTuber have different pay raise system
    elif(player_info.path == "military"):  # different pay raise schedule: salary double every 4 yrs up to 5 raises
        if((player_info.num_pay_raises < 5) and (player_info.cur_time_til_raise == 1)):  # time for raise: double salary
            player_info.current_salary *= 2
            player_info.num_pay_raises += 1
            if(player_info.num_pay_raises == 5):  # no more raises
                player_info.cur_time_til_raise = 0
            else:  # reset time til raise
                job = get_job("Military")
                player_info.cur_time_til_raise = job.default_time_til_raise
        elif(player_info.num_pay_raises >= 5):
            pass
        else:
            player_info.cur_time_til_raise -= 1
    elif(player_info.job == "YouTuber"):  # special pay raise system: roll even = +$15,000, roll odd = =$15,000
        roll = simulateRoll()
        if((roll % 2) == 0):
            player_info.current_salary += 15000
        else:
            if(player_info.current_salary != 15000):  # min of $15,000 salary
                player_info.current_salary -= 15000
    else:
        if(player_info.cur_time_til_raise == 1):  # time for raise
            player_info.num_pay_raises += 1
            job = get_job(player_info.job)
            player_info.cur_time_til_raise = job.default_time_til_raise
            player_info.current_salary += 1000  # $1000 raise
        else:
            player_info.cur_time_til_raise -= 1

    # update action chart
    if(player_info.upgrade_over_40 > 0):
        player_info.upgrade_over_40 -= 1
    if(player_info.yrs_til_buy_organic > 0):
        player_info.yrs_til_buy_organic -= 1
    if(player_info.yrs_til_upgrade_appliances > 0):
        player_info.yrs_til_upgrade_appliances -= 1
    if(player_info.yrs_til_change_car > 0):
        player_info.yrs_til_change_car -= 1
    if(player_info.yrs_til_change_house > 0):
        player_info.yrs_til_change_house -= 1
    if(player_info.yrs_til_buy_clothes > 0):
        player_info.yrs_til_buy_clothes -= 1
    if(player_info.yrs_til_travel > 0):
        player_info.yrs_til_travel -= 1
    if(player_info.yrs_til_change_married > 0):
        player_info.yrs_til_change_married -= 1
    if(player_info.yrs_til_have_kid > 0):
        player_info.yrs_til_have_kid -= 1
    if(player_info.yrs_til_have_grandkid > 0):
        player_info.yrs_til_have_grandkid -= 1
    if(player_info.yrs_til_switch_jobs > 0):
        player_info.yrs_til_switch_jobs -= 1
    if(player_info.yrs_til_rich_action > 0):
        player_info.yrs_til_rich_action -= 1
    if(player_info.yrs_til_peace_corps > 0):
        player_info.yrs_til_peace_corps -= 1
    if(player_info.yrs_til_mission_trip > 0):
        player_info.yrs_til_mission_trip -= 1
    if(player_info.yrs_til_invest > 0):
        player_info.yrs_til_invest -= 1

    if(player_info.job == "Teacher"):
        player_info.num_yrs_teacher += 1

    if((player_info.job == "Teacher") and (player_info.num_yrs_teacher == 15)):
        flash("You have been promoted to Principal!", "info")
        player_info.current_salary = 100000
        
    salary = player_info.current_salary
    if((player_info.job == "Athlete") and (player_info.med_prob)):
        salary *= 0.25

    extras = 0
    if(player_info.job == "Accountant"):  # get all tax prep fees
        extras += get_all_tax_prep_fees(player.cur_game)
    elif(player_info.job == "Dentist"):  # get all dental fees
        extras += get_all_dental_fees(player.cur_game)
    elif(player_info.job == "Veterinarian"):  # get all pet fees
        extras += get_all_pet_fees(player.cur_game)

    player_info.money += (salary - expenses + extras)

    player_info.buying_organic = False  # reset
    player_info.med_prob = False  # reset

    player_info.age += 1
    if(player_info.num_kids >= 1):
        player_info.oldest_child_age += 1

    if(player_info.age == 26):  # no longer covered by parents' health insurance
        player_info.have_health_ins = False

    if((player_info.path == "military")):
        player_info.yrs_military += 1

    if((player_info.path == "college") or (player_info.grad_school)):
        player_info.num_yrs_college += 1

    # update to new insurances
    if((player_info.age < 26) or check_eligibility(player_info.path, player_info.yrs_military, player_info.age_grad, player_info.age)):
        player_info.have_health_ins = True
    else:
        want_health_ins = request.args.get("health-ins")
        if(want_health_ins):
            player_info.have_health_ins = True
        else:
            player_info.have_health_ins = False
    want_auto_ins = request.args.get("auto-ins")
    if(want_auto_ins):
        player_info.have_auto_ins = True
        player_info.last_auto_ins = get_new_auto_ins(player_info)
    else:
        player_info.have_auto_ins = False
        player_info.last_auto_ins = 0
    want_home_ins = request.args.get("home-ins")
    if(want_home_ins):
        player_info.have_home_ins = True
        player_info.last_home_ins = get_new_home_ins(player_info)
    else:
        player_info.have_home_ins = False
        player_info.last_home_ins = 0

    # reset yearly vals kept track of
    player_info.med_prob = False
    player_info.depressed = False
    player_info.buy_organic = False
    player_info.done_action = False

    # handle college scholarships
    if((player_info.path == "college") and (player_info.age < 23) and (not player_info.mil_to_college)):  # not graduating yet, free tuition if mil -> college
        tuition = 50000
        roll = simulateRoll()  # roll for scholarship
        scholarship = 5000 * roll
        parent_help = 0
        if(player_info.age == 19):  # add in parent contribution
            roll2 = simulateRoll()  # roll for scholarship
            parent_help = 5000 * roll2
        player_info.college_loans += (tuition - scholarship + parent_help)

    # handle grad school scholarships
    if(player_info.grad_school):  # not graduating yet
        tuition = 100000
        roll = simulateRoll()  # roll for scholarship
        scholarship = 10000 * roll
        player_info.college_loans += (tuition - scholarship)

    if((player_info.age == 65) and ((player_info.loans > 0) or (player_info.college_loans > 0))):  
        player_info.points = 0  # if have loans when retire = lose all points

    db.session.commit()

    if(player_info.num_yrs_college == 10):  # graduating 6 yr grad school
        flash("You graduated 6yr grad school!", "info")
        return redirect(url_for('graduate'))    

    if(player_info.age == 65):  # retirement = game over
        end_game(player.cur_game)
        return redirect(url_for('scoreboard')) # show final scores

    return redirect(url_for('player_info'))

@app.route('/graduate')
@login_required
def graduate():
    player, player_info = get_cur_player_info()

    player_info.age_grad = player_info.age
    player_info.graduating = True
    if(player_info.grad_school):
        player_info.points += 50    # grad school graduation = 100 points
    player_info.points += 50
    player_info.num_yrs_college = 0  # reset so no notification to graduate

    db.session.commit()
    return redirect(url_for('job'))
    
@app.route('/go_to_grad_school')
@login_required
def go_to_grad_school():
    player, player_info = get_cur_player_info()

    player_info.grad_school = True
    player_info.path = "regular"

    # handle grad school scholarships
    tuition = 100000
    roll = simulateRoll()  # roll for scholarship
    scholarship = 10000 * roll
    player_info.college_loans += (tuition - scholarship)

    db.session.commit()
    return redirect(url_for('player_info'))

@app.route('/continue_grad_school')
@login_required
def continue_grad_school():
    player, player_info = get_cur_player_info()

    # handle grad school scholarships
    tuition = 100000
    roll = simulateRoll()  # roll for scholarship
    scholarship = 10000 * roll
    player_info.college_loans += (tuition - scholarship)

    db.session.commit() 
    return redirect(url_for('player_info'))


