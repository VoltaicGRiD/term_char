import src.commands.character as char
import src.extras as extras


def distribute(main: str, args, character, messages):
    match main:
        case "help":
            return extras.help()
        case "new":
            return char.new()
