from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired, NumberRange
import requests

'''
Red underlines? Install the required packages first: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from requirements.txt for this project.
'''
api_key = "5dbbd7b8b96e1ea61693744804babaac"
url = "https://api.themoviedb.org/3/search/movie"
image_url = "https://image.tmdb.org/t/p/w500"
find_movie_url = "https://api.themoviedb.org/3/movie/"


class EditForm(FlaskForm):
    rating = FloatField("Your Rating out of 10",[DataRequired(), NumberRange(min=0, max=10, message="from 0 to 10")])
    review = StringField("Your Review", [DataRequired()])
    submit = SubmitField("Submit")


class AddMovie(FlaskForm):
    name = StringField("Movie title", [DataRequired()])
    submit = SubmitField("Add")
    pass


class Base(DeclarativeBase):
  pass


db = SQLAlchemy(model_class=Base)


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///top_movies.db"
db.init_app(app)


class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=False, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String, nullable=True)
    img_url: Mapped[str] = mapped_column(String, nullable=False)

    def __repr__(self):
        return f'<Movie {self.title}>'


# CREATE TABLE
with app.app_context():
    db.create_all()


@app.route("/")
def home():
    all_movies = db.session.execute(db.select(Movie).order_by(Movie.rating)).scalars().all()

    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route("/edit/id=<id>", methods=["POST", "GET"])
def edit_movie(id):
    form = EditForm()
    movie = db.get_or_404(Movie, id)
    if form.validate_on_submit():
        movie.rating = form.rating.data
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", form=form, title=movie.title)


@app.route("/delete")
def delete():
    movie_id = request.args.get("id")
    movie = db.get_or_404(Movie, movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/add", methods=["POST", "GET"])
def add():
    form = AddMovie()
    if form.validate_on_submit():
        parameters = {
            "api_key": api_key,
            "query": form.name.data
        }
        response = requests.get(url, params=parameters)
        return render_template("select.html", movies=response.json()["results"])
    return render_template("add.html", form=form)


@app.route("/find")
def find_movie():
    movie_api_id = request.args.get("id")
    if movie_api_id:
        movie_api_url = f"{find_movie_url}{movie_api_id}"
        #The language parameter is optional, if you were making the website for a different audience
        #e.g. Hindi speakers then you might choose "hi-IN"
        response = requests.get(movie_api_url, params={"api_key": api_key, "language": "en-US"})
        data = response.json()
        new_movie = Movie(
            title=data["title"],
            #The data in release_date includes month and day, we will want to get rid of.
            year=data["release_date"].split("-")[0],
            img_url=f"{image_url}{data['poster_path']}",
            description=data["overview"]
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for("edit_movie", id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
