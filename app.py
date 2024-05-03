from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_pymongo import PyMongo
import requests
import os
from bs4 import BeautifulSoup

app = Flask(__name__)
app.secret_key = "1234567890"
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True

login_manager = LoginManager()
login_manager.init_app(app)

app.config["MONGO_URI"] = "mongodb+srv://gafuradm09adm:QWgWKykTRgCSlH58@cluster0.c6gqzyr.mongodb.net/registrations?retryWrites=true&w=majority&appName=Cluster0%22"
mongo = PyMongo(app)

class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id

    @staticmethod
    def get(user_id):
        user_data = mongo.db.users.find_one({'_id': user_id})
        if user_data:
            return User(user_data['_id'])
        return None

@login_manager.user_loader
def load_user(user_id):
    print(user_id)
    return User.get(user_id)

def scrape_event_details(event_url):
    response = requests.get(event_url)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    title_element = soup.find('div', class_='title')
    title = title_element.text.strip() if title_element else "Название мероприятия не найдено"
    
    date_element = soup.find('div', class_='single_date')
    date = date_element.text.strip() if date_element else "Дата мероприятия не указана"
    
    desc_element = soup.find('p', class_='')
    desc = desc_element.text.strip() if desc_element else "Описание отсутствует"
    
    location_element = soup.find('div', class_='group')
    location = location_element.text.strip() if location_element else "Место проведения мероприятия не указано"
    
    public_element = soup.find('div', class_='publication')
    public = public_element.text.strip() if public_element else "Дата публикации не указана"

    tickets_available = soup.find(class_='buy-ticket') is not None
    
    event_id = event_url.split('/')[-1]
    
    event_details_url = url_for('event_details', event_url=event_url)
    
    return {'title': title, 'location': location, 'date': date, 'desc': desc, 'public': public, 'tickets_available': tickets_available, 'event_details_url': event_details_url}

def scrape_events():
    url = 'https://sxodim.com/almaty'
    response = requests.get(url)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    cards = soup.find_all(class_='impression-card')
    events = []
    for card in cards:
        title = card.find(class_='impression-card-title').text.strip()
        info = card.find(class_='impression-card-info').text.strip()
        event_url = card.find('a')['href']
        events.append({'title': title, 'info': info, 'url': event_url})
    return events

@app.route('/register', methods=['GET', 'POST'])
def register_new_user():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        
        if mongo.db.users.find_one({'email': email}):
            flash('User with this email already exists!', 'error')
            return redirect(url_for('register_new_user'))
        
        mongo.db.users.insert_one({'email': email, 'password': hashed_password})
        flash('Registration successful! You can now login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = mongo.db.users.find_one({'email': email})
        
        if user and check_password_hash(user['password'], password):
            user_obj = User(user['_id'])
            login_user(user_obj)
            print(current_user)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
            print(current_user)
        else:
            flash('Invalid email or password. Please try again.', 'error')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/')
def index():
    events = scrape_events()
    print(current_user)
    return render_template('index.html', events=events, current_user=current_user)

@app.route('/event/<path:event_url>')
def event_details(event_url):
    event_details = scrape_event_details(event_url)
    print("Current user:", current_user)
    return render_template('event_details.html', event=event_details, current_user=current_user)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
