#!/usr/bin/env python3
"""
Copy generated static files into the invest/ folder for GitHub/Cloudflare Pages deployment.
Run after generate_dashboard.py, generate_news.py, and generate_reports.py.
"""
import os, shutil, re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INVEST_DIR = os.path.join(BASE_DIR, "invest")
DASHBOARD_SRC = os.path.join(BASE_DIR, "AI_Datacenter_Power_Landscape.html")
NEWS_SRC = os.path.join(BASE_DIR, "morning-news")
REPORTS_SRC = os.path.join(BASE_DIR, "reports")

def deploy():
    # Ensure invest/ dirs exist
    os.makedirs(os.path.join(INVEST_DIR, "morning-news"), exist_ok=True)
    os.makedirs(os.path.join(INVEST_DIR, "reports"), exist_ok=True)

    # 1. Copy dashboard as index.html
    shutil.copy2(DASHBOARD_SRC, os.path.join(INVEST_DIR, "index.html"))
    print(f"  Copied dashboard -> invest/index.html")

    # 2. Copy all morning news HTML files
    count = 0
    if os.path.isdir(NEWS_SRC):
        for f in os.listdir(NEWS_SRC):
            if f.endswith(".html"):
                src = os.path.join(NEWS_SRC, f)
                dst = os.path.join(INVEST_DIR, "morning-news", f)
                shutil.copy2(src, dst)
                count += 1
                # Fix back-link to dashboard
                with open(dst, "r", encoding="utf-8") as fh:
                    content = fh.read()
                content = content.replace(
                    "../AI_Datacenter_Power_Landscape.html",
                    "../index.html"
                )
                with open(dst, "w", encoding="utf-8") as fh:
                    fh.write(content)
    print(f"  Copied {count} morning news briefs -> invest/morning-news/")

    # 3. Copy all company report HTML files
    count = 0
    if os.path.isdir(REPORTS_SRC):
        for f in os.listdir(REPORTS_SRC):
            if f.endswith(".html"):
                shutil.copy2(os.path.join(REPORTS_SRC, f), os.path.join(INVEST_DIR, "reports", f))
                count += 1
    print(f"  Copied {count} company reports -> invest/reports/")

    total = sum(len(files) for _, _, files in os.walk(INVEST_DIR))
    print(f"\ninvest/ ready for deployment: {total} files")

if __name__ == "__main__":
    deploy()
