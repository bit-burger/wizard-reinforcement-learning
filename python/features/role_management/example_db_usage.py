from features.role_management.database import Database

db = Database()

# Einen Tag mit Mitgliedern einfügen
db.insert_tag('Tag1', '#FF5733', [708227359916163137, 7082273889161343137])

# Einen Tag löschen
db.delete_tag('Tag1')

# Eine Rolle einfügen
db.insert_role('Admin')

# Den Timestamp der Rolle aktualisieren
db.update_role_last_used('Admin')

# Eine Rolle löschen
db.delete_role('Admin')

db.close()