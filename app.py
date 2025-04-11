from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import random
import re
from transformers import pipeline

app = Flask(__name__)
app.secret_key = 'test'

DATA_FILE = 'data.txt'

#AI MODEL
generator = pipeline("text-generation", model="gpt2")

def generate_password():
    letters = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
    numbers = list("0123456789")
    symbols = list("!#$%&()*+")
    password_letters = [random.choice(letters) for _ in range(random.randint(8, 10))]
    password_numbers = [random.choice(numbers) for _ in range(random.randint(2, 4))]
    password_symbols = [random.choice(symbols) for _ in range(random.randint(2, 4))]
    password_list = password_letters + password_numbers + password_symbols
    random.shuffle(password_list)
    return ''.join(password_list)

def check_password_strength(password):
    score = 0
    if len(password) >= 12:
        score += 1
    if any(char.isdigit() for char in password):
        score += 1
    if any(char.isupper() for char in password):
        score += 1
    if any(char.islower() for char in password):
        score += 1
    if any(char in "!#$%&()*+" for char in password):
        score += 1

    if score >= 4:
        return "Strong"
    elif score == 3:
        return "Moderate"
    else:
        return "Weak"

# Make the password "strong" if it isn't already
def enhance_password(password):
    letters = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
    numbers = list("0123456789")
    symbols = list("!#$%&()*+")
    while check_password_strength(password) != "Strong":
        password += random.choice(letters + numbers + symbols)
    return password

def generate_password_gpt(website, email):
    # first three letters of the website name for prompt purposes
    abbreviation = ''.join(filter(str.isalnum, website))[:3].upper()
    
    prompt = (
        f"Generate a secure, memorable, and unique password for website '{website}' "
        f"with username/email '{email}'. The password should be 12 to 16 characters long, contain at least one uppercase letter, one lowercase letter, one digit, and one special character from !#$%&()*+. "
        f"Also, include the abbreviation '{abbreviation}' somewhere in the password to make it contextually related. "
        f"Return only the password:"
    )
    
    #prompt result
    result = generator(prompt, max_length=len(prompt) + 40, num_return_sequences=1, do_sample=True, temperature=0.7)
    generated_text = result[0]['generated_text']
    generated_part = generated_text[len(prompt):].strip()
    match = re.search(r'[A-Za-z0-9!#$%&()*+]{12,16}', generated_part)
    if match:
        password = match.group(0)
    else:
        #error handling if password isn't generated
        password = generate_password()
    
    #force abbreviation to the output
    if abbreviation not in password:
        pos = random.randint(0, len(password))
        password = password[:pos] + abbreviation + password[pos:]
        if len(password) > 16:
            password = password[:16]
    
    # ENHANCE!
    password = enhance_password(password)
    
    if len(password) > 16:
        password = password[:16]
    elif len(password) < 12:
        while len(password) < 12:
            password += random.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!#$%&()*+")
    
    return password

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['GET'])
def generate():
    password = generate_password()
    return jsonify({'password': password})

@app.route('/generate_gpt', methods=['POST'])
def generate_gpt():
    data = request.get_json()
    website = data.get("website", "")
    email = data.get("email", "")
    if website and email:
        password = generate_password_gpt(website, email)
    else:
        password = generate_password()
    return jsonify({'password': password})

@app.route('/strength_check', methods=['POST'])
def strength_check():
    data = request.get_json()
    password = data.get("password", "")
    strength = check_password_strength(password)
    return jsonify({"strength": strength})

@app.route('/save', methods=['POST'])
def save():
    website = request.form.get('website')
    email = request.form.get('email')
    password = request.form.get('password')

    if not website or not password:
        flash("Please make sure you haven't left any fields empty.")
        return redirect(url_for('index'))

    with open(DATA_FILE, 'a') as file:
        file.write(f"{website} | {email} | {password}\n")

    flash("Data saved successfully!")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
