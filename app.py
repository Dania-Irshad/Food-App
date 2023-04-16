from flask import Flask, render_template, flash, redirect, session, g, request, url_for
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from forms import UserAddForm, LoginForm, UserEditForm
from models import db, connect_db, User
import requests

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///food-app'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = 'secret-7894@$44'
toolbar = DebugToolbarExtension(app)

connect_db(app)


##############################################################################
# User signup/login/logout

@app.before_request
def add_user_to_g():
    """If user is logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """
    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]
    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()

        except IntegrityError:
            flash('Username already taken', 'danger')
            return render_template('signup.html', form=form)

        do_login(user)

        return redirect('/')

    else:
        return render_template('signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            flash(f'Hello, {user.username}!', 'success')
            return redirect('/')

        flash('Invalid credentials.', 'danger')

    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""
    
    do_logout()
    flash("Successfully Logged out.", 'success')
    return redirect('/login')


##############################################################################
# Homepage and error pages

@app.route('/')
def homepage():
    """Display the logged in user homepage"""
    user = g.user
    if user:
        res = requests.get('https://www.themealdb.com/api/json/v1/1/categories.php')
        data = res.json()
        categories = data.get('categories')
        return render_template('home.html', user=user, categories=categories)
    else:
        return redirect('/login')

@app.errorhandler(404)
def page_not_found(e):
    """404 NOT FOUND page."""

    return render_template('404.html'), 404


##############################################################################
# Recipes

@app.route('/category/<category_name>')
def get_category(category_name):
    """Display all recipes the selected category"""
    user = g.user
    if user:
        res = requests.get(f'https://www.themealdb.com/api/json/v1/1/filter.php',
                           params={'c': category_name})
        data = res.json()
        recipes = data.get('meals')
        return render_template('category.html', user=user, recipes=recipes)
    else:
        return redirect('/login')


@app.route('/recipe/<recipe_name>')
def get_recipe(recipe_name):
    """Display the selected recipe"""
    user = g.user
    if user:
        res = requests.get(f'https://www.themealdb.com/api/json/v1/1/search.php',
                           params={'s': recipe_name})
        data = res.json()
        recipe = data.get('meals')[0]
        video_code = recipe["strYoutube"].split("=")[1]
        ingredient_dict = {}
        x = 1
        while recipe["strIngredient" + str(x)] != "" and recipe["strIngredient" + str(x)] != "null":
            ingredient_dict[recipe["strIngredient" + str(x)]] = recipe["strMeasure" + str(x)]
            x += 1
        print(ingredient_dict.items())
        return render_template('recipe.html', user=user, recipe=recipe, video_code=video_code, ingredient_dict=ingredient_dict.items())
    else:
        return redirect('/login')
    

##############################################################################
# Navbar

@app.route('/about')
def about():
    """Display the about page."""
    user = g.user
    if user:
        return render_template('about.html')
    else:
        return redirect('/login')
    
@app.route('/recipe', methods=['POST'])
def search():
    """Search a recipe"""
    user = g.user
    if user:
        search_value = request.form['s']
        return redirect(url_for('get_recipe', recipe_name=search_value))
    else:
        return redirect('/login')

@app.route('/user/<int:user_id>')
def user_profile(user_id):
    """Display user profile."""
    user = g.user
    if user:
        curr_user = User.query.get_or_404(user_id)
        if curr_user == user:
            return render_template('profile.html', user=user)
        else:
            return redirect('/')
    else:
        return redirect('/login')


##############################################################################
# Profile

@app.route('/user/<int:user_id>/edit', methods=["GET", "POST"])
def edit_profile(user_id):
    """Edit user profile."""
    user = g.user
    if user:
        curr_user = User.query.get_or_404(user_id)
        if curr_user == user:
            form = UserEditForm(obj=user)
            if form.validate_on_submit():
                if User.authenticate(user.username, form.password.data):
                    try:
                        user.username=form.username.data,
                        user.email=form.email.data,
                        user.image_url=form.image_url.data or User.image_url.default.arg
                        db.session.commit()
                    except IntegrityError:
                        flash('Username already taken', 'danger')
                        db.session.rollback()
                        return render_template('edit.html', form=form, user=user)
                    return redirect(f'/user/{user.id}')
                else:
                    flash('Wrong Password.', 'danger')
                    return render_template('edit.html', form=form, user=user)
            return render_template('edit.html', form=form, user=user)
        else:
            return redirect('/')
    else:
        return redirect('/login')
    

@app.route('/user/<int:user_id>/delete', methods=["GET", "POST"])
def delete_user(user_id):
    """Delete user"""
    user = g.user
    if user:
        curr_user = User.query.get_or_404(user_id)
        if curr_user == user:
            do_logout()
            db.session.delete(g.user)
            db.session.commit()
            return redirect('/signup')
        else:
            return redirect('/')
    else:
        return redirect('/login')
