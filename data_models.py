from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Author(db.Model):
    __tablename__: str = "author"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    birth_date = db.Column(db.Date)
    date_of_death = db.Column(db.Date, nullable=True)
    books = db.relationship("Book", back_populates="author")

    def __repr__(self):
        return (
            f"Author(id={self.id}, name={self.name!r}, "
            f"birth_date={self.birth_date}, date_of_death={self.date_of_death})"
        )

    def __str__(self):
        return f"{self.name}"


class Book(db.Model):
    __tablename__: str = "book"
    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String, nullable=False, unique=True)
    title = db.Column(db.String, nullable=False)
    publication_year = db.Column(db.Integer)
    author_id = db.Column(db.Integer, db.ForeignKey("author.id"), nullable=False)
    author = db.relationship("Author", back_populates="books")

    def __repr__(self) -> str:
        return f"Book(id={self.id}, title={self.title!r})"

    def __str__(self) -> str:
        return f"{self.title}"
