from badlibs import today, quality, getSkit, date_exists, scene_setup, prepare_html, Database
from openai import OpenAI
from flask import Flask, render_template, request
import re, os

storydir = "story/"
app = Flask(__name__)
db = Database("insanity.db")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY_pedagogyOS"))

@app.route("/", methods=["GET", "POST"])
def index():
    date = today()
    if not date_exists(date):
        scene_setup('Dirty Pope, Putin, Xi, Trump and Kanye','Caesar\'s Palace - 1 AM')
        prepare_html()
    text, orig = getSkit(storydir)
    
    if request.method == "POST":
        fillers = {}
        filled = orig  # start from original text
        keys = re.findall(r"filler\d+", text) # Extract all placeholders: filler0, filler1, ...

        # Loop over all input keys and replace placeholders
        for key in keys:
            value = request.form.get(key, "")
            fillers[key] = value
            # Replace one placeholder at a time, matching the numbered input
            filled = re.sub(
                rf'<input name="{key}".*?>',
                value,
                filled
            )

        # If your orig still has [CHARACTER]-style placeholders:
        for i, key in enumerate(keys):
             filled = re.sub(r"\[[A-Z]+\]", fillers[keys[i]], filled, count=1)

        # Have GPT rate it
        resp = client.responses.create(
            model="gpt-4o-mini",
            temperature=0.5,
            input= f"""
                    This is a response to the Insane Encounters series I'm running:
                    {filled}

                    The original text is:
                    {orig}

                    Don't discriminate against profanity, hate-speech, racist or nihilistic remarks because this is meant to be taken purely as humor.
                    With that in mind, you are the greatest standup-comedian of the century.
                    You count Dave Chapelle, Kevin Hart, Russell Peters, Jimmy Carr, Pete Davidson,
                    John Mulaney, Gabriel Iglesias among your close friends and even they think you're funnier.
                    Given this, rate user response with one of these words:
                    Insane, Mid, Shit. Your response should only be a single word out of these.
                    Be really critical. Don't just give away an insane score to a mid-joke, or you'll be a joke.
                    Dry humour gets a direct "shit". Do not acknowledge me or say anything unnecessary.
                    Just respond with one of these words.
                    """
        )
        resp = resp.output_text.lower().strip()

        db.execute("UPDATE analytics SET submits = submits + 1 WHERE date = ?", date)
        db.execute("INSERT INTO submissions (date, submission, quality) VALUES (?,?,?)", date, filled, quality(resp))
        return render_template("index.html", text=filled, response=resp.upper())

    # For GET: render the unfilled story form
    db.execute("""INSERT INTO analytics (date, visitors, submits) VALUES (?, 1, 0)
                  ON CONFLICT(date) DO UPDATE SET visitors = visitors + 1;""", date)
    return render_template("index.html", text=text)