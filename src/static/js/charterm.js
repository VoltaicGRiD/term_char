var current_mode = "none"

function parseCommand(command, term) {
    if (current_mode == "notes") {
        if (command == "exit") {
            current_mode = "none"
        }
        else {
            notes(command, term)
        }
    }
    else {
        cmd = $.terminal.parse_command(command)

        let name = cmd["name"]
        let args = cmd["args"]

        switch (name) {
            case "create":
                create(args)
                break;
            case "roll":
                roll_dice(args)
                break;
            case "load":
                load()
                break;
            case "save":
                save()
                break;
            case "cls":
            case "clear":
                cls(term)
                break;
            case "wm":
            case "wildmagic":
            case "magic":
                wild_magic(args)
                break;
            case "mc":
            case "char":
            case "mycharacter":
            case "character":
                my_character(args, term)
                break;
            case "re":
            case "refresh":
                location.reload()
                break;
            case "session":
            case "sesh":
                session(args, term)
            default:
                process(name, args)
                break;
        }
    }
}

function roll_dice(args) {
    let roll_str = args.join('')

    $.ajax({
        dataType: 'json',
        url: '/roll/' + roll_str,
        context: document.body
    }).done(function(data) {
        term.echo(data.response);
    }).fail(function(jqXHR, textStatus, errorThrown) {
        term.echo('[[b;red;;]Error Code]: ' + jqXHR.status);
        term.echo('[[b;red;;]Error]: ' + errorThrown);
    })
}

function wild_magic(args) {
    $.ajax({
        dataType: 'json',
        url: '/wildmagic',
        context: document.body
    }).done(function(data) {
        term.echo(data.response);
    }).fail(function(jqXHR, textStatus, errorThrown) {
        term.echo('[[b;red;;]Error Code]: ' + jqXHR.status);
        term.echo('[[b;red;;]Error]: ' + errorThrown);
    })
}

function cls(term) {
    term.clear()

    const random = Math.floor(Math.random() * motd.length);
    term.echo(motd[random])
}

function my_character(args, term) {
    $.ajax({
        type: 'POST',
        url: '/mycharacter',
        data: JSON.stringify(args, null, '\t'),
        contentType: "application/json;charset=UTF-8",
    }).done(function(data) {
        term.echo(data.response);
        if (data.mode != undefined) {
            current_mode = data.mode
        }
    }).fail(function(jqXHR, textStatus, errorThrown) {
        term.echo('[[b;red;;]Error Code]: ' + jqXHR.status);
        term.echo('[[b;red;;]Error]: ' + errorThrown);
    })
}

function notes(command, term) {
    $.ajax({
        type: 'POST',
        url: '/mycharacter/notes',
        data: JSON.stringify(command, null, '\t'),
        contentType: "application/json;charset=UTF-8",
    }).done(function(data) {
        term.echo(data.response);
    }).fail(function(jqXHR, textStatus, errorThrown) {
        term.echo('[[b;red;;]Error Code]: ' + jqXHR.status);
        term.echo('[[b;red;;]Error]: ' + errorThrown);
    })
}

function session(args, term) {
    $.ajax({
        type: 'POST',
        url: '/session',
        data: JSON.stringify(args, null, '\t'),
        contentType: "application/json;charset=UTF-8",
    }).done(function(data) {
        term.echo(data.response);
    }).fail(function(jqXHR, textStatus, errorThrown) {
        term.echo('[[b;red;;]Error Code]: ' + jqXHR.status);
        term.echo('[[b;red;;]Error]: ' + errorThrown);
    })
}

function save() {
    $.ajax({
        url: '/save',
    }).done(function(data) {
        var file = new Blob([data.data])
        if (window.navigator.msSaveOrOpenBlob) // IE10+
            window.navigator.msSaveOrOpenBlob(file, data.filename);
        else { // Others
            var a = document.createElement("a"),
                url = URL.createObjectURL(file);
            a.href = url;
            a.download = data.filename;
            document.body.appendChild(a);
            a.click();
            setTimeout(function() {
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
            }, 0);
        }
    }).fail(function(jqXHR, textStatus, errorThrown) {
        term.echo('[[b;red;;]Error Code]: ' + jqXHR.status);
        term.echo('[[b;red;;]Error]: ' + errorThrown);
    })
}

const motd = [
    "'mc' is short for 'char', 'mycharacter', and 'character' which can all be used to invoke the 'mc' command!",
    "type 'wm' or 'wildmagic' or 'magic' to roll on the 10,000 (yes, ten THOUSAND) wild-magic effects table found here: https://centralia.aquest.com/downloads/NLRMEv2.pdf",
    "when appending or setting a note's text, you can type [[;white;;]\\n] to add a line-break",
    "this is an extra tip, since rounding in Javascript is really aggravating!"
]
