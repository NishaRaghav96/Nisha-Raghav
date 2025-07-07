import pandas as pd

df = pd.read_csv("classified_dishes.csv")
df.columns = df.columns.str.strip().str.lower().str.replace(r'\s+', ' ', regex=True)

df.rename(columns={
    'dish name': 'dish',
    'calories (kcal)': 'calories',
    'protein (g)': 'protein',
    'type': 'type'
}, inplace=True)

df['type'] = df['type'].astype(str).str.strip().str.lower()
df = df.dropna(subset=['calories', 'protein'])

def get_targets(weight, goal):
    if goal == "loss":
        return (weight * 30) - 400, weight * 1.0
    elif goal == "maintain":
        return weight * 35, weight * 0.9
    else:
        return weight * 40, weight * 1.5

def build_meal_plan(cal_limit, protein_limit, available_df):
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
    return pd.DataFrame(meal)

def get_meal_summary(weight, goal, preference_type):
    target_calories, target_protein = get_targets(weight, goal)
    meal_split = {"breakfast": 0.25, "lunch": 0.4, "dinner": 0.35}

    type_mapping = {
        "vegetarian": ["vegetarian", "veg"],
        "non-vegetarian": ["non-vegetarian", "non-veg", "egg", "chicken"]
    }

    allowed_types = type_mapping.get(preference_type.lower(), [])
    filtered = df[df['type'].isin(allowed_types)].sort_values(by='protein', ascending=False)

    used_dishes = set()

    def get_unique_meal(cal_limit, protein_limit):
        available = filtered[~filtered['dish'].isin(used_dishes)]
        meal = build_meal_plan(cal_limit, protein_limit, available)
        used_dishes.update(meal['dish'].tolist())
        return meal

    meals = {}
    for meal_name in ['breakfast', 'lunch', 'dinner']:
        meal_df = get_unique_meal(target_calories * meal_split[meal_name],
                                  target_protein * meal_split[meal_name])
        meals[meal_name] = {
            "foods": meal_df.to_dict('records'),
            "calories": round(meal_df['calories'].sum(), 2) if not meal_df.empty else 0,
            "protein": round(meal_df['protein'].sum(), 2) if not meal_df.empty else 0
        }

    return meals, round(target_calories, 2), round(target_protein, 2)
