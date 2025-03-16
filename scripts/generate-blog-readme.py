import re
import requests
import urllib.parse
from bs4 import BeautifulSoup
import feedparser
import os
import json

from html2image import Html2Image
from google.analytics.data import BetaAnalyticsDataClient
from google.analytics.data import RunReportRequest, DateRange, Metric

BLOG_URL = "https://youngsu5582.life"
BLOG_DOMAIN = "youngsu5582.life"

POST_URL = "https://youngsu5582.life/feed"
POST_COUNT = 3

TAG_URL = "https://youngsu5582.life/tags/"
TAG_COUNT = 5

def build_markdown_card(posts, tags, today, total):
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

    return header + latest + tags_html

def get_post_data(url, count):
    feed = feedparser.parse(url)
    posts = []
    for entry in feed.entries[:count]:
        title = entry.title
        link = entry.link
        date_short = entry.published.split("T")[0] if "T" in entry.published else entry.published
        posts.append((title, link, date_short))
    return posts

def get_tag_data(url, count):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    tag_divs = soup.select("#tags div")
    tags = []
    for div in tag_divs:
        a_tag = div.select_one("a.tag")
        if not a_tag:
            continue
        tag_name = a_tag.contents[0].strip()
        count_span = a_tag.select_one("span.text-muted")
        if count_span:
            tag_count = int(count_span.get_text(strip=True))
        else:
            tag_count = 0
        tags.append((tag_name, tag_count))

    tags.sort(key=lambda x: x[1], reverse=True)
    return tags[:count]

def get_today_visitors():
    service_account_json = os.environ.get("GA_SERVICE_ACCOUNT_JSON", "")
    property_id = os.environ.get("GA_PROPERTY_ID","")
    if not service_account_json:
        return 0
    credentials_info = json.loads(service_account_json)
    client = BetaAnalyticsDataClient.from_service_account_info(credentials_info)
    request = RunReportRequest(
        property=property_id,
        metrics=[Metric(name="activeUsers")],
        date_ranges=[DateRange(start_date="today", end_date="today")],
    )
    response = client.run_report(request)
    if response.rows:
        return int(response.rows[0].metric_values[0].value)
    return 0

def get_total_visitors():
    service_account_json = os.environ.get("GA_SERVICE_ACCOUNT_JSON", "")
    property_id = os.environ.get("GA_PROPERTY_ID","")
    if not service_account_json:
        return 0
    
    credentials_info = json.loads(service_account_json)

    client = BetaAnalyticsDataClient.from_service_account_info(credentials_info)
    request = RunReportRequest(
        property=property_id,
        metrics=[Metric(name="activeUsers")],
        date_ranges=[DateRange(start_date="2025-01-01", end_date="today")],
    )
    response = client.run_report(request)
    if response.rows:
        return int(response.rows[0].metric_values[0].value)
    return 0

if __name__ == "__main__":
    posts = get_post_data(POST_URL, POST_COUNT)
    tags = get_tag_data(TAG_URL, TAG_COUNT)
    ga_today_users = get_today_visitors()
    ga_total_users = get_total_visitors()

    md = build_markdown_card(posts, tags, ga_today_users, ga_total_users)
    print(md)
