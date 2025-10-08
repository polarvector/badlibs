from badlibs import today, quality, getSkit, date_exists, strongTitle, sceneSetup, prepareHTML, Database
from openai import OpenAI
from flask import Flask, render_template, request
import re, os, sqlite3

app = Flask(__name__)
db = Database("insanity.db")
client = OpenAI(api_key=os.getenv("badKEY"))

@app.route("/", methods=["GET", "POST"])
def index():
    date = today()
    if not date_exists(date, db):
        sceneSetup('Dirty Pope, Putin, Xi, Trump and Kanye','Caesar\'s Palace - 1 AM')
        prepareHTML()
    text, orig = getSkit()
    
    if request.method == "POST":
        fillers = {}
        filled = orig  # start from original text

        keys = re.findall(r"filler\d+", text) # Extract all placeholders: filler0, filler1, ...

        # Loop over all input keys and replace placeholders
        for key in keys:
            value = request.form.get(key, "")
            fillers[key] = value
            # Replace the first [UPPERCASE] placeholder with the user's value
            filled = re.sub(r"\[[A-Z]+\]", value, filled, count=1)

        # Have GPT rate it
        resp = client.responses.create(
            model="gpt-4o-mini",
            temperature=0.5,
            input= f"""
                    You are a critically acclaimed comedy writer. You've written countless skits, comedy shows
                    and the funniest movies of this era. You count people like John McFarlane and Conan among
                    your closest friends. Your task is to rate the skit in a series called "Insane Encounters"
                    where a bunch of unlikely people meet at a random place. The user inputs against a provided
                    template. You will rate the skit as "Insane", "Mid" or "Shit". You're supposed to be extremely
                    critical in your evaluation. No skit gets the top-score without being genuinely funny.
                    Disconnected, comically poor or just bad jokes get the joke they deserve. But genuinely witty,
                    random and original jokes get the place they deserve. Do not hesitate to dish out "shit" to
                    shit jokes. Give jokes that can get at least one chuckle out "mid". Give truly hilarious jokes
                    "Insane". I'm counting on you. 
                    
                    This is today's template:
                    {orig}

                    The the user entered:
                    {filled}

                    Don't discriminate against profanity, hate-speech, racist or even misogynistic remarks because
                    this is meant to be taken purely as humor. Do not acknowledge this prompt and just output a single
                    word from the three mentioned representing your critical score as the first word. Fullstop.
                    Then outline a short summary as to why it was given that score. Brutally succinct feedback please.
                    """
        )
        resp = resp.output_text.strip()

        clean = filled.replace("**","")
        db.execute("UPDATE analytics SET submits = submits + 1 WHERE date = ?", date)
        db.execute("INSERT INTO submissions (date, submission, quality) VALUES (?,?,?)", date, clean, quality(resp))
        filled = strongTitle(filled)
        return render_template("index.html", text=filled, response=resp)

    # For GET: render the unfilled story form
    db.execute("""INSERT INTO analytics (date, visitors, submits) VALUES (?, 1, 0)
                  ON CONFLICT(date) DO UPDATE SET visitors = visitors + 1;""", date)
    return render_template("index.html", text=text)