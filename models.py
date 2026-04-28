class User:
    def __init__(self, username, password):
        self.username = username
        self.password = password

class Disaster:
    def __init__(self, event_id, name, type, region, country, date, magnitude, casualties, status):
        self.event_id = event_id
        self.name = name
        self.type = type
        self.region = region
        self.country = country
        self.date = date
        self.magnitude = float(magnitude)
        self.casualties = int(casualties)
        self.status = status

    def to_dict(self):
        return {
            "event_id": self.event_id,
            "name": self.name,
            "type": self.type,
            "region": self.region,
            "country": self.country,
            "date": self.date,
            "magnitude": self.magnitude,
            "casualties": self.casualties,
            "status": self.status
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            data["event_id"],
            data["name"],
            data["type"],
            data["region"],
            data["country"],
            data["date"],
            data["magnitude"],
            data["casualties"],
            data["status"]
        )
