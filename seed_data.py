"""Seed the library with 12 authors and 12 books via the running app's HTTP routes."""

import re
import sys
import urllib.parse
import urllib.request

BASE_URL = (
    sys.argv[1]
    if len(sys.argv) > 1
    else "https://minusisabel-burgergordon-5002.codio.io"
)

AUTHORS: list[dict[str, str]] = [
    {
        "name": "George Orwell",
        "birth_date": "1903-06-25",
        "date_of_death": "1950-01-21",
    },
    {
        "name": "Agatha Christie",
        "birth_date": "1890-09-15",
        "date_of_death": "1976-01-12",
    },
    {
        "name": "J.R.R. Tolkien",
        "birth_date": "1892-01-03",
        "date_of_death": "1973-09-02",
    },
    {
        "name": "Jane Austen",
        "birth_date": "1775-12-16",
        "date_of_death": "1817-07-18",
    },
    {
        "name": "Mark Twain",
        "birth_date": "1835-11-30",
        "date_of_death": "1910-04-21",
    },
    {
        "name": "Virginia Woolf",
        "birth_date": "1882-01-25",
        "date_of_death": "1941-03-28",
    },
    {
        "name": "Ernest Hemingway",
        "birth_date": "1899-07-21",
        "date_of_death": "1961-07-02",
    },
    {
        "name": "Franz Kafka",
        "birth_date": "1883-07-03",
        "date_of_death": "1924-06-03",
    },
    {
        "name": "Toni Morrison",
        "birth_date": "1931-02-18",
        "date_of_death": "2019-08-05",
    },
    {
        "name": "Haruki Murakami",
        "birth_date": "1949-01-12",
    },
    {
        "name": "Aurélien Géron",
    },
    {
        "name": "Ian Goodfellow",
    },
]

BOOKS: list[dict[str, str]] = [
    {
        "isbn": "9780451524935",
        "title": "1984",
        "publication_year": "1949",
        "author": "George Orwell",
    },
    {
        "isbn": "9780062073488",
        "title": "Murder on the Orient Express",
        "publication_year": "1934",
        "author": "Agatha Christie",
    },
    {
        "isbn": "9780618640157",
        "title": "The Lord of the Rings",
        "publication_year": "1954",
        "author": "J.R.R. Tolkien",
    },
    {
        "isbn": "9780141439518",
        "title": "Pride and Prejudice",
        "publication_year": "1813",
        "author": "Jane Austen",
    },
    {
        "isbn": "9780486280615",
        "title": "The Adventures of Huckleberry Finn",
        "publication_year": "1884",
        "author": "Mark Twain",
    },
    {
        "isbn": "9780156907392",
        "title": "Mrs Dalloway",
        "publication_year": "1925",
        "author": "Virginia Woolf",
    },
    {
        "isbn": "9780684801223",
        "title": "The Old Man and the Sea",
        "publication_year": "1952",
        "author": "Ernest Hemingway",
    },
    {
        "isbn": "9780805209990",
        "title": "The Trial",
        "publication_year": "1925",
        "author": "Franz Kafka",
    },
    {
        "isbn": "9781400033423",
        "title": "Beloved",
        "publication_year": "1987",
        "author": "Toni Morrison",
    },
    {
        "isbn": "9780375704024",
        "title": "Norwegian Wood",
        "publication_year": "1987",
        "author": "Haruki Murakami",
    },
    {
        "isbn": "979-8341607989",
        "title": "Hands-On Machine Learning with Scikit-Learn and PyTorch",
        "publication_year": "2025",
        "author": "Aurélien Géron",
    },
    {
        "isbn": "978-0262035613",
        "title": "Deep Learning",
        "publication_year": "2016",
        "author": "Ian Goodfellow",
    },
]


def post_form(path: str, data: dict[str, str]) -> str:
    """Submit a form to the running app with a POST request.

    Parameters
    ----------
    path : str
        Route to submit to, for example ``"/add_author"``.
    data : dict[str, str]
        Form fields, sent as ``application/x-www-form-urlencoded``.

    Returns
    -------
    str
        The HTML of the response page.
    """
    encoded: bytes = urllib.parse.urlencode(data).encode()
    request = urllib.request.Request(f"{BASE_URL}{path}", data=encoded, method="POST")
    with urllib.request.urlopen(request) as response:
        return response.read().decode()


def get(path: str) -> str:
    """Fetch a page from the running app.

    Parameters
    ----------
    path : str
        Route to fetch, for example ``"/add_book"``.

    Returns
    -------
    str
        The HTML of the response page.
    """
    with urllib.request.urlopen(f"{BASE_URL}{path}") as response:
        return response.read().decode()


def fetch_author_ids() -> dict[str, str]:
    """Read the author IDs back out of the add-book page.

    IDs are assigned by the database, so they are unknown until the authors
    have been created. The add-book form lists every author in a dropdown,
    which pairs each name with its ID.

    Returns
    -------
    dict[str, str]
        Author name mapped to author ID, for every author in the dropdown.
    """
    options: list[tuple[str, str]] = re.findall(
        r'<option value="(\d+)">([^<]+)</option>', get("/add_book")
    )
    return {name.strip(): author_id for author_id, name in options}


def main() -> None:
    """Create every author in ``AUTHORS``, then every book in ``BOOKS``."""
    for author in AUTHORS:
        post_form("/add_author", author)
    print(f"Added {len(AUTHORS)} authors.")

    name_to_id: dict[str, str] = fetch_author_ids()

    for book in BOOKS:
        post_form(
            "/add_book",
            {
                "isbn": book["isbn"],
                "title": book["title"],
                "publication_year": book["publication_year"],
                "author_id": name_to_id[book["author"]],
            },
        )
    print(f"Added {len(BOOKS)} books.")


if __name__ == "__main__":
    main()
