import os
import json
import inspect
from flask import Flask, Response, jsonify, render_template, request, send_file, session
from dotenv import load_dotenv, dotenv_values

from src.character import Attribute, Character, CharacterData, Resource
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


@app.route("/mycharacter", methods=["POST"])
def my_character():
    arguments = request.json

    if len(arguments) == 0:
        data = {"response": "Type [[;white;;]mc help] to output help documentation"}
        return jsonify(data)

    main = arguments[0]
    args = arguments[1:]

    messages = []

    if main == "help":
        help_text = ""
        with open("src/help/help_verbose.txt", "r") as f:
            help_text = f.read()
        data = {"response": help_text}
        return jsonify(data)

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

    if main == "new":
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

    try:
        session.pop("save_warning")
    except KeyError:
        pass

    if main == "add":

        # ---- Adding an attribute ----
        if args[0] == "attr" or args[0] == "attribute":

            name = args[1]
            alias = args[2]
            roll = args[3]
            stat = float(args[4]) if isinstance(args[4], float) else 0
            n = Attribute(name=name, alias=alias, roll=roll, stat=stat)
            character.add_attr(n)
            messages.append("Added resource: ")
            messages.append(f"\tname: [[;white;;]{n.name}]")
            messages.append(f"\talias: [[;white;;]{n.alias}]")
            messages.append(f"\troll: [[;white;;]{n.roll}]")
            messages.append(f"\tstat: [[;white;;]{n.stat}]")

        # ---- Adding a resource ----
        if args[0] == "res" or args[0] == "resource":
            print("adding resource...")

            name = args[1]
            alias = args[2]
            value = args[3]
            max = args[4]
            if len(args) > 4:
                change = args[5]
            if len(args) > 5:
                if isinstance(args[6], int):
                    reset = bool(args[6])
                elif isinstance(args[6], str):
                    reset = bool(args[6])
                else:
                    reset = True
            r = Resource(
                name=name,
                alias=alias,
                value=value,
                max=max,
                change=change,
                auto_reset=reset,
                previous_value=-1,
            )
            character.add_resource(r)
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
            messages.append("Cannot heal [[b;red;;]negative] health.")
        else:
            prev, health = character.damage(-dmg)
            messages.append(f"[[b;lime;;]Healed] character for [[;white;;]{dmg}]")
            messages.append(f"Previous health: [[;white;;]{prev}]")
            messages.append(f"Current health: [[;white;;]{health}]")

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
    return extras.roll(roll_str)


@app.route("/wildmagic")
def wild_magic():
    return extras.wild_magic()


# --------------
# Main -
# --------------
if __name__ == "__main__":
    pass
