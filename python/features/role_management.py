from hilfen.role_database import Database

db = Database()

# Einen Tag mit Mitgliedern einfügen
db.insert_tag('Tag1', '#FF5733', [123, 456, 789])

# Einen Tag löschen
db.delete_tag('Tag1')

# Eine Rolle einfügen
db.insert_role('Admin')

# Den Timestamp der Rolle aktualisieren
db.update_role_last_used('Admin')

# Eine Rolle löschen
db.delete_role('Admin')

db.close()