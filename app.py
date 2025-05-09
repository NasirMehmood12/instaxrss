# from flask import Flask, render_template, request, redirect, url_for, session

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import psycopg2
import os, time

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Required for session management

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://neondb_owner:npg_7SjyKhDinEv8@ep-young-term-a5zyo5in-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require")

# Hardcoded username and password
USERNAME = "IMM"
PASSWORD = "imm@geotv"



def get_instagram_post():
    """Fetch Instagram links from the database, including timestamps."""
    try:
        start_time = time.time()
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT page_name, link, post_image, caption, timestamp AT TIME ZONE 'Asia/Karachi' FROM instagram_post ORDER BY timestamp DESC")
        data = cursor.fetchall()
        end_time = time.time()
        results = [
            {"page_name": row[0], "link": row[1],"post_image":row[2],"caption":row[3], "timestamp": row[4].strftime('%Y-%m-%d %H:%M:%S') if row[4] else None,}
            for row in data
        ]
        execution_time = end_time-start_time
        print(f"instagram db execution time {execution_time}")
        cursor.close()
        conn.close()
        
        return results  
    except Exception as e:
        print(f"Error fetching Instagram links: {e}")
        return []



# def get_fb_links():
#     """Fetch Facebook links from the database, including timestamps."""
#     try:
#         conn = psycopg2.connect(DATABASE_URL)
#         cursor = conn.cursor()
#         cursor.execute('SELECT page_name,link,timestamp,post_image FROM fb_links order by timestamp DESC')
#         data = cursor.fetchall()
        
#         results = [
#             # {"link": row[1], "page_name": row[0], "post_image": row[4], "timestamp": row[2] if row[2] else None}
#             {"link": row[1], "page_name": row[0],"post_image": row[3], "timestamp": row[2] if row[2] else None}

#             for row in data
#         ]

#         cursor.close()
#         conn.close()
#         return results  
#     except Exception as e:
#         print(f"Error fetching Facebook links: {e}")
#         return []





def get_fb_links():
    """Fetch Facebook links from the database with computed sort_value for ordering."""
    try:
        start_time=time.time()
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        query = """
            SELECT 
                page_name,
                link,
                timestamp,
                post_image,
                CASE 
                    WHEN timestamp LIKE '%h' THEN CAST(SPLIT_PART(timestamp, 'h', 1) AS INTEGER) * 60
                    WHEN timestamp LIKE '%m%' THEN CAST(SPLIT_PART(timestamp, 'm', 1) AS INTEGER)
                    ELSE 0
                END AS sort_value
            FROM fb_links
            ORDER BY sort_value ASC;
        """
        cursor.execute(query)
        data = cursor.fetchall()
        end_time=time.time()
        execution_time = end_time-start_time
        results = [
            {
                "page_name": row[0],
                "link": row[1],
                "timestamp": row[2] if row[2] else None,
                "post_image": row[3],
                "sort_value": row[4]
            }
            for row in data
        ]
        
        print(f"facebook db execution time {execution_time}")

        cursor.close()
        conn.close()
        return results
    except Exception as e:
        print(f"Error fetching Facebook links: {e}")
        return []






@app.route("/instagram")
def index():
    """Show links only if logged in"""
    if "user" not in session:
        return redirect(url_for("login"))  

    instagram_post = get_instagram_post()
    
    instagram_pages = list(set([link["page_name"] for link in instagram_post]))  
    
   
    return render_template("index.html", 
                           instagram_post=instagram_post, 
                         
                           instagram_pages=instagram_pages, 
                           )


@app.route("/facebook")
def fb():
    """Show links only if logged in"""
    if "user" not in session:
        return redirect(url_for("login"))  

    
    fb_links = get_fb_links()

      
    facebook_pages = list(set([link["page_name"] for link in fb_links]))
   
    return render_template("fb.html", 
                          
                           fb_links=fb_links, 
                        
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





@app.route("/tiktok")
def tiktok():
    """Show TikTok links"""
    if "user" not in session:
        return redirect(url_for("login"))

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        query = """
SELECT 
    page_name,
    video_link,
    img_src,
    timestamp,
    CASE 
        WHEN RIGHT(timestamp, 3) = 'ago' AND POSITION('d' IN timestamp) > 0
            THEN CAST(SPLIT_PART(REPLACE(timestamp, ' ago', ''), 'd', 1) AS INTEGER) * 1440
        WHEN RIGHT(timestamp, 3) = 'ago' AND POSITION('h' IN timestamp) > 0
            THEN CAST(SPLIT_PART(REPLACE(timestamp, ' ago', ''), 'h', 1) AS INTEGER) * 60
        WHEN RIGHT(timestamp, 3) = 'ago' AND POSITION('m' IN timestamp) > 0
            THEN CAST(SPLIT_PART(REPLACE(timestamp, ' ago', ''), 'm', 1) AS INTEGER)
        ELSE 0
    END AS sort_value
FROM tiktok_link
ORDER BY sort_value ASC;
        """
        cursor.execute(query)
        tiktok_link = cursor.fetchall()
        cursor.close()
        conn.close()

        tiktok_post = [
            {
                "page_name": row[0], 
                "video_link": row[1], 
                "img_src": row[2], 
                "post_time": row[3]  # Add post_time to the dictionary
            }
            for row in tiktok_link
        ]

        return render_template("tiktok.html", tiktok_post=tiktok_post)

    except Exception as e:
        print(f"Error fetching TikTok link: {e}")
        return redirect(url_for("tiktok"))











@app.route("/trends")
def trends_page():
    """Show RSS links"""
    if "user" not in session:
        return redirect(url_for("login"))

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("""SELECT country, category, trending_search, search_volume, change_percentage, started, status
                            FROM trending_data
                            ORDER BY 
                                CASE
                                    WHEN search_volume ILIKE '%K%' THEN CAST(REPLACE(REPLACE(search_volume, 'K', ''), '+', '') AS FLOAT) * 1000
                                ELSE CAST(REPLACE(search_volume, '+', '') AS FLOAT)
                                END DESC""")
        rss_links = cursor.fetchall()
        cursor.close()
        conn.close()

        trends = [
            {"country": row[0], "category": row[1], "trending_search": row[2], "search_volume": row[3], "change_percentage": row[4], "started": row[5], "status": row[6]}
            for row in rss_links
        ]

        countries = list(set([trend["country"] for trend in trends]))
        categories = list(set([trend["category"] for trend in trends]))

        return render_template("trends.html", trends=trends, countries=countries, categories=categories)
    except Exception as e:
        print(f"Error fetching trending data: {e}")
        return redirect(url_for("index"))















@app.route("/rrss")
def rrss_page():
    """Show RRSS links"""
    if "user" not in session:
        return redirect(url_for("login"))

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT channel, title, link, pubDate,thumbnail FROM rrss_links ORDER BY pubdate DESC")
        rrss_links = cursor.fetchall()
        cursor.close()
        conn.close()

        rrss_data = [
            {"channel": row[0], "title": row[1], "link": row[2], "pubDate": row[3],"thumbnail": row[4]}
            for row in rrss_links
        ]

        channels = list(set([link["channel"] for link in rrss_data]))

        return render_template("rrss.html", rrss_links=rrss_data, channels=channels)
    except Exception as e:
        print(f"Error fetching RRSS links: {e}")
        return redirect(url_for("index"))










# @app.get("/get_selection/")
# def get_selection():
#     card_id = request.args.get("card_id")
#     if not card_id:
#         return jsonify({"selected_options": []})  # Return empty list if no card_id

#     conn = psycopg2.connect(DATABASE_URL)
#     cursor = conn.cursor()
    
#     # Fetch all selected options for the given card_id
#     cursor.execute("SELECT selected_option FROM card_selections WHERE card_id = %s", (card_id,))
#     results = cursor.fetchall()
    
#     cursor.close()
#     conn.close()

#     # Extract names from query results and return as a list
#     selected_options = [row[0] for row in results]
#     return jsonify({"selected_options": selected_options})








# @app.route("/save_selection/", methods=["POST"])
# def save_selection():
#     try:
#         data = request.json  # Get data from JSON request
#         card_id = data.get("card_id")
#         selected_option = data.get("selected_option")

#         if not card_id or not selected_option:
#             return jsonify({"error": "Missing required fields"}), 400

#         conn = psycopg2.connect(DATABASE_URL)
#         cursor = conn.cursor()
        
#         cursor.execute("""
#             INSERT INTO card_selections (card_id, selected_option)
#             VALUES (%s, %s)
#             ON CONFLICT (card_id, selected_option)
#             DO NOTHING
#         """, (card_id, selected_option))

#         conn.commit()
#         cursor.close()
#         conn.close()

#         return jsonify({"message": "Selection saved"}), 200
#     except Exception as e:
#         print(f"Error saving selection: {e}")
#         return jsonify({"error": str(e)}), 500






@app.get("/get_selection/")
def get_selection():
    card_id = request.args.get("card_id")
    if not card_id:
        return jsonify({"selected_options": []})

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        cursor.execute("SELECT selected_option FROM card_selections WHERE card_id = %s", (card_id,))
        results = cursor.fetchall()

        cursor.close()
        conn.close()

        selected_options = [row[0] for row in results]
        return jsonify({"selected_options": selected_options})
    except Exception as e:
        print(f"Error fetching selection: {e}")
        return jsonify({"selected_options": []})


@app.route("/save_selection/", methods=["POST"])
def save_selection():
    try:
        data = request.json
        card_id = data.get("card_id")
        selected_option = data.get("selected_option")

        if not card_id or not selected_option:
            return jsonify({"error": "Missing required fields"}), 400

        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO card_selections (card_id, selected_option)
            VALUES (%s, %s)
            ON CONFLICT (card_id, selected_option)
            DO NOTHING
        """, (card_id, selected_option))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "Selection saved"}), 200
    except Exception as e:
        print(f"Error saving selection: {e}")
        return jsonify({"error": str(e)}), 500    





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




