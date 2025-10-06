from datetime import datetime
from badlibs import quality, Database
from openai import OpenAI
from flask import Flask, render_template, request
import re, os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY_pedagogyOS"))
db = Database("insanity.db")

with open("story_form_ready.txt", "r", encoding="utf-8") as f:
    text = f.read()
with open("story.txt", "r", encoding="utf-8") as f:
    orig = f.read()

date = datetime.now()
date = date.year*10000 + date.month*100 + date.day

text = text.replace("\n", "<br>")
orig = orig.replace("\n", "<br>")

# Extract all filler names like filler0, filler1, ...
keys = re.findall(r"filler\d+", text)

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        fillers = {}
        filled = orig  # start from original text

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

        db.execute("INSERT INTO submissions (date, submission, quality) VALUES (?,?,?)", date, filled, quality(resp))
        return render_template("index.html", text=filled, response=resp.upper())

    # For GET: render the unfilled story form
    return render_template("index.html", text=text)
