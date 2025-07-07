from flask import Flask, render_template, request
import pandas as pd
from datetime import datetime
from pulp import LpMaximize, LpProblem, LpVariable, lpSum
from flask import Flask, render_template, request, redirect, session, url_for
import secrets  # For a secure secret key

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Load and clean dataset
df = pd.read_csv("categorized_dishes.csv")
df.columns = df.columns.str.strip().str.replace(r'\s+', ' ', regex=True)
df.rename(columns={
    'Dish Name': 'dish',
    'Calories (kcal)': 'calories',
    'Protein (g)': 'protein',
    'Type': 'type'
}, inplace=True)
df['type'] = df['type'].str.strip().str.lower()

def get_targets(weight, age, gender, goal):
    gender = gender.lower()
    weight, age = float(weight), int(age)
    # Simplified BMR with average height
    bmr = 10 * weight + 6.25 * (170 if gender == "male" else 160) - 5 * age + (5 if gender == "male" else -161)
    calories = bmr * 1.4 + (-300 if goal=="loss" else 300 if goal=="gain" else 0)
    protein = weight * (1.5 if goal=="gain" else 1.2 if goal=="maintain" else 1.0)
    return round(calories,2), round(protein,2)
import random

def build_optimized_meal(cal_limit, protein_limit, available_df, max_dishes=4):
    df_av = available_df.reset_index(drop=True)
    n = len(df_av)
    model = LpProblem("MealPlan", LpMaximize)
    x = [LpVariable(f"x{i}", cat="Binary") for i in range(n)]

    # Introduce slight randomness to the objective to get different solutions
    random_weights = [random.uniform(0.9, 1.1) for _ in range(n)]

    model += lpSum(df_av.loc[i, 'protein'] * random_weights[i] * x[i] for i in range(n)), "RandomizedProteinMax"

    model += lpSum(df_av.loc[i, 'calories'] * x[i] for i in range(n)) <= cal_limit + 100
    model += lpSum(df_av.loc[i, 'calories'] * x[i] for i in range(n)) >= cal_limit - 50
    model += lpSum(df_av.loc[i, 'protein'] * x[i] for i in range(n)) >= protein_limit - 5
    model += lpSum(x[i] for i in range(n)) <= max_dishes

    soup_salad = [i for i in range(n) if df_av.loc[i, 'Category'].lower() in ['soup', 'salad']]
    bev_des = [i for i in range(n) if df_av.loc[i, 'Category'].lower() in ['beverage', 'dessert']]
    if soup_salad:
        model += lpSum(x[i] for i in soup_salad) <= 1
    if bev_des:
        model += lpSum(x[i] for i in bev_des) <= 1

    model.solve()
    chosen = [i for i in range(n) if x[i].varValue == 1]
    return df_av.loc[chosen]

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/result', methods=['POST'])
def result():
    session['user_data'] = {
        'weight': request.form['weight'],
        'age': request.form['age'],
        'gender': request.form['gender'],
        'goal': request.form['goal'],
        'preference': request.form['preference_type'].lower()
    }
    return redirect(url_for('generate_plan'))

@app.route('/generate')
@app.route('/generate')
def generate_plan():
    user = session.get('user_data')
    if not user:
        return redirect(url_for('home'))

    weight = user['weight']
    age = user['age']
    gender = user['gender']
    goal = user['goal']
    preference = user['preference']

    target_cals, target_prot = get_targets(weight, age, gender, goal)
    meal_split = {'breakfast':0.2, 'lunch':0.4, 'dinner':0.4}

    # Use a dynamic seed for randomness
    import uuid
    seed = uuid.uuid4().int & (1<<32)-1
    filtered = df[df['type'] == preference].sample(frac=1, random_state=seed)
    used = set()

    def pick_meal(portion):
        avail = filtered[~filtered['dish'].isin(used)]
        meal = build_optimized_meal(target_cals*portion, target_prot*portion, avail)
        used.update(meal['dish'].tolist())
        return meal

    breakfast = pick_meal(meal_split['breakfast'])
    lunch     = pick_meal(meal_split['lunch'])
    dinner    = pick_meal(meal_split['dinner'])

    summary = {}
    for name, meal in zip(['breakfast','lunch','dinner'], [breakfast,lunch,dinner]):
        summary[name] = {
            'foods': meal.to_dict('records'),
            'calories': round(meal['calories'].sum(),2),
            'protein': round(meal['protein'].sum(),2)
        }

    return render_template('result.html',
        current_date=datetime.now().strftime("%d %B %Y"),
        weight=weight, age=age, gender=gender.capitalize(), goal=goal.capitalize(),
        target_cals=target_cals, target_prot=target_prot,
        summary=summary)

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

