import re, os, sqlite3
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY_pedagogyOS"))

def scene_setup(characters, setting):
    prompt = f"""
    You are generating a short, absurdly funny script, which is part of a series called “Insane Encounters” 
    Each day, users vote for 4–5 characters, and the winning ones appear in this scene.

    TASK:
    Write a dialogue under 10 lines where the given characters meet in a hilariously random location. Adults-only locations are allowed. 
    Keep the tone absurd, fast-paced, and self-aware — like a fever dream sitcom mixed with political satire. 
    Objects, food, or furniture in the scene may speak or move. 
    Add very brief stage directions if they enhance the chaos.

    Insert 4–6 blanks for users to fill (Mad Libs style), labeled clearly with ALL CAPS placeholders.
    Only these 16 general libs are allowed: CHARACTER, THING, PLACE, STUFF, ACTION, SPEECH, VIBE, SOUND, POWER, TIME, REF, QUANTITY, NAME, EVENT, RELATION, SPOT

    RULES:
    - Set up the location and time in one-line.
    - Jump straight into the funny part — no setup paragraph.
    - End with a punchline or unexpected comment from either one of the main characters or inanimate object or side characters in the scene.
    - Keep it under 8–10 lines total.
    - No moral or explanation; just pure absurd humor.
    - Output only the dialogue script (no intro text).
    - Have at least one paragraph separation for readability and maximum humor impact.

    EXAMPLE:
    LA HOOTERS – MIDNIGHT

    Trump: Best [THING]. Everyone says so. Tremendous [THING].  
    Elon: They’d be better if they self-[ACTION].  
    Landa: I prefer my [STUFF]… interrogated.  
    Forrest: I just wanted some [STUFF].  
    Kanye: Who ordered the [STUFF]?  
    Waitress: Sir, that’s ranch.  
    Kanye: Not anymore.  
    Chair: I’m leaving this timeline.
    Landa(sipping beer): Ja, smart chair.

    TODAY's SETUP:
    Characters: {characters}
    Location & Time: {setting}
    """

    resp = client.responses.create(
        model="gpt-4o",
        temperature=0.7,
        input=prompt,
    )

    with open('story.txt','w',encoding='UTF-8') as f:
        f.write(resp.output_text)

def prepare_html():
    with open('story.txt', 'r', encoding='utf-8') as f:
        text = f.read()

    # Define libs and construct pattern safely
    libs = ["character", "thing", "place", "stuff", "action", "speech", "vibe",
            "sound", "power", "time", "ref", "quantity", "name", "event",
            "relation", "spot"]

    # Match placeholders like [CHARACTER], [THING], etc.
    pattern = r"\[(" + "|".join(lib.upper() for lib in libs) + r")\]"

    new = ""
    last = 0
    iter = 0
    fillers = []

    # Iterate through each match
    for match in re.finditer(pattern, text):
        start, end = match.span()
        placeholder = match.group(1).lower()   # convert matched placeholder to lowercase (without brackets)
        fillers.append(placeholder)

        # Append the text before match and then the input tag
        new += text[last:start]
        new += f'<input name="filler{iter}" type="text" placeholder="{placeholder}" maxlength="60">'
        last = end
        iter += 1

    # Append any remaining text
    new += text[last:]

    with open('story_form_ready.txt', 'w', encoding='utf-8') as f:
        f.write(new)

def quality(response):
    if 'insane' in response: return  1
    if 'mid'    in response: return  0
    if 'shit'   in response: return -1

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

def main():
    scene_setup('Pope, Putin, Xi, Trump and Kanye','LA Strip Club at 3 AM')
    prepare_html()

if __name__=="__main__":
    main()