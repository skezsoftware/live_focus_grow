from app import create_app, db
from sqlalchemy import inspect

app = create_app()
with app.app_context():
    # Get table names using inspector
    inspector = inspect(db.engine)
    print("\nTables in database:", inspector.get_table_names())
    
    # Check activities table
    result = db.session.execute(db.text("SELECT * FROM activities")).fetchall()
    print("\nActivities in database:")
    for row in result:
        # Convert row to dictionary using _mapping
        row_dict = row._mapping
        print(f"- {dict(row_dict)}")
        
    # Check user_activities table structure
    print("\nUser Activities table structure:")
    for column in inspector.get_columns('user_activities'):
        print(f"- {column['name']}: {column['type']}")
    
    # Check user_activities table content
    result = db.session.execute(db.text("SELECT * FROM user_activities")).fetchall()
    print("\nUser Activities in database:")
    for row in result:
        # Convert row to dictionary using _mapping
        row_dict = row._mapping
        print(f"- {dict(row_dict)}") 