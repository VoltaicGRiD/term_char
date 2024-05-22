import json

from flask import jsonify
import rolldice as dice


def wild_magic():
    with open("src/wildmagic.json", "r") as f:
        data = json.load(f)

        dur_roll = str(dice.roll_dice("1d100")[0])
        dur_data: dict = data["duration"]
        dur = dur_data[dur_roll]

        for expr in dur.split(" "):
            try:
                roll, _ = dice.roll_dice(expr)
                val = f"[[;gray;;]{{{expr}}}] [[b;orange;;]{str(roll)}]"
                dur = dur.replace(expr, val)
            except dice.DiceGroupException:
                continue
            except dice.DiceOperatorException:
                continue

        effect_roll = str(dice.roll_dice("1d10")[0])
        effect_data: dict = data[f"effect{effect_roll}"]
        sub_effect_roll = str(dice.roll_dice("1d1000")[0])
        effect = effect_data[sub_effect_roll]

        for expr in effect.split(" "):
            try:
                roll, _ = dice.roll_dice(expr)
                val = f"[[;gray;;]{{{expr}}}] [[b;orange;;]{str(roll)}]"
                effect = effect.replace(expr, val)
            except dice.DiceGroupException as exc:
                print(exc)
                continue
            except dice.DiceOperatorException as exc:
                print(exc)
                continue

        output = f"[[;white;;]Until [[;gray;;]{{{dur_roll}/100}}] {dur}, [[;gray;;]{{{int(effect_roll) - 1}{int(sub_effect_roll)}/10,000}}] {effect}]"
        response = {"response": output}

        return jsonify(response)


def roll(roll_str: str) -> tuple[int, str]:
    result, explanation = dice.roll_dice(roll_str)

    return result, explanation


def roll_table(options: list[str], count=1) -> list[str]:
    size = len(options)
    dice_str = f"1d{size}"
    results: list[str] = []

    for _ in range(count):
        result, _ = roll(dice_str)
        results.append(options[result])

    return results
