# memory.py

user_memory = {}

def get_user_memory(user_id):
    if user_id not in user_memory:
        user_memory[user_id] = {
            "name": None,
            "nickname": None,
            "gift_history": [],
            "custom_facts": [],
            "last_message": None,
            "mood": None,
            "recent_topics": []
        }
    return user_memory[user_id]

def update_user_memory(user_id, key, value):
    memory = get_user_memory(user_id)
    if key == "gift_history":
        memory[key].append(value)
    elif key == "custom_facts" and value not in memory[key]:
        memory[key].append(value)
    elif key == "recent_topics":
        memory[key] = memory[key][-4:] + [value]  # keep only recent 5 topics
    else:
        memory[key] = value

def remember_fact(user_id, fact):
    update_user_memory(user_id, "custom_facts", fact)

def add_gift(user_id, gift_name):
    update_user_memory(user_id, "gift_history", gift_name)
