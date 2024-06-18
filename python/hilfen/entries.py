from config import client


# Findet den ersten Eintrag, der sich in einer Liste von Einträgen geändert hat
async def find_changed_entry(previous, current):
    filtered_previous, filtered_current = filter_bot_entries(previous, current)
    for previous, current in zip(filtered_previous, filtered_current):
        if current.extra.count != previous.extra.count or current.user != previous.user:
            return current
    return None


def filter_bot_entries(previous, current):
    # Filtern Sie die Einträge in der vorherigen Liste, die nicht von einem Bot erstellt wurden
    previous = [entry for entry in previous if not entry.user.bot]

    # Filtern Sie die Einträge in der aktuellen Liste, die nicht von einem Bot erstellt wurden
    current = [entry for entry in current if not entry.user.bot]

    return previous, current
