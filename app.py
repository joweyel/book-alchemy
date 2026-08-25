import os
from datetime import date, datetime

from flask import Flask, flash, redirect, render_template, request, url_for
from sqlalchemy.exc import IntegrityError
from werkzeug.wrappers import Response

from data_models import Author, Book, db

app = Flask(__name__)
app.secret_key = "dev-secret-key"
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"sqlite:///{os.path.join(basedir, 'data/library.sqlite')}"
)
db.init_app(app)

# with app.app_context():
#     db.create_all()


def parse_date(value: str | None) -> date | None:
    """Parse a ``YYYY-MM-DD`` string into a date, or None if empty."""
    return datetime.strptime(value, "%Y-%m-%d").date() if value else None


@app.route("/add_author", methods=["GET", "POST"])
def add_author() -> str:
    """Show the add-author form, or create a new author from it.

    On GET, renders the empty form. On POST, validates and creates
    the author from the submitted form data, re-rendering the form
    with an error or success message.

    Returns
    -------
    str
        The rendered ``add_author.html`` page.
    """
    if request.method == "POST":
        # Checks for learing or trailing whitespaces and removes them
        name: str = (request.form.get("name") or "").strip()
        try:
            birth_date: date | None = parse_date(request.form.get("birth_date"))
            date_of_death: date | None = parse_date(request.form.get("date_of_death"))
        except ValueError:
            return render_template(
                "add_author.html",
                message="Invalid date format. Please use the date picker.",
            )

        if not name:
            return render_template("add_author.html", message="Name is required.")

        # Check if Author already exists in database (case insensitive)
        if db.session.scalar(
            db.select(Author).where(db.func.lower(Author.name) == name.lower())
        ):
            return render_template(
                "add_author.html",
                message=f"An author named '{name}' already exists.",
            )

        new_author: Author = Author(
            name=name,
            birth_date=birth_date,
            date_of_death=date_of_death,
        )
        # Add author and give warning if the insert failed
        try:
            db.session.add(new_author)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return render_template(
                "add_author.html",
                message=f"An author named '{name}' already exists.",
            )
        return render_template(
            "add_author.html",
            message="Author added successfully!",
        )
    # GET case
    return render_template("add_author.html")


@app.route("/add_book", methods=["GET", "POST"])
def add_book() -> str:
    """Show the add-book form, or create a new book from it.

    On GET, renders the form with a dropdown of existing authors.
    On POST, validates and creates the book from the submitted form
    data, re-rendering the form with an error or success message.

    Returns
    -------
    str
        The rendered ``add_book.html`` page.
    """
    if request.method == "POST":
        # Additional empty string fallback and whitespace 'purge' for safety
        # + isbn-normalization
        isbn: str = (
            (request.form.get("isbn") or "").replace("-", "").replace(" ", "").strip()
        )
        title: str = (request.form.get("title") or "").strip()
        publication_year_raw: str | None = request.form.get("publication_year")
        author_id_raw: str | None = request.form.get("author_id")

        try:
            if publication_year_raw is None or author_id_raw is None:
                raise ValueError
            publication_year: int = int(publication_year_raw)
            author_id: int = int(author_id_raw)
        except ValueError:
            authors = db.session.scalars(db.select(Author)).all()
            return render_template(
                "add_book.html",
                authors=authors,
                message="Publication year and author are required.",
            )

        if not isbn or not title or not db.session.get(Author, author_id):
            authors = db.session.scalars(db.select(Author)).all()
            return render_template(
                "add_book.html",
                authors=authors,
                message="ISBN, title, and a valid author are required.",
            )

        # ISBN-Check: Is book with specified ISBN already in the database
        if db.session.scalar(db.select(Book).where(Book.isbn == isbn)):
            authors = db.session.scalars(db.select(Author)).all()
            return render_template(
                "add_book.html",
                authors=authors,
                message=f"A book with ISBN {isbn} is already in the library.",
            )

        new_book: Book = Book(
            isbn=isbn,
            title=title,
            publication_year=publication_year,
            author_id=author_id,
        )
        db.session.add(new_book)
        db.session.commit()

        authors = db.session.scalars(db.select(Author)).all()
        return render_template(
            "add_book.html",
            authors=authors,
            message="Book added successfully!",
        )
    # GET case
    authors = db.session.scalars(db.select(Author)).all()
    return render_template("add_book.html", authors=authors)


@app.route("/", methods=["GET"])
def index() -> Response:
    """Redirect the site root to the library home page."""
    return redirect(url_for("home"))


@app.route("/home", methods=["GET"])
def home() -> str:
    """Show the library, optionally filtered and sorted.

    Reads ``sort`` (``"title"`` or ``"author"``) and ``search`` from
    the query string to filter books by title/author and order the
    results.

    Returns
    -------
    str
        The rendered ``home.html`` page.
    """
    sort_by: str = request.args.get("sort", "title")
    search: str = request.args.get("search", "").strip()

    query = db.select(Book)
    if search or sort_by == "author":
        query = query.join(Author)
    if search:
        query = query.where(
            db.or_(
                Book.title.ilike(f"%{search}%"),
                Author.name.ilike(f"%{search}%"),
            )
        )

    books = db.session.scalars(
        query.order_by(Author.name if sort_by == "author" else Book.title)
    ).all()

    message: str | None = (
        f'No books found containing "{search}"' if search and not books else None
    )
    return render_template(
        "home.html",
        books=books,
        sort_by=sort_by,
        search=search,
        message=message,
    )


@app.route("/book/<int:book_id>/delete", methods=["POST"])
def delete_book(book_id: int) -> Response:
    """Delete a book, and its author too if they have no books left.

    Parameters
    ----------
    book_id : int
        ID of the book to delete.

    Returns
    -------
    Response
        Redirect response to the home page.
    """
    book: Book = db.get_or_404(Book, book_id)
    author: Author = book.author

    db.session.delete(book)
    db.session.commit()

    if not author.books:
        db.session.delete(author)
        db.session.commit()

    flash(f"Book '{book.title}' deleted successfully!")
    return redirect(url_for("home"))


@app.route("/author/<int:author_id>/delete", methods=["POST"])
def delete_author(author_id: int) -> Response:
    """Delete an author along with all of their books.

    Parameters
    ----------
    author_id : int
        ID of the author to delete.

    Returns
    -------
    Response
        Redirect response to the home page.
    """
    author: Author = db.get_or_404(Author, author_id)
    for book in list(author.books):
        db.session.delete(book)
    db.session.delete(author)
    db.session.commit()

    flash(f"Author '{author.name}' and all their books deleted successfully!")
    return redirect(url_for("home"))


@app.route("/book/<int:book_id>")
def book_detail(book_id: int) -> str:
    """Show the detail page for a single book.

    Parameters
    ----------
    book_id : int
        ID of the book to display.

    Returns
    -------
    str
        The rendered ``book_detail.html`` page.
    """
    book: Book = db.get_or_404(Book, book_id)
    return render_template("book_detail.html", book=book)


@app.route("/author/<int:author_id>")
def author_detail(author_id: int) -> str:
    """Show the detail page for a single author and their books.

    Parameters
    ----------
    author_id : int
        ID of the author to display.

    Returns
    -------
    str
        The rendered ``author_detail.html`` page.
    """
    author: Author = db.get_or_404(Author, author_id)
    return render_template("author_detail.html", author=author)


@app.errorhandler(404)
def not_found(error) -> tuple[str, int]:
    """Render a friendly page for 404 Not Found errors."""
    return render_template("error.html", code=404, message="Page not found."), 404


@app.errorhandler(500)
def server_error(error) -> tuple[str, int]:
    """Render a friendly page for 500 Internal Server errors."""
    return (
        render_template("error.html", code=500, message="Internal server error."),
        500,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
