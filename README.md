This Flask app creates a personalized meal plan for users.
The user provides their weight, fitness goal (loss, maintain, gain), and food preference.
It reads dish information from a CSV file.
Column names are cleaned and standardized for consistency.
Dishes are filtered based on the user's selected food type.
The app calculates daily calorie and protein needs according to the goal.
These targets are split into breakfast, lunch, and dinner portions.
It selects dishes for each meal while avoiding repetition.
Only dishes that fit within calorie and protein limits are included.
The final output shows a summary with selected dishes, total calories, and protein.
