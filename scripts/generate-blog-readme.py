import requests

BLOG_URL = "https://youngsu5582.today"
STATS_URL = "https://youngsu5582.today/api/stats"
POST_COUNT = 3
NOTE_COUNT = 3


def format_date(date):
    """Converts YYYY-MM-DD to a compact README date."""
    year, month, day = date.split("-")
    return f"{year[2:]}.{month}.{day}"


def build_markdown_card(posts, notes):
    posts_md = "\n".join(
        f"- [{title}]({link}) · {format_date(date)}"
        for title, link, date in posts
    )

    notes_md = "\n".join(
        f"- [{title}]({link}) · {', '.join(note_tags[:2])} · {format_date(date)}"
        for title, link, date, note_tags in notes
    )

    return f"""[Blog]({BLOG_URL})

**Latest Posts**
{posts_md}

**Recent Notes**
{notes_md}"""


def get_blog_stats(post_count, note_count):
    resp = requests.get(STATS_URL, params={"posts": post_count, "notes": note_count})
    resp.raise_for_status()
    data = resp.json()
    posts = [(p["title"], p["link"], p["date"].split("T")[0]) for p in data["posts"]]
    notes = [(n["title"], n["link"], n["date"].split("T")[0], n.get("tags", [])) for n in data["notes"]]
    return posts, notes


if __name__ == "__main__":
    posts, notes = get_blog_stats(POST_COUNT, NOTE_COUNT)
    md = build_markdown_card(posts, notes)
    print(md)
