def new():
    try:
        if session["save_warning"] == 1:
            messages.append("Character data wiped. Creating a new one.")
            messages.append("\tNew character name: [[;white;;]'John Doe']")
            char = Character()
            character_data = CharacterData(name="John Doe")
            char.base_data = character_data
            character = char
            session.pop("save_warning")
    except KeyError:
        messages.append(
            "[[b;yellow;;]Warning!] Creating a new character will [[b;yellow;;]overwrite the character saved in session storage!]"
        )
        messages.append("\tType [[;white;;]mc new] again to ignore")
        messages.append("\tType [[;white;;]save] to save your character first")
        session["save_warning"] = 1
