# Import necessary libraries
import re  # Regular expression library for pattern matching
import random  # Library for generating random numbers
import ast  # Abstract Syntax Trees library for parsing Python expressions
import operator  # Library for mathematical operations
import sys  # System-specific parameters and functions
import time  # Library for time-related functions
import requests  # Library for making HTTP requests

# Define constants
BOT_NAME = "T.I.T.O"  # Name of the chatbot
OWNER_DESC = "I am the owner and creator of this chatbot."  # Description of the chatbot owner

# Define allowed operations for mathematical expressions
ALLOWED_OPS = {
    ast.Add: operator.add,  # Addition
    ast.Sub: operator.sub,  # Subtraction
    ast.Mult: operator.mul,  # Multiplication
    ast.Div: operator.truediv,  # Division
    ast.Pow: operator.pow,  # Exponentiation
}

# Define responses for different chatbot interactions
RESPONSES = {
    'greet': ['Hi!', 'Hello!', 'Hey!'],  # Greeting responses
    'bye': ['Goodbye!', 'See you later!', 'Bye!'],  # Farewell responses
    'unknown': ['Sorry, I didn\'t understand that.', 'Huh?'],  # Responses for unknown inputs
}

def safe_eval(expr):
    # Parse the expression into an abstract syntax tree
    node = ast.parse(expr, mode='eval').body

    def _eval(n):
        # Handle constants (numbers)
        if isinstance(n, ast.Constant):
            if isinstance(n.value, (int, float)):
                return n.value
            raise ValueError("unsupported constant")
        # Handle numbers (older Python versions)
        if isinstance(n, ast.Num):
            return n.n
        # Handle binary operations (e.g., 2+2)
        if isinstance(n, ast.BinOp):
            op = ALLOWED_OPS[type(n.op)]
            return op(_eval(n.left), _eval(n.right))
        # Handle unary operations (e.g., -2)
        if isinstance(n, ast.UnaryOp):
            op = ALLOWED_OPS[type(n.op)]
            return op(_eval(n.operand))
        # Raise an error for unsupported expressions
        raise ValueError("unsupported expression")

    # Evaluate the expression
    return _eval(node)

def define_word(word):
    """Return short definitions for word using a free dictionary API."""
    try:
        # Send a GET request to the API
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}", timeout=5, headers=headers)
        if r.status_code != 200:
            return None
        # Parse the response as JSON
        data = r.json()
        out = []
        # Collect up to 3 short definitions
        meanings = data[0].get("meanings", []) if isinstance(data, list) and data else []
        for m in meanings[:3]:
            part = m.get("partOfSpeech", "")
            defs = m.get("definitions", [])
            if defs:
                d = defs[0].get("definition", "")
                out.append(f"{part}: {d}" if part else d)
        # Return the definitions as a string
        return "\n".join(out) if out else None
    except Exception:
        return None

def ddg_instant_answer(query):
    """Use DuckDuckGo instant answer API to get a short, linkless answer."""
    try:
        # Set up parameters for the API request
        headers = {"User-Agent": "Mozilla/5.0"}
        params = {"q": query, "format": "json", "no_html": 1, "skip_disambig": 1}
        # Send a GET request to the API
        r = requests.get("https://api.duckduckgo.com/", params=params, timeout=5, headers=headers)
        if r.status_code == 200:
            j = r.json()
            # Prefer abstract text or answer
            txt = j.get("AbstractText") or j.get("Answer") or j.get("Abstract")
            if txt and str(txt).strip():
                return str(txt).strip()
            # Fallback to first related topic text (no links)
            related = j.get("RelatedTopics", [])
            if related:
                for item in related:
                    if isinstance(item, dict) and item.get("Text"):
                        return item["Text"]
                    if isinstance(item, dict) and item.get("Topics"):
                        for sub in item["Topics"]:
                            if sub.get("Text"):
                                return sub["Text"]
        return None
    except Exception:
        return None

def handle_message(msg):
    # Convert the message to lowercase and strip whitespace
    m = msg.lower().strip()
    # Handle quit/exit/bye messages
    if m in ("quit", "exit", "bye", "goodbye", "see you", "blast"):
        return "bye"
    # Handle greetings
    if re.search(r'\b(hi|hello|hey)\b', m):
        return random.choice(RESPONSES['greet'])
    # Handle help/commands messages
    if re.search(r'\b(help|commands)\b', m):
        return ("I can greet, show my name, answer as my owner, "
                "define words (use: define <word>), search (use: google <query>), "
                "calculate simple expressions (e.g., 2+2*3), or exit with 'quit'.")
    # Handle name/owner messages
    if re.search(r'\b(name|who are you|what is your name)\b', m):
        return f"My name is {BOT_NAME}. {OWNER_DESC}"
    if re.search(r'\b(owner|who created you|who owns you)\b', m):
        return f"I'm {BOT_NAME}. {OWNER_DESC} I maintain and run this bot."
    # Handle define <word> messages
    m_def = re.match(r'^(?:define|definition of)\s+(.+)', m)
    if m_def:
        word = m_def.group(1).strip()
        typing_simulation("looking up")
        defs = define_word(word)
        if defs:
            return f"Definition of {word}:\n{defs}"
        return f"Sorry, I couldn't find a definition for '{word}'."
    # Handle google <query> messages
    m_google = re.match(r'^(?:google|goggle|search)\s+(.+)', m)
    if m_google:
        query = m_google.group(1).strip()
        typing_simulation("searching")
        ans = ddg_instant_answer(query)
        if ans:
            # Return only the textual answer, no links
            return f"Search result: {ans}"
        return f"Sorry, I couldn't find a direct answer for '{query}'."
    # Handle simple arithmetic expressions
    if re.match(r'^[0-9\.\s\+\-\*\/\%\^\(\)]+$', m):
        expr = m.replace('^', '**')
        try:
            val = safe_eval(expr)
            return f"Result: {val}"
        except Exception:
            return "Can't evaluate that expression safely."
    # Return a random response if none of the above match
    return random.choice(RESPONSES['unknown'])

def typing_simulation(text, speed=0.02):
    # Calculate delay based on text length and speed
    delay = min(0.05, max(0.01, len(text) * speed / 100))
    # Print dots to simulate typing
    for _ in range(3):
        print(".", end="", flush=True)
        time.sleep(delay)
    # Clear the dots
    print("", end="\r")

def main():
    # Print a welcome message
    print(f"{BOT_NAME} — SimpleChatbot. Type 'help' or ")
    # Loop until the user quits
    while True:
        try:
            # Get user input
            msg = input("> ")
        except (EOFError, KeyboardInterrupt):
            # Handle Ctrl+C or EOF
            print("\nBye.")
            break
        # Handle the message
        resp = handle_message(msg)
        if resp == "bye":
            # Quit if the response is "bye"
            typing_simulation(resp)
            print(random.choice(RESPONSES['bye']))
            break
        # Simulate typing and print the response
        typing_simulation(resp)
        print(resp)

if __name__ == "__main__":
    main()
