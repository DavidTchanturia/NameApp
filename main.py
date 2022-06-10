import flask
import requests
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import bcrypt


app = Flask(__name__)
app.config['SECRET_KEY'] = 'thisismysecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user.sqlite'
app.config['SQLALCHEMY_BINDS'] = {'name': 'sqlite:///name.sqlite'}
db = SQLAlchemy(app)


genderize_Link = "https://api.genderize.io?name={parameter}"
agify_link = "https://api.agify.io?name={parameter}"


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(25), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(30), nullable=False)

    def __str__(self):
        return f'username: {self.username}, email: {self.email}'


class Name(db.Model):
    __bind_key__ = "name"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(25), nullable=False, unique=True)
    gender = db.Column(db.String(10), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    probability = db.Column(db.Float, nullable=False)
    count = db.Column(db.Integer, nullable=False)

    def __str__(self):
        return f'{self.name} is a {self.gender}'


# db.create_all(bind='name')
db.create_all()


@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == "POST":
        return render_template('login.html')
    return render_template('index.html')


@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()

        if not user is None:
            if user.username == username and bcrypt.checkpw(password.encode("utf-8"), user.password):
                return redirect(url_for('name'))
            flash('incorrect credentials')
        flash('incorrect credentials')
    return render_template('login.html')


@app.route('/register', methods=["POST", "GET"])
def register():
    if request.method == "POST":
        reg_username = request.form['registerUsername']
        reg_password = request.form['registerPassword']
        email = request.form['email']

        hashed_password = bcrypt.hashpw(reg_password.encode("utf-8"), bcrypt.gensalt())

        user1 = User(username=reg_username, password=hashed_password, email=email)
        db.session.add(user1)
        db.session.commit()

        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/name', methods=['POST', 'GET'])
def name():
    if request.method == "POST":
        person_name = request.form['name']
        r_gender = requests.get(f'https://api.genderize.io/?name={person_name}').json()
        r_age = requests.get(f"https://api.agify.io?name={person_name}").json()

        p_name = r_gender['name']
        sex = r_gender['gender']
        age = r_age['age']
        probability = r_gender['probability']
        count = r_gender['count']
        person_info = [p_name, sex, age, probability, count]

        if Name.query.filter_by(name=p_name).first() is not None:
            return redirect(url_for('/database'))

        name1 = Name(name=p_name, gender=sex, age=age, probability=probability, count=count)

        db.session.add(name1)
        db.session.commit()


        all_info = Name.query.all()
        return render_template('name.html', all_info=all_info)

    all_info = Name.query.all()
    return render_template('name.html', all_info=all_info)


app.add_url_rule('/database', '/database')
@app.endpoint('/database')
def database():
    all_names = Name.query.all()
    return render_template('database.html', all_names=all_names)


# @app.route('/database')
# def database():
#     all_names = Name.query.all()
#     return render_template('database.html', all_names=all_names)


@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('error.html'), 404


if __name__ == '__main__':
    app.run(debug=True)