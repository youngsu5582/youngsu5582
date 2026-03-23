import requests
import urllib.parse
import os
import json

from google.analytics.data import BetaAnalyticsDataClient
from google.analytics.data import RunReportRequest, DateRange, Metric

BLOG_URL = "https://youngsu5582.today"
BLOG_DOMAIN = "youngsu5582.today"

STATS_URL = "https://youngsu5582.today/api/stats"
POST_COUNT = 3
NOTE_COUNT = 3
TAG_COUNT = 5

def build_markdown_card(posts, notes, tags, today, total):
    # Header + Visitors
    header = f"""
<table cellpadding="8" cellspacing="0" style="border:1px solid #87CEFA; border-radius:8px; width:100%; max-width:600px; font-family:sans-serif;">
  <tr style="background:#F0F8FF;">
    <td style="text-align:center; vertical-align:middle; border-bottom:1px solid #87CEFA;">
      <a href="{BLOG_URL}">
        <img src="https://img.shields.io/badge/Blog-{BLOG_DOMAIN}-87CEFA?style=flat-square"
             alt="Blog"
             style="display:block; margin:0 auto;" />
      </a>
    </td>
    <td style="text-align:center; vertical-align:middle; border-bottom:1px solid #87CEFA; font-weight:bold;">
      Yesterday: <strong>{today}</strong> | Total: <strong>{total}</strong>
    </td>
  </tr>"""

    # Latest Posts
    posts_rows = "".join(f"""
        <tr>
          <td align="center"><a href="{link}">{title}</a></td>
          <td align="center">{date}</td>
        </tr>""" for title, link, date in posts)

    latest = f"""
  <tr>
    <td colspan="2" style="padding-top:12px;">
      <strong>📝 Latest Posts</strong>
      <table cellpadding="6" cellspacing="0" style="width:100%; margin-top:8px; border-collapse:collapse;">
        <tr style="background:#AAD1E7;">
          <th align="center">Title</th>
          <th align="center">Date</th>
        </tr>{posts_rows}
      </table>
    </td>
  </tr>"""

    # Recent Notes
    notes_rows = "".join(f"""
        <tr>
          <td align="center"><a href="{link}">{title}</a></td>
          <td align="center">{' · '.join(t for t in note_tags[:2])}</td>
          <td align="center">{date}</td>
        </tr>""" for title, link, date, note_tags in notes)

    notes_html = f"""
  <tr>
    <td colspan="2" style="padding-top:12px;">
      <strong>📓 Recent Notes</strong>
      <table cellpadding="6" cellspacing="0" style="width:100%; margin-top:8px; border-collapse:collapse;">
        <tr style="background:#AAD1E7;">
          <th align="center">Title</th>
          <th align="center">Tags</th>
          <th align="center">Date</th>
        </tr>{notes_rows}
      </table>
    </td>
  </tr>"""

    # Top Tags
    badges = " ".join(
        f'<a href="{BLOG_URL}/tags/{urllib.parse.quote(name)}/"><img src="https://img.shields.io/badge/{urllib.parse.quote(name)}%20%28{cnt}%29-87CEFA?style=flat-square" alt="{name}"/></a>'
        for name, cnt in tags
    )

    tags_html = f"""
  <tr>
    <td colspan="2" style="padding-top:14px;">
      <strong>🔖 Top Tags</strong><br/>
      {badges}
    </td>
  </tr>
</table>"""

    return header + latest + notes_html + tags_html

def get_blog_stats(post_count, note_count, tag_count):
    resp = requests.get(STATS_URL, params={"posts": post_count, "notes": note_count, "tags": tag_count})
    data = resp.json()
    posts = [(p["title"], p["link"], p["date"].split("T")[0]) for p in data["posts"]]
    notes = [(n["title"], n["link"], n["date"].split("T")[0], n.get("tags", [])) for n in data["notes"]]
    tags = [(t["name"], t["count"]) for t in data["tags"]]
    return posts, notes, tags

def get_ga_credentials():
    """Fetches GA credentials from env var or local file."""
    service_account_json_env = os.environ.get("GA_SERVICE_ACCOUNT_JSON")
    if service_account_json_env:
        return json.loads(service_account_json_env)
    try:
        with open('ga_service_account.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def get_ga_property_id():
    """Fetches the GA Property ID from env var or local file."""
    prop_id = os.environ.get("GA_PROPERTY_ID")
    if prop_id:
        return prop_id
    try:
        with open('ga_property_id.txt', 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def get_today_visitors():
    property_id = get_ga_property_id()
    credentials_info = get_ga_credentials()

    if not property_id or not credentials_info:
        print("Error: GA credentials or Property ID not found.")
        return 0

    client = BetaAnalyticsDataClient.from_service_account_info(credentials_info)
    request = RunReportRequest(
        property=f"properties/{property_id}",
        metrics=[Metric(name="activeUsers")],
        date_ranges=[DateRange(start_date="today", end_date="today")],
    )
    response = client.run_report(request)
    if response.rows:
        return int(response.rows[0].metric_values[0].value)
    return 0

def get_total_visitors():
    property_id = get_ga_property_id()
    credentials_info = get_ga_credentials()

    if not property_id or not credentials_info:
        print("Error: GA credentials or Property ID not found.")
        return 0

    client = BetaAnalyticsDataClient.from_service_account_info(credentials_info)
    request = RunReportRequest(
        property=f"properties/{property_id}",
        metrics=[Metric(name="totalUsers")],
        date_ranges=[DateRange(start_date="2020-01-01", end_date="today")],
    )
    response = client.run_report(request)
    if response.rows:
        return int(response.rows[0].metric_values[0].value)
    return 0

if __name__ == "__main__":
    posts, notes, tags = get_blog_stats(POST_COUNT, NOTE_COUNT, TAG_COUNT)
    ga_today_users = get_today_visitors()
    ga_total_users = get_total_visitors()
    md = build_markdown_card(posts, notes, tags, ga_today_users, ga_total_users)
    print(md)
