from flask import Flask, request, redirect, url_for, render_template, flash
from datetime import datetime

import matplotlib
from matplotlib import pyplot as plt

from models import *

matplotlib.use('Agg')  # matplotlib backend

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite3'
app.config['SECRET_KEY'] = '09876543e'

db.init_app(app)
app.app_context().push()

db.create_all() # creating the database tables


# landing page for the app
@app.route('/')
def landing_page():
    return render_template('landing_page.html')


# Login page for an  old user
@app.route('/login', methods=['GET', "POST"])
def old_user():
    if request.method == 'GET':
        return render_template('old_user.html')
    elif request.method == 'POST':
        user_name = request.form['u_name']
        user = User.query.filter_by(name=user_name).first()
        # user doesnt exist
        if user is None:
            flash(message="User not found!")
            return redirect(url_for('old_user'))
        else:
            return redirect(url_for('main_board', user_id=user.id))


# new user sign in page
@app.route('/sign-in', methods=['GET', 'POST'])
def login_user():
    if request.method == 'GET':
        return render_template('new_user.html')
    elif request.method == 'POST':
        user_name = request.form['u_name']
        user = User.query.filter_by(name=user_name).first()
        # username already exists
        if user:
            flash(message='*Username already exists! Try another !')
            return redirect(url_for('login_user'))
        else:
            user_obj = User(name=user_name)
            db.session.add(user_obj)
            db.session.commit()
            return redirect(url_for('main_board', user_id=user_obj.id))


# main dashboard for the logged-in user
@app.route('/<int:user_id>/main-board', methods=['GET', 'POST'])
def main_board(user_id):
    if request.method == 'GET':
        user = User.query.filter_by(id=user_id).first()

        lists = Lists.query.filter_by(u_id=user_id).all()

        return render_template('main_board.html', user=user, lists=lists)


# Create a new list
@app.route('/<int:user_id>/create_list', methods=['GET', 'POST'])
def create_list(user_id):
    if request.method == 'GET':
        return render_template('create_list.html', user_id=user_id)
    elif request.method == 'POST':
        list_title = request.form['l_title']

        if Lists.query.filter_by(u_id=user_id, title=list_title).first():
            flash(message="You have already created a list with this name !")
            return redirect(url_for('create_list', user_id=user_id))
        else:
            list_obj = Lists(u_id=user_id, title=list_title)
            db.session.add(list_obj)
            db.session.commit()

            return redirect(url_for('main_board', user_id=user_id))


# edit an existing list (title)
@app.route('/<int:user_id>/<int:list_id>/edit_list', methods=['GET', 'POST'])
def edit_list(user_id, list_id):
    if request.method == 'GET':
        current_list = Lists.query.filter_by(id=list_id).first()
        return render_template('update_list.html', user_id=user_id, list_id=list_id, list=current_list)
    elif request.method == 'POST':
        new_title = request.form['new_title']

        list_to_be_edited = Lists.query.filter_by(u_id=user_id, id=list_id).first()
        list_to_be_edited.title = new_title

        db.session.commit()

        return redirect(url_for('main_board', user_id=user_id))


# delete an existing list
@app.route('/<int:user_id>/<int:list_id>/delete_list', methods=['GET', 'POST'])
def delete_list(user_id, list_id):
    cards = Cards.query.filter_by(l_id=list_id).all()
    if request.method == 'GET':
        # directly delete a list from the board if it has zero cards
        if len(cards) == 0:
            db.session.delete(Lists.query.filter_by(id=list_id).first())
            db.session.commit()
            return redirect(url_for('main_board', user_id=user_id))
        else:
            # give options before deleting
            return render_template('ask_before_deleting.html', user_id=user_id, list_id=list_id)
    elif request.method == 'POST':
        # delete the lists with the cards
        if request.form['delete'] == 'delete_all':

            for card in cards:
                db.session.delete(card)  # delete the cards first

            db.session.delete(Lists.query.filter_by(id=list_id).first())  # then delete the list
            db.session.commit()

            return redirect(url_for('main_board', user_id=user_id))

        elif request.form['delete'] == 'shift_cards':
            # give option to shift the cards to a new list
            return redirect(url_for('shift_cards', user_id=user_id, list_id=list_id))


# shifting cards to a new list before deleting
@app.route('/<int:user_id>/<int:list_id>/shift_and_delete', methods=['GET', 'POST'])
def shift_cards(user_id, list_id):
    if request.method == 'GET':
        lists = Lists.query.filter_by(u_id=user_id).all()
        # choose list to shift the cards
        return render_template('where_to_shift.html', user_id=user_id, list_id=list_id, lists=lists)

    if request.method == 'POST':
        l_id = request.form['move']
        cards = Cards.query.filter_by(l_id=list_id).all()

        for card in cards:
            card.l_id = l_id  # changing the list it refers to by changing the list id
            card.time_updated = datetime.now().replace(microsecond=0, second=0)

        db.session.delete(Lists.query.filter_by(id=list_id).first())  # then deleting the list

        db.session.commit()
        return redirect(url_for('main_board', user_id=user_id))


# create a card for a list
@app.route('/<int:user_id>/<int:list_id>/create_card', methods=['GET', 'POST'])
def create_card(user_id, list_id):
    if request.method == 'GET':
        card_list = Lists.query.filter_by(id=list_id).first()
        return render_template('create_card.html', user_id=user_id, list_id=list_id, list_name=card_list.title)
    elif request.method == 'POST':
        title = request.form['c_title']

        if Cards.query.filter_by(l_id=list_id, title=title).first():
            flash(message='You have already created a card with this title !')
            return redirect(url_for('create_card', user_id=user_id, list_id=list_id))

        content = request.form['c_content']
        deadline = request.form['deadline']
        done = request.form['done']
        date_now = datetime.now().replace(microsecond=0, second=0)

        list_it_belongs_to = Lists.query.filter_by(id=list_id).first()

        if done == 'yes':
            date = date_now
        else:
            date = None

        card_obj = Cards(l_id=list_id, title=title, content=content, deadline=deadline,
                         time_completed=date, time_updated=date_now, time_created=date_now)

        list_it_belongs_to.cards.append(card_obj) # appending the cards to the 'cards' column

        db.session.add(card_obj)
        db.session.commit()

        return redirect(url_for('main_board', user_id=user_id))


# update an existing card
@app.route('/<int:user_id>/<int:list_id>/<int:card_id>/edit_card', methods=['GET', 'POST'])
def update_card(user_id, list_id, card_id):
    if request.method == 'GET':
        lists = Lists.query.filter_by(u_id=user_id).all()

        cards = Cards.query.filter_by(l_id=list_id, id=card_id).first()

        return render_template('update_card.html', user_id=user_id, list_id=list_id,
                               card_id=card_id, lists=lists, card=cards)

    elif request.method == 'POST':
        card = Cards.query.filter_by(l_id=list_id, id=card_id).first()

        title = request.form['c_title']
        content = request.form['c_content']
        deadline = request.form['deadline']

        done = request.form['done']
        move_to = request.form['move']

        date = datetime.now().replace(microsecond=0, second=0)

        card.title = title
        card.content = content
        card.deadline = deadline
        card.time_updated = date
        card.l_id = move_to

        if done == 'yes':
            card.time_completed = date
        else:
            card.time_completed = None

        db.session.commit()

    return redirect(url_for('main_board', user_id=user_id))


# delete an existing card
@app.route('/<int:user_id>/<int:card_id>/delete_card', methods=['GET', 'POST'])
def delete_card(user_id, card_id):
    db.session.delete(Cards.query.filter_by(id=card_id).first())
    db.session.commit()

    return redirect(url_for('main_board', user_id=user_id))


# summary page of completed cards for the user
@app.route('/<int:user_id>/summary', methods=['GET'])
def show_summary(user_id):
    user = User.query.filter_by(id=user_id).first()
    user_lists = Lists.query.filter_by(u_id=user_id).all()

    # plotting number of cards completed before deadline list wise
    title = []
    no_of_completed_cards = []

    for lists in user_lists:
        title.append(lists.title)
        cards = Cards.query.filter_by(l_id=lists.id).all()
        cards_done = 0
        for card in cards:
            ded = datetime.strptime(card.deadline, '%Y-%m-%dT%H:%M')
            if card.time_completed is not None and card.time_completed < ded:
                cards_done += 1
        no_of_completed_cards.append(cards_done)

    plt.bar(title, no_of_completed_cards, color='hotpink')
    plt.xlabel(' User Lists ')
    plt.ylabel(' Number of cards completed before deadline ')
    plt.savefig('static/images/list_chart.png')
    plt.close()

    # list wise summary and trend line for completed cards
    summary = []
    for list_ in user_lists:

        data = {}
        cards_done = 0
        deadline_crossed = 0

        cards = Cards.query.filter_by(l_id=list_.id).order_by('time_completed').all()

        for card in cards:

            deadline = datetime.strptime(card.deadline, '%Y-%m-%dT%H:%M')

            if card.time_completed is not None and card.time_completed < deadline:
                cards_done += 1
                if card.time_completed.strftime("%d %B, %Y") in data:
                    data[card.time_completed.strftime("%d %B, %Y")] += 1
                else:
                    data[card.time_completed.strftime("%d %B, %Y")] = 1

            elif card.time_completed is not None and card.time_completed > deadline:
                deadline_crossed += 1

            elif datetime.now() > deadline and card.time_completed is None:
                deadline_crossed += 1

        timestamps = list(data.keys())
        no_of_tasks = list(data.values())

        data['list_title'] = list_.title
        data['total_cards'] = len(cards)
        data['cards_done'] = cards_done
        data['cards_not_done'] = len(cards) - cards_done
        data['chart'] = f'/static/images/image_{list_.id}.png'
        data['cards_crossed_deadline'] = deadline_crossed

        if len(timestamps) != 0:
            plt.bar(timestamps, no_of_tasks, color='cyan', width=0.6)
            plt.xlabel(' Dates ')
            plt.ylabel(' Number of cards completed ')
            plt.xlim(-0.7, len(timestamps))

            plt.savefig(f'static/images/image_{list_.id}.png')
            plt.close()

        else:
            data['chart'] = ''

        summary.append(data)

    return render_template('summary_page.html', lists=summary, chart='/static/images/list_chart.png', user=user)


if __name__ == '__main__':
    app.run(debug=True)
