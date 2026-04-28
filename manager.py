from models import Disaster
from storage import load_disasters, save_disasters

class SystemManager:
    def __init__(self):
        self.disasters = load_disasters()
    
    def get_all_disasters(self):
        return list(self.disasters.values())

    def add_disaster(self, event_id, name, type_val, region, country, date, magnitude, casualties, status):
        if event_id in self.disasters:
            raise ValueError(f"Event ID {event_id} already exists.")
        
        try:
            magnitude_val = float(magnitude)
            casualties_val = int(casualties)
        except ValueError:
            raise ValueError("Magnitude must be a number and casualties must be an integer.")

        d = Disaster(event_id, name, type_val, region, country, date, magnitude_val, casualties_val, status)
        self.disasters[event_id] = d
        save_disasters(self.disasters)

    def update_disaster(self, event_id, **kwargs):
        if event_id not in self.disasters:
            raise KeyError(f"Event ID {event_id} not found.")
        
        d = self.disasters[event_id]
        
        if 'magnitude' in kwargs:
            try:
                d.magnitude = float(kwargs['magnitude'])
            except ValueError:
                raise ValueError("Magnitude must be a number.")
        if 'casualties' in kwargs:
            try:
                d.casualties = int(kwargs['casualties'])
            except ValueError:
                raise ValueError("Casualties must be an integer.")
        
        for k, v in kwargs.items():
            if k not in ['magnitude', 'casualties']:
                setattr(d, k, v)
                
        save_disasters(self.disasters)

    def delete_disaster(self, event_id):
        if event_id in self.disasters:
            del self.disasters[event_id]
            save_disasters(self.disasters)
            return True
        return False

    def search_disasters(self, search_term):
        results = []
        term = search_term.lower()
        for d in self.disasters.values():
            if (term in d.name.lower() or 
                term in d.type.lower() or 
                term in d.region.lower() or 
                term in d.country.lower() or 
                term in d.status.lower()):
                results.append(d)
        return results

    def get_dashboard_stats(self):
        total = len(self.disasters)
        active = sum(1 for d in self.disasters.values() if d.status.lower() == 'active')
        if total > 0:
            highest_mag = max(self.disasters.values(), key=lambda x: x.magnitude)
            
            # Most affected region
            regions = {}
            for d in self.disasters.values():
                regions[d.region] = regions.get(d.region, 0) + 1
            most_affected_region = max(regions, key=regions.get)
        else:
            highest_mag = None
            most_affected_region = "N/A"

        # Deadliest
        deadliest = sorted(self.disasters.values(), key=lambda x: x.casualties, reverse=True)[:5]
        
        return {
            "total": total,
            "active": active,
            "highest_magnitude": highest_mag,
            "most_affected_region": most_affected_region,
            "deadliest": deadliest
        }
