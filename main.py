import sys
from auth import authenticate
from manager import SystemManager

def print_separator():
    print("-" * 50)

def login_flow():
    print("=== Welcome to Sentinel ===")
    while True:
        username = input("Username: ")
        password = input("Password: ")
        if authenticate(username, password):
            print("\nLogin successful!")
            return True
        else:
            print("Invalid credentials. Try again.\n")

def display_dashboard(manager):
    stats = manager.get_dashboard_stats()
    print_separator()
    print("=== D A S H B O A R D ===")
    print(f"Total Disasters Logged: {stats['total']}")
    print(f"Active Disasters: {stats['active']}")
    
    if stats['highest_magnitude']:
        hm = stats['highest_magnitude']
        print(f"Highest Magnitude: {hm.magnitude} ({hm.name})")
    
    print(f"Most Affected Region: {stats['most_affected_region']}")
    
    print("\nRecent Alerts (Top 5 Deadliest):")
    for d in stats['deadliest']:
        print(f"- {d.name} ({d.casualties} casualties)")
    print_separator()

def main_menu():
    print("\n=== Main Menu ===")
    print("1. View all disasters")
    print("2. Add new disaster")
    print("3. Search/filter disasters")
    print("4. Update disaster record")
    print("5. Delete disaster record")
    print("6. View dashboard statistics")
    print("7. Logout")
    return input("Choose an action: ")

def view_all(manager):
    print_separator()
    print("=== All Disasters ===")
    for d in manager.get_all_disasters():
        print(f"[{d.event_id}] {d.name} | {d.type} | {d.date} | Status: {d.status}")

def add_disaster(manager):
    print_separator()
    print("=== Add New Disaster ===")
    event_id = input("Event ID: ")
    name = input("Name: ")
    type_val = input("Type: ")
    region = input("Region: ")
    country = input("Country: ")
    date = input("Date (YYYY-MM-DD): ")
    magnitude = input("Magnitude: ")
    casualties = input("Casualties: ")
    status = input("Status: ")
    
    try:
        manager.add_disaster(event_id, name, type_val, region, country, date, magnitude, casualties, status)
        print("Disaster record added successfully!")
    except ValueError as e:
        print(f"Error adding record: {e}")

def search_disasters(manager):
    print_separator()
    term = input("Enter search term (type, region, status, etc.): ")
    results = manager.search_disasters(term)
    print(f"\nFound {len(results)} matching records:")
    for d in results:
         print(f"[{d.event_id}] {d.name} | {d.type} | Region: {d.region} | Status: {d.status}")

def update_disaster(manager):
    print_separator()
    event_id = input("Enter Event ID to update: ")
    print("Enter new values (leave blank to keep current):")
    name = input("Name: ")
    type_val = input("Type: ")
    region = input("Region: ")
    country = input("Country: ")
    date = input("Date: ")
    magnitude = input("Magnitude: ")
    casualties = input("Casualties: ")
    status = input("Status: ")
    
    updates = {}
    if name: updates['name'] = name
    if type_val: updates['type'] = type_val
    if region: updates['region'] = region
    if country: updates['country'] = country
    if date: updates['date'] = date
    if magnitude: updates['magnitude'] = magnitude
    if casualties: updates['casualties'] = casualties
    if status: updates['status'] = status
    
    try:
        manager.update_disaster(event_id, **updates)
        print("Record updated successfully!")
    except (KeyError, ValueError) as e:
        print(f"Error: {e}")

def delete_disaster(manager):
    print_separator()
    event_id = input("Enter Event ID to delete: ")
    confirm = input(f"Are you sure you want to delete {event_id}? (y/n): ")
    if confirm.lower() == 'y':
        if manager.delete_disaster(event_id):
            print("Record deleted successfully.")
        else:
            print("Event ID not found.")
    else:
        print("Deletion cancelled.")

def run():
    if not login_flow():
        return

    manager = SystemManager()
    
    while True:
        display_dashboard(manager)
        choice = main_menu()
        
        if choice == '1':
            view_all(manager)
        elif choice == '2':
            add_disaster(manager)
        elif choice == '3':
            search_disasters(manager)
        elif choice == '4':
            update_disaster(manager)
        elif choice == '5':
            delete_disaster(manager)
        elif choice == '6':
            # Dashboard is displayed at start of loop
            pass
        elif choice == '7':
            print("Logging out...")
            break
        else:
            print("Invalid choice, please try again.")

if __name__ == "__main__":
    run()
