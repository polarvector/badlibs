import re, os, sqlite3
from openai import OpenAI
from datetime import datetime, timezone

os.makedirs("story", exist_ok=True)
utc = timezone.utc
story = "story/"

def sceneSetup(characters, setting):
    client = OpenAI(api_key=os.getenv("badKEY"))
    prompt = f"""
    You are generating a short, absurdly funny script, which is part of a series called “Insane Encounters”. 
    Each day, users vote for 4–5 characters, and the winning ones appear in this scene.

    TASK:
    Write a dialogue under 10 lines where the given characters meet in a hilariously random location. Adults-only locations are allowed. 
    Keep the tone absurd, fast-paced, and self-aware — like a fever dream sitcom mixed with political satire. 
    Objects, food, or furniture in the scene may speak or move. 
    Add very brief stage directions if they enhance the chaos.

    Insert 4–6 blanks for users to fill (Mad Libs style), labeled clearly with ALL CAPS placeholders.
    Strictly, only these 16 libs are allowed: CHARACTER, THING, PLACE, STUFF, ACTION, SPEECH, VIBE, SOUND, POWER, TIME, REF, QUANTITY, NAME, EVENT, RELATION, SPOT.
    NEVER use the plural form of these libs. I said 16 STRICTLY. That means under no condition there's gonna be any more.

    RULES:
    - Set up the location and time in one line.
    - Jump straight into the funny part — no setup paragraph.
    - End with a punchline or unexpected comment from either one of the main characters or inanimate object or side characters in the scene.
    - Keep it under 8–10 lines total.
    - No moral or explanation; just pure absurd humor.
    - Output only the dialogue script (no intro text).
    - DO NOT have two newlines respectively between every single line. Only one newline tag per line. Exception is the rule below.
    - Have at least one paragraph separation in the entire joke selected for maximum humor impact.

    EXAMPLE:
    **LA Hooters – Midnight**

    Trump: Best [THING]. Everyone says so. Tremendous [THING].  
    Elon: They’d be better if they self-[ACTION].  
    Landa: I prefer my [STUFF]… interrogated.  
    Forrest: I just wanted some [STUFF].  
    Kanye: Who ordered the [STUFF]?  
    Waitress: Sir, that’s ranch.  
    Kanye: Not anymore.  
    Chair: I’m leaving this timeline.  
    Landa(sipping beer): Ja, smart chair.

    TODAY'S SETUP:
    Characters: {characters}
    Location & Time: {setting}
    """

    resp = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.7,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    with open(story + 'story.txt', 'w', encoding='utf-8') as f:
        f.write(resp.choices[0].message.content)
        
def prepareHTML():
    with open(story+'story.txt', 'r', encoding='utf-8') as f:
        text = f.read()

    # Define libs and construct pattern safely
    libs = [
        "character", "characters",
        "thing", "things",
        "place", "places",
        "stuff", "stuffs",
        "action", "actions",
        "speech", "speeches",
        "vibe", "vibes",
        "sound", "sounds",
        "power", "powers",
        "time", "times",
        "ref", "refs",
        "quantity", "quantities",
        "name", "names",
        "event", "events",
        "relation", "relations",
        "spot", "spots"
    ]

    # Pattern that matches exact placeholders like [THING] or [THINGS] — no partial overlap.
    alts = sorted({lib.upper() for lib in libs}, key=len, reverse=True)
    pattern = r"\[(" + "|".join(re.escape(w) for w in alts) + r")\]"
    
    new = ""
    last = 0
    iter = 0
    fillers = []

    for match in re.finditer(pattern, text):
        start, end = match.span()
        placeholder = match.group(1).lower()   # inner text without brackets
        fillers.append(placeholder)

        new += text[last:start]
        new += f'<input name="filler{iter}" type="text" placeholder="{placeholder}" maxlength="60">'
        last = end
        iter += 1

    new += text[last:]
    new = strongTitle(new)
    with open(story+'storyHTML.txt', 'w', encoding='utf-8') as f:
        f.write(new)

def quality(response):
    response = response.lower()
    if 'insane' in response: return  1
    elif 'mid'    in response: return  0
    elif 'shit'   in response: return -1
    else: return 0

class Database():
    def __init__(self, path="insanity.db"):
        self.path = path
    
    def execute(self, query, *params):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(query, params)

        if query.strip().lower().startswith("select"):
            rows = cur.fetchall()
            conn.close()
            return [dict(row) for row in rows]
        else:
            conn.commit()
            conn.close()
            return None

def getSkit(story="story/"):
    with open(story+'story.txt','r',encoding="utf-8") as f:
        orig = f.read()
    with open(story+'storyHTML.txt','r',encoding="utf-8") as f:
        text = f.read()
    return text, orig

def today():
    dt = datetime.now(utc)
    return dt.year*10000 + dt.month*100 + dt.day

def date_exists(date, db):
    exists = db.execute("SELECT * FROM analytics WHERE date = ?", date)
    return bool(exists)

def strongTitle(text):
    lines    = text.split("\n")
    lines[0] = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", lines[0])
    text = "\n".join(lines)
    return text

def main():
    sceneSetup('Pope, Putin, Xi, Trump and Kanye','LV Casino - 1 a.m.')
    prepareHTML()

if __name__=="__main__":
    main()