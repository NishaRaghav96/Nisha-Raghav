from flask import Flask, render_template, request
import pandas as pd
from datetime import datetime

app = Flask(__name__)

# Load CSV and clean column names
df = pd.read_csv("classified_dishes.csv")
df.columns = df.columns.str.strip().str.replace(r'\s+', ' ', regex=True)

# Rename columns to simple names
df.rename(columns={
    'Dish Name': 'dish',
    'Calories (kcal)': 'calories',
    'Protein (g)': 'protein',
    'Type': 'type'
}, inplace=True)

# Normalize 'type' column for safe filtering
df['type'] = df['type'].str.strip().str.lower()

print("✅ Final Columns:", df.columns.tolist())
print("Unique types in dataframe:", df['type'].unique())

def get_targets(weight, goal):
    if goal == "loss":
        return (weight * 30) - 400, weight * 1.0
    elif goal == "maintain":
        return weight * 35, weight * 0.9
    else:
        return weight * 40, weight * 1.5

def build_meal_plan(cal_limit, protein_limit, available_df):
    print(f"Build meal plan with cal_limit={cal_limit}, protein_limit={protein_limit}")
    print("Top 5 available dishes:")
    print(available_df.head())
    
    meal = []
    total_cals = 0
    total_protein = 0
    for _, row in available_df.iterrows():
        cal = row['calories']
        prot = row['protein']
        if total_cals + cal <= cal_limit and total_protein + prot <= protein_limit:
            meal.append(row)
            total_cals += cal
            total_protein += prot
        if total_cals >= cal_limit * 0.9 or total_protein >= protein_limit * 0.9:
            break

    if meal:
        return pd.DataFrame(meal)
    else:
        return pd.DataFrame(columns=['dish', 'calories', 'protein', 'type'])

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/result', methods=['POST'])
def result():
    weight = float(request.form['weight'])
    goal = request.form['goal']
    preference_type = request.form['preference_type'].strip().lower()

    print(f"User input - Weight: {weight}, Goal: {goal}, Preference: {preference_type}")

    target_calories, target_protein = get_targets(weight, goal)
    meal_split = {"breakfast": 0.25, "lunch": 0.4, "dinner": 0.35}

    # Filter by type
    filtered = df[df['type'] == preference_type].sort_values(by='protein', ascending=False)
    print(f"Filtered rows count: {len(filtered)}")

    used_dishes = set()

    def get_unique_meal(cal_limit, protein_limit, available_df, used):
        available = available_df[~available_df['dish'].isin(used)]
        meal = build_meal_plan(cal_limit, protein_limit, available)
        # Update used dishes
        used.update(meal['dish'].tolist())
        return meal

    breakfast = get_unique_meal(target_calories * meal_split['breakfast'], target_protein * meal_split['breakfast'], filtered, used_dishes)
    lunch = get_unique_meal(target_calories * meal_split['lunch'], target_protein * meal_split['lunch'], filtered, used_dishes)
    dinner = get_unique_meal(target_calories * meal_split['dinner'], target_protein * meal_split['dinner'], filtered, used_dishes)

    summary = {
        "breakfast": {
            "foods": breakfast.to_dict('records'),
            "calories": round(breakfast['calories'].sum(), 2) if not breakfast.empty else 0,
            "protein": round(breakfast['protein'].sum(), 2) if not breakfast.empty else 0
        },
        "lunch": {
            "foods": lunch.to_dict('records'),
            "calories": round(lunch['calories'].sum(), 2) if not lunch.empty else 0,
            "protein": round(lunch['protein'].sum(), 2) if not lunch.empty else 0
        },
        "dinner": {
            "foods": dinner.to_dict('records'),
            "calories": round(dinner['calories'].sum(), 2) if not dinner.empty else 0,
            "protein": round(dinner['protein'].sum(), 2) if not dinner.empty else 0
        }
    }

    return render_template("result.html",
                           current_date=datetime.now().strftime("%d %B %Y"),
                           goal=goal.capitalize(),
                           target_calories=round(target_calories, 2),
                           target_protein=round(target_protein, 2),
                           summary=summary)

if __name__ == '__main__':
    app.run(debug=True)
