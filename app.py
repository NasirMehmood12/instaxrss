from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
import os

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Required for session management

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://instaxrss_user:QGBb5ALqiBraZtjt1c1zoifa4Kf4G1Tu@dpg-cv7sqcqj1k6c739htp00-a.oregon-postgres.render.com/instaxrss")

# Hardcoded username and password
USERNAME = "IMM"
PASSWORD = "imm@geotv"

def get_instagram_links():
    """Fetch Instagram links from the database, including timestamps."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT page_name, link, timestamp AT TIME ZONE 'Asia/Karachi' FROM instagram_links ORDER BY timestamp DESC")
        data = cursor.fetchall()
        
        results = [
            {"page_name": row[0], "link": row[1], "timestamp": row[2].strftime('%Y-%m-%d %H:%M:%S') if row[2] else None}
            for row in data
        ]

        cursor.close()
        conn.close()
        return results  
    except Exception as e:
        print(f"Error fetching Instagram links: {e}")
        return []

def get_fb_links():
    """Fetch Facebook links from the database, including timestamps."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute('SELECT link, timestamp, page_name FROM fb_links ORDER BY timestamp DESC')
        data = cursor.fetchall()
        
        results = [
            {"link": row[0], "page_name": row[2], "timestamp": row[1] if row[1] else None}
            for row in data
        ]

        cursor.close()
        conn.close()
        return results  
    except Exception as e:
        print(f"Error fetching Facebook links: {e}")
        return []

@app.route("/links")
def index():
    """Show links only if logged in"""
    if "user" not in session:
        return redirect(url_for("login"))  

    instagram_links = get_instagram_links()
    fb_links = get_fb_links()

    instagram_pages = list(set([link["page_name"] for link in instagram_links]))  
    facebook_pages = list(set([link["page_name"] for link in fb_links]))
   
    return render_template("index.html", 
                           instagram_links=instagram_links, 
                           fb_links=fb_links, 
                           instagram_pages=instagram_pages, 
                           facebook_pages=facebook_pages)

@app.route("/rss")
def rss_page():
    """Show RSS links"""
    if "user" not in session:
        return redirect(url_for("login"))

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT country, category, title, link FROM rss_links ")
        rss_links = cursor.fetchall()
        cursor.close()
        conn.close()

        rss_data = [
            {"country": row[0], "category": row[1], "title": row[2], "link": row[3]}
            for row in rss_links
        ]

        countries = list(set([link["country"] for link in rss_data]))
        categories = list(set([link["category"] for link in rss_data]))

        return render_template("rss.html", rss_links=rss_data, countries=countries, categories=categories)
    except Exception as e:
        print(f"Error fetching RSS links: {e}")
        return redirect(url_for("index"))


@app.route("/rrss")
def rrss_page():
    """Show RRSS links"""
    if "user" not in session:
        return redirect(url_for("login"))

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT channel, title, link, pubDate FROM rrss_links ORDER BY pubdate DESC")
        rrss_links = cursor.fetchall()
        cursor.close()
        conn.close()

        rrss_data = [
            {"channel": row[0], "title": row[1], "link": row[2], "pubDate": row[3]}
            for row in rrss_links
        ]

        channels = list(set([link["channel"] for link in rrss_data]))

        return render_template("rrss.html", rrss_links=rrss_data, channels=channels)
    except Exception as e:
        print(f"Error fetching RRSS links: {e}")
        return redirect(url_for("index"))



@app.route("/", methods=["GET", "POST"])
def login():
    """Login Page"""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == USERNAME and password == PASSWORD:
            session["user"] = username  # Store user session
            return redirect(url_for("index"))  # Redirect to links page
        else:
            return render_template("login.html", error="Invalid credentials")
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    """Logout and clear session"""
    session.pop("user", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)




