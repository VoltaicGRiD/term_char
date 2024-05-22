import os
import json
import inspect
import re
import datetime
from flask import Flask, Response, jsonify, render_template, request, session
from dotenv import load_dotenv, dotenv_values

from src.character import Attribute, Character, CharacterData, Quest, Resource, Note
import src.commands.distributor as dist
import src.extras as extras

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]


@app.route("/")
def main_func():
    return render_template("interpreter.html")


# --------------
# Character save / load -
# --------------
@app.route("/load", methods=["POST"])
def load():
    json_data = request.json
    print(json_data)
    json_data = request.get_json(False, False, False)
    print(json_data)

    return Response("success", 200, None, None, "json", False)


@app.route("/save")
def save():
    try:
        json_data = session["character"]
        character: Character = Character.parse_raw(json_data)

        data = {
            "filename": f"{character.base_data.name}.json",
            "data": character.model_dump_json(indent=2),
        }

        return jsonify(data)

        # with open("src/character_saves/mycharacter.json", "w") as f:
        #     f.write(json_data)
        #
        # return send_file(
        #     "character_saves/mycharacter.json",
        #     as_attachment=True,
        #     download_name=f"{character.base_data.name}.json",
        # )
    except KeyError as kexc:
        return Response("Error: No character loaded!", 500, None, None, None, False)


@app.route("/session", methods=["POST"])
def app_session():
    arguments = request.json

    if len(arguments) > 0:
        main = arguments[0]

        if main == "wipe":
            for key, value in session.items():
                session.pop(key)


@app.route("/mycharacter/notes", methods=["POST"])
def notes_mode():
    to_append = request.json
    messages = []

    try:
        json_data = session["character"]
        character: Character = Character.parse_raw(json_data)
    except KeyError as kexc:
        messages.append("No character selected or loaded. Creating a new one.")
        messages.append("\tNew character name: [[;white;;]'John Doe']")
        char = Character()
        character_data = CharacterData(name="John Doe")
        char.base_data = character_data
        character = char

    try:
        json_data = session["note"]
        note: Note = Note.parse_raw(json_data)
        note.note = f"{note.note}\n{to_append}"
        messages.append(f"Session note '{note.name}' exists. Appending.")
    except KeyError as kexc:
        name = f"{datetime.datetime.today()}_note"
        date = datetime.datetime.today()
        messages.append("No ongoing note. Creating one.")
        messages.append(f"\tNew note created with name [[;white;;]{name}]")
        note = Note(name=name, date=date, note=to_append)

    messages.append(note.note)
    messages.append(character.note_mode(note))
    session["note"] = note.model_dump_json()
    session["character"] = character.model_dump_json()

    data = {"response": "\n".join(messages)}
    return jsonify(data)


@app.route("/mycharacter", methods=["POST"])
def my_character():
    arguments = request.json

    if len(arguments) == 0:
        data = {"response": "Type [[;white;;]mc help] to output help documentation"}
        return jsonify(data)

    main = arguments[0]
    args = arguments[1:]

    if main == "new":
        try:
            if session["save_warning"] == 1 and char:
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
    else:
        try:
            session.pop("save_warning")
            try:
                json_data = session["character"]
                character: Character = Character.parse_raw(json_data)
            except KeyError as kexc:
                messages.append("No character selected or loaded. Creating a new one.")
                messages.append("\tNew character name: [[;white;;]'John Doe']")
                char = Character()
                character_data = CharacterData(name="John Doe")
                char.base_data = character_data
                character = char

        except KeyError:
            pass

    messages = []
    dist.distribute(main, args, character, messages)

    if main == "help":
        help_text = ""
        with open("src/help/help_verbose.txt", "r") as f:
            help_text = f.read()
        data = {"response": help_text}
        return jsonify(data)

    if main == "add":
        # ---- Adding an attribute ----
        if args[0] == "attr" or args[0] == "attribute":
            name = args[1]
            alias = args[2]
            roll = args[3]
            stat = float(args[4]) if isinstance(args[4], float) else 0
            n = Attribute(name=name, alias=alias, roll=roll, stat=stat)
            character.attribute_add(n)
            messages.append("Added resource: ")
            messages.append(f"\tname: [[;white;;]{n.name}]")
            messages.append(f"\talias: [[;white;;]{n.alias}]")
            messages.append(f"\troll: [[;white;;]{n.roll}]")
            messages.append(f"\tstat: [[;white;;]{n.stat}]")

        # ---- Adding a resource ----
        if args[0] == "res" or args[0] == "resource":
            print("adding resource...")

            if len(args) < 4:
                messages.append("[[b;red;;]Error!] Not enough arguments provided")
                messages.append(
                    "\t[[;white;;]mc add res <name> <alias> <value> <max> (change) (reset)]"
                )
            else:
                name = args[1]
                alias = args[2]
                value = args[3]
                max = args[4]
                r = Resource(
                    name=name,
                    alias=alias,
                    value=value,
                    max=max,
                    previous_value=-1,
                )
                if len(args) > 5:
                    r.change = args[5]
                if len(args) > 6:
                    if isinstance(args[6], int):
                        r.auto_reset = bool(args[6])
                    elif isinstance(args[6], str):
                        r.auto_reset = bool(args[6])
                    else:
                        r.auto_reset = True
                character.resource_add(r)
                messages.append("Added resource: ")
                messages.append(f"\tname: [[;white;;]{r.name}]")
                messages.append(f"\talias: [[;white;;]{r.alias}]")
                messages.append(f"\tvalue: [[;white;;]{r.value}]")
                messages.append(f"\tmax: [[;white;;]{r.max}]")
                messages.append(f"\tchange: [[;white;;]{r.change}]")
                messages.append(f"\tauto_reset: [[;white;;]{r.auto_reset}]")

        if args[0] == "data" or args[0] == "info":
            character.extra_data[args[1]] = args[2]
            messages.append(json.dumps(character.extra_data))

    if main == "get":
        if len(args) == 0:
            response = character.base_data
            messages.append("[[b;orange;;]Character base data:]")
            messages.append(response.model_dump_json(indent=2))

            if len(character.extra_data) > 0:
                response = character.extra_data
                messages.append("\n[[b;orange;;]Character extra data:]")
                messages.append(json.dumps(character.extra_data, indent=2))

        else:
            alias = args[0]

            a = ["--attributes", "-a"]
            r = ["--resources", "-r"]
            c = ["--counters", "-c"]
            n = ["--notes", "-n"]

            if any(alias in x for x in a):
                response = character.attributes
                for ele in response:
                    messages.append(ele.model_dump_json(indent=2))
            elif any(alias in x for x in r):
                response = character.resources
                for ele in response:
                    messages.append(ele.model_dump_json(indent=2))
            elif any(alias in x for x in c):
                response = character.counters
                for ele in response:
                    messages.append(ele.model_dump_json(indent=2))
            elif any(alias in x for x in n):
                response = character.notes
                for ele in response:
                    messages.append("---------- NOTE ----------")
                    messages.append(f"Name: [[;white;;]{ele.name}]")
                    messages.append(f"Date: [[;white;;]{ele.date}]")
                    messages.append(ele.note)
                    messages.append("--------------------------")
            else:
                response = character.get(alias)

                if response is None:
                    messages.append(
                        f"No attribute, resource, or counter with alias [[;white;;]{alias}] found."
                    )
                else:
                    try:
                        messages.append(response.model_dump_json(indent=2))
                    except AttributeError:
                        messages.append(response)

    if main == "val":
        alias = args[0]
        response = character.get(alias)

        if response is None:
            messages.append(
                f"No attribute, resource, or counter with alias [[;white;;]{alias}] found."
            )
        else:
            if getattr(response, "value") is not None:
                messages.append(f"[[b;orange;;]{response.value}]")
            else:
                messages.append(f"[[b;orange;;]{response.stat}]")

    if main == "use":
        alias = args[0]
        value = character.use(alias)
        messages.append(
            f"Resource [[;white;;]{alias}] new value: [[b;orange;;]{value}]"
        )

    if main == "dmg" or main == "damage":
        dmg = args[0]
        prev, health = character.damage(dmg)
        if dmg >= 0:
            messages.append(f"[[b;red;;]Damaged] character for [[;white;;]{dmg}]")
        else:
            messages.append(f"[[b;lime;;]Healed] character for [[;white;;]{dmg}]")
        messages.append(f"Previous health: [[;white;;]{prev}]")
        messages.append(f"Current health: [[;white;;]{health}]")

    if main == "heal":
        dmg = args[0]
        if dmg <= 0:
            messages.append(
                "Cannot heal [[b;red;;]negative] health. Use [[;white;;]mc dmg <amount>] instead"
            )
        else:
            prev, health = character.damage(-dmg)
            messages.append(f"[[b;lime;;]Healed] character for [[;white;;]{dmg}]")
            messages.append(f"Previous health: [[;white;;]{prev}]")
            messages.append(f"Current health: [[;white;;]{health}]")

    if main == "quest":
        if len(args) == 0:
            if len(character.quests) > 0:
                for ele in character.quests:
                    messages.append(ele.model_dump_json(indent=2))
            else:
                messages.append(
                    "[[b;yellow;;]Warning!] Your character has no saved quests!"
                )
        else:
            sub = args[0]

            if sub == "new":
                quest = Quest()
                quest.name = args[1]
                quest.giver = args[2] if len(args) > 2 else ""
                quest.objective = args[3] if len(args) > 3 else ""
                quest.due = args[4] if len(args) > 4 else ""
                quest.outcome = args[5] if len(args) > 5 else ""

                response = character.quest_new(quest)
                messages.append(response.model_dump_json(indent=2))

            if sub == "update":
                name = args[1]
                attribute = args[2]
                value = args[3]

                if "--" in attribute:
                    attr = attribute.replace("--", "")
                    response = character.update_quest(name, attr, value)
                    messages.append(response.model_dump_json(indent=2))
                else:
                    messages.append(
                        "[[b;red;;]Error:] ensure you're referencing a valid attribute with '--<attribute>'"
                    )

    if main == "notes" or main == "note":
        if len(args) == 0:
            data = {
                "response": "Now in [[b;lime;;]notes mode]! Everything you type is appended to a note. Type [[;white;;]'exit'] to go back to normal mode!",
                "mode": "notes",
            }
            return jsonify(data)

        else:
            if args[0] == "select":
                name = str(args[1])
                note = character.note_select(name)

                if isinstance(note, Note):
                    session["note"] = note.model_dump_json()
                    data = {
                        "response": "Now in [[b;lime;;]notes mode]! Everything you type is appended to the note you've selected. Type [[;white;;]'exit'] to go back to normal mode!",
                        "mode": "notes",
                    }
                    return jsonify(data)

            elif args[0] == "delete":
                name = str(args[1])
                confirmation = args[2]

                if (
                    confirmation == "-y"
                    or confirmation == "--yes"
                    or confirmation == "--confirm"
                ):
                    result = character.note_delete(name)
                    if result == True:
                        data = {
                            "response": f"[[b;lime;;]Success!] Note '{name}' deleted!"
                        }
                        return jsonify(data)
                    else:
                        data = {
                            "response": f"[[b;red;;]Error!] Note '{name}' not found!"
                        }
                        return jsonify(data)
                else:
                    data = {
                        "response": "[[b;yellow;;]Warning!] Note not deleted, add [[;white;;]--yes] or [[;white;;]-y] or [[;white;;]--confirm] to the end of your command to confirm deletion!"
                    }
                    return jsonify(data)

            elif args[0] == "get" or args[0] == "read":
                name = str(args[1])
                note = character.note_get(name)
                messages.append("---------- NOTE ----------")
                messages.append(f"Name: [[;white;;]{note.name}]")
                messages.append(f"Date: [[;white;;]{note.date}]")
                messages.append(note.note)
                messages.append("--------------------------")

            elif args[0] == "append" or args[0] == "add":
                name = str(args[1])
                if len(args) > 3:
                    value = " ".join(args[2:]).replace("\\n", "\n")
                else:
                    value = args[2].replace("\\n", "\n")
                note = character.note_append(name, value)
                messages.append("---------- NOTE ----------")
                messages.append(f"Name: [[;white;;]{note.name}]")
                messages.append(f"Date: [[;white;;]{note.date}]")
                messages.append(note.note)
                messages.append("--------------------------")

            elif args[0] == "new":
                name = str(args[1])

                if len(args) > 2:
                    if len(args) > 3:
                        value = " ".join(args[2:]).replace("\\n", "\n")
                    else:
                        value = args[2].replace("\\n", "\n")
                    note = Note(name=name, date=datetime.datetime.today(), note=value)
                    character.note_new(note)
                else:
                    messages.append(f"New note created! Name: [[;white;;]{name}]")

    if main == "update":
        alias = args[0]
        base_options = inspect.getmembers(
            character.base_data, lambda a: not (inspect.isroutine(a))
        )

        if any(alias in x for x in base_options):
            value = args[1]
            response = character.update_base(alias, value)
            messages.append(response.model_dump_json(indent=2))

        else:
            attribute = args[1]
            value = args[2]

            if "--" in attribute:
                attr = attribute.replace("--", "")
                response = character.update(alias, attr, value)
                messages.append(response.model_dump_json(indent=2))
            else:
                messages.append(
                    "[[b;red;;]Error:] ensure you're referencing a valid attribute with '--<attribute>'"
                )

    session["character"] = character.model_dump_json()

    data = {"response": "\n".join(messages)}

    return jsonify(data)


# --------------
# Extras -
# --------------
@app.route("/roll/<roll_str>")
def roll(roll_str: str):
    if "@" in roll_str:
        try:
            json_data = session["character"]
            character: Character = Character.parse_raw(json_data)
        except KeyError as kexc:
            messages.append("No character selected or loaded. Creating a new one.")
            messages.append("\tNew character name: [[;white;;]'John Doe']")
            char = Character()
            character_data = CharacterData(name="John Doe")
            char.base_data = character_data
            character = char

        roll_str = character.get_roll_data(roll_str)

        print(roll_str)
        result, expl = extras.roll(roll_str)

    else:
        result, expl = extras.roll(roll_str)

    output = f"--------------------\n[[;white;;]Result:] [[b;lime;;]{result}]\n[[;white;;]Reason:] {expl}\n--------------------"

    data = {"response": output}
    return jsonify(data)


@app.route("/wildmagic")
def wild_magic():
    return extras.wild_magic()


# --------------
# Main -
# --------------
if __name__ == "__main__":
    pass
