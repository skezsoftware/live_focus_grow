from app import create_app
from app.extensions import db
from app.models.activity import Activity
import uuid

app = create_app()

default_activities = {
    "Mind + Body": [
        # Physical Activities
        { "name": "Weight Lifting", "type": "physical", "description": "Strength training with weights" },
        { "name": "Jiu Jitsu", "type": "physical", "description": "Brazilian Jiu-Jitsu training" },
        { "name": "Boxing", "type": "physical", "description": "Boxing training or practice" },
        { "name": "Walking", "type": "physical", "description": "Walking for exercise" },
        { "name": "Running", "type": "physical", "description": "Running or jogging" },
        { "name": "Yoga", "type": "physical", "description": "Yoga practice" },
        { "name": "Swimming", "type": "physical", "description": "Swimming for exercise" },
        { "name": "Cycling", "type": "physical", "description": "Cycling or biking" },
        { "name": "HIIT", "type": "physical", "description": "High-Intensity Interval Training" },
        { "name": "Pilates", "type": "physical", "description": "Pilates workout" },
        # Wellness Activities
        { "name": "Cold Plunge", "type": "wellness", "description": "Cold water immersion" },
        { "name": "Sauna", "type": "wellness", "description": "Sauna session" },
        { "name": "Stretching", "type": "wellness", "description": "Stretching routine" },
        { "name": "Breathwork", "type": "wellness", "description": "Breathing exercises" },
        { "name": "Massage", "type": "wellness", "description": "Massage therapy" },
        # Mental Activities
        { "name": "Meditation", "type": "mental", "description": "Meditation practice" },
        { "name": "Reading", "type": "mental", "description": "Reading for leisure" },
        { "name": "Crossword Puzzle", "type": "mental", "description": "Solving crossword puzzles" },
        { "name": "Sudoku", "type": "mental", "description": "Playing Sudoku" },
        { "name": "Chess", "type": "mental", "description": "Playing chess" },
        { "name": "Board Game", "type": "mental", "description": "Playing board games" },
        { "name": "Language Learning", "type": "mental", "description": "Learning a new language" },
        { "name": "Mindfulness", "type": "mental", "description": "Mindfulness practice" },
    ],
    "Growth + Creation": [
        # Learning & Skills
        { "name": "Learning New Skill", "type": "growth", "description": "Learning a new skill" },
        { "name": "Online Course", "type": "growth", "description": "Taking an online course" },
        { "name": "Educational Reading", "type": "growth", "description": "Reading educational material" },
        { "name": "Skill Practice", "type": "growth", "description": "Practicing a skill" },
        # Career & Work
        { "name": "Work", "type": "career", "description": "Focused work time" },
        { "name": "Side Hustle", "type": "career", "description": "Working on side projects" },
        { "name": "Networking", "type": "career", "description": "Professional networking" },
        { "name": "Job Search", "type": "career", "description": "Job searching activities" },
        # Personal Development
        { "name": "Journaling", "type": "personal", "description": "Writing in journal" },
        { "name": "Goal Setting", "type": "personal", "description": "Setting and reviewing goals" },
        { "name": "Daily Reflection", "type": "personal", "description": "Daily reflection practice" },
        # Health & Organization
        { "name": "Clean Eating", "type": "health", "description": "Healthy eating habits" },
        { "name": "Meal Prep", "type": "health", "description": "Preparing healthy meals" },
        { "name": "Organizing", "type": "productivity", "description": "Organizing space or tasks" },
        { "name": "Planning", "type": "productivity", "description": "Planning and scheduling" },
    ],
    "Purpose + People": [
        # Family
        { "name": "Family Dinner", "type": "family", "description": "Having dinner with family" },
        { "name": "Family Time", "type": "family", "description": "Quality time with family" },
        { "name": "Family Call", "type": "family", "description": "Calling family members" },
        { "name": "Family Activity", "type": "family", "description": "Activity with family" },
        # Social
        { "name": "Night Out with Friends", "type": "social", "description": "Social time with friends" },
        { "name": "Call a Friend", "type": "social", "description": "Calling friends" },
        { "name": "Social Activity", "type": "social", "description": "Group social activity" },
        { "name": "Dating", "type": "social", "description": "Dating activities" },
        # Community
        { "name": "Volunteering", "type": "community", "description": "Volunteer work" },
        { "name": "Community Event", "type": "community", "description": "Attending community events" },
        { "name": "Mentoring", "type": "community", "description": "Mentoring others" },
        # Hobbies
        { "name": "Hobby Time", "type": "hobby", "description": "Working on hobbies" },
        { "name": "Creative Project", "type": "hobby", "description": "Creative activities" },
        { "name": "Playing Music", "type": "hobby", "description": "Playing musical instruments" },
    ],
}

def seed_activities():
    with app.app_context():
        print("Deleting existing default activities...")
        Activity.query.filter_by(is_custom=False).delete()
        db.session.commit()

        print("Seeding default activities...")
        for category, activities in default_activities.items():
            for activity in activities:
                new_activity = Activity(
                    id=str(uuid.uuid4()),
                    name=activity["name"],
                    category=category,
                    type=activity["type"],
                    description=activity["description"],
                    is_custom=False,
                    is_active=True,
                    xp_value=10.0
                )
                db.session.add(new_activity)
        
        db.session.commit()
        print("Default activities seeded successfully!")

if __name__ == "__main__":
    seed_activities() 