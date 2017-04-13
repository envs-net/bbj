# -*- fill-column: 72 -*-
"""
If you're looking for help on how to use the program, just press
? while its running. This mess will not help you.

Urwid aint my speed. Hell, making complex, UI-oriented programs
aint my speed. So some of this code is pretty messy. I stand by
it though, and it seems to be working rather well.

Most of the functionality is crammed in the App() class. Key
handling is found in the other subclasses for urwid widgets.
An instantiation of App() is casted as `app` globally and
the keypress methods will call into this global `app` object.

There are few additional functions that are defined outside
of the App class. They are delegated to the very bottom of
this file.

Please mail me (~desvox) for feedback and for any of your
"OH MY GOD WHY WOULD YOU DO THIS"'s or "PEP8 IS A THING"'s.
"""

from network import BBJ, URLError
from string import punctuation
from datetime import datetime
from time import time, sleep
from subprocess import run
from random import choice
from sys import argv
import tempfile
import urwid
import json
import os
import re

try:
    port_spec = argv.index("--port")
    port = argv[port_spec+1]
except ValueError: # --port not specified
    port = 7099
except IndexError: # flag given but no value
    exit("thats not how this works, silly! --port 7099")

try:
    network = BBJ(host="127.0.0.1", port=port)
except URLError as e:
    # print the connection error in red
    exit("\033[0;31m%s\033[0m" % repr(e))

obnoxious_logo = """
  %     _                 *              !            *
%   8 888888888o  % 8 888888888o   .           8 8888
    8 8888    `88.  8 8888    `88.      _   !  8 8888   &
  ^ 8 8888     `88  8 8888     `88   *         8 8888 _
    8 8888     ,88  8 8888     ,88             8 8888
*   8 8888.   ,88'  8 8888.   ,88'      !      8 8888    "
    8 8888888888    8 8888888888               8 8888 =
  ! 8 8888    `88.  8 8888    `88.  88.        8 8888
    8 8888      88  8 8888      88  `88.    |  8 888'   '
 >  8 8888.   ,88'  8 8888.   ,88'    `88o.   .8 88'  .
    8 888888888P    8 888888888P        `Y888888 '  .
 %                                                     %"""

welcome = """>>> Welcome to Bulletin Butter & Jelly! ------------------@
| BBJ is a persistent, chronologically ordered text       |
| discussion board for tilde.town. You may log in,        |
| register as a new user, or participate anonymously.     |
|---------------------------------------------------------|
| \033[1;31mTo go anon, just press enter. Otherwise, give me a name\033[0m |
|                 \033[1;31m(registered or not)\033[0m                     |
@_________________________________________________________@
"""

format_help = [
    "Quick reminder: \[rainbow: expressions work like this]\n\n"

    "BBJ supports **bolding**, __underlining__, and [rainbow: coloring] text "
    "using markdown-style symbols as well as tag-like expressions. Markdown "
    "is **NOT** fully implemented, but several of the more obvious concepts "
    "have been brought over. Additionally, we have chan-style greentext and "
    "numeric post referencing, ala >>3 for the third reply.",

    "[red: Whitespace]",

    "When you're composing, it is desirable to introduce linebreaks into the "
    "body to keep it from overflowing the screen. However, you __dont__ want "
    "that same spacing to bleed over to other people's screens, because clients "
    "will wrap the text themselves.",

    "Single line breaks in the body join into eachother to form sentences, "
    "putting a space where the break was. This works like html. When you want "
    "to split it off into a paragraph, **use two line breaks.**",

    "[red: Colors, Bold, Underline & Expressions]",

    "You can use [rainbow: rainbow], [red: red], [yellow: yellow], [green: green], "
    "[blue: blue], [cyan: cyan], [magenta: and magenta], **bold**, and __underline__ "
    "inside of your posts. **bold\nworks like this**, __and\nunderlines like this__. "
    "The symbolic, markdown form of these directives does NOT allow escaping, and "
    "can only apply to up to 20 characters on the same line. They are best used on short "
    "phrases. However, you can use a different syntax for it, which is also required to use "
    "colors: these expressions \[bold: look like this] and are much more reliable. "
    "The colon and the space following it are important. When you use these "
    "expressions, the __first__ space is not part of the content, but any characters, "
    "including spaces, that follow it are included in the body. The formatting will "
    "apply until the closing ]. You can escape such an expression \\\[cyan: like this] "
    "and can also \\[blue: escape \\\] other closing brackets] inside of it. Only "
    "closing brackets need to be escaped within an expression. Any backslashes used "
    "for escaping will not show in the body unless you use two slashes.",

    "This peculiar syntax elimiates false positives. You never have to escape [normal] "
    "brackets when using the board. Only expressions with **valid and defined** directives "
    "will be affected. [so: this is totally valid and requires no escapes] because 'so' is "
    "not a directive. [red this will pass too] because the colon is missing.",

    "The following directives may be used in this form: red, yellow, green, blue, cyan, "
    "magenta, bold, underline, and rainbow. Nesting expressions into eachother will "
    "override the parent directives until it closes. Thus, nesting is valid but doesn't produce "
    "layered results.",

    "[red: Quotes & Greentext]",

    "You can refer to a post number using two angle brackets pointing into a number. >>432 "
    "like this. You can color a whole line green by proceeding it with a '>'. Note that "
    "this violates the sentence structure outlined in the **Whitespace** section above, "
    "so you may introduce >greentext without splicing into seperate paragraphs. The '>' "
    "must be the first character on the line with no whitespace before it.\n>it looks like this\n"
    "and the paragraph doesnt have to break on either side.",

    "When using numeric quotes, they are highlighted and the author's name will show "
    "next to them in the thread. You can press enter when focused on a message to view "
    "the parent posts. You may insert these directives manually or use the <Reply> function "
    "on post menus.",

    "Quoting directives cannot be escaped."
]

general_help = [
    ("bold", "use q or escape to close dialogs and menus (including this one)\n\n"),

    "You may use the arrow keys, or use jk/np/Control-n|p to move up and down by "
    "an element. If an element is overflowing the screen, it will scroll only one line. "
    "To make scrolling faster, hold shift when using a control: it will repeat 5 times.\n\n"

    "To go back and forth between threads, you may also use the left/right arrow keys, "
    "or h/l to do it vi-style.\n\n"

    "In the thread index and any open thread, the b and t keys may be used to go to "
    "very top or bottom.\n\n"

    "Aside from those, primary controls are shown on the very bottom of the screen "
    "in the footer line, or may be placed in window titles for other actions like "
    "dialogs or composers."
]

colors = [
    "\033[1;31m", "\033[1;33m", "\033[1;33m",
    "\033[1;32m", "\033[1;34m", "\033[1;35m"
]

colornames = ["none", "red", "yellow", "green", "blue", "cyan", "magenta"]
editors = ["nano", "vim", "emacs", "vim -u NONE", "emacs -Q", "micro", "ed", "joe"]

default_prefs = {
    "editor": os.getenv("EDITOR", default="nano"),
    "integrate_external_editor": True,
    "dramatic_exit": True,
    "date": "%Y/%m/%d",
    "time": "%H:%M",
    "frame_title": "> > T I L D E T O W N < <",
    "max_text_width": 80
}

bars = {
    "index": "[RET]Open [C]ompose [R]efresh [O]ptions [?]Help [Q]uit",
    "thread": "[C]ompose [RET]Interact [Q]Back [R]efresh [B/T]End [?]Help"
}

colormap = [
    ("default", "default", "default"),
    ("bar", "light magenta", "default"),
    ("button", "light red", "default"),
    ("quote", "brown", "default"),
    ("opt_prompt", "black", "light gray"),
    ("opt_header", "light cyan", "default"),
    ("hover", "light cyan", "default"),
    ("dim", "dark gray", "default"),
    ("bold", "default,bold", "default"),
    ("underline", "default,underline", "default"),

    # map the bbj api color values for display
    ("0", "default", "default"),
    ("1", "dark red", "default"),
    # sounds ugly but brown is as close as we can get to yellow without being bold
    ("2", "brown", "default"),
    ("3", "dark green", "default"),
    ("4", "dark blue", "default"),
    ("5", "dark cyan", "default"),
    ("6", "dark magenta", "default"),

    # and have the bolded colors use the same values times 10
    ("10", "light red", "default"),
    ("20", "yellow", "default"),
    ("30", "light green", "default"),
    ("40", "light blue", "default"),
    ("50", "light cyan", "default"),
    ("60", "light magenta", "default")
]

class App(object):
    def __init__(self):
        self.prefs = bbjrc("load")

        self.mode = None
        self.thread = None
        self.usermap = {}
        self.window_split = False
        self.last_pos = 0

        # these can be changed and manipulated by other methods
        self.walker = urwid.SimpleFocusListWalker([])
        self.box = ActionBox(self.walker)

        self.loop = urwid.MainLoop(
            urwid.Frame(
                urwid.LineBox(
                    self.box,
                    title=self.prefs["frame_title"],
                    **frame_theme()
                )),
            palette=colormap,
            handle_mouse=False)

        self.index()


    def set_header(self, text, *format_specs):
        """
        Update the header line with the logged in user, a seperator,
        then concat text with format_specs applied to it. Applies
        bar formatting to it.
        """
        header = ("{}@bbj | " + text).format(
            (network.user_name or "anonymous"),
            *format_specs
        )
        self.loop.widget.header = urwid.AttrMap(urwid.Text(header), "bar")


    def set_footer(self, string):
        """
        Sets the footer to display `string`, applying bar formatting.
        Other than setting the color, `string` is shown verbatim.
        """
        self.loop.widget.footer = urwid.AttrMap(urwid.Text(string), "bar")


    def set_default_header(self):
        """
        Sets the header to the default for the current screen.
        """
        if self.mode == "thread":
            name = self.usermap[self.thread["author"]]["user_name"]
            self.set_header("~{}: {}", name, self.thread["title"])
        else:
            self.set_header("{} threads", len(self.walker))


    def set_default_footer(self):
        """
        Sets the footer to the default for the current screen.
        """
        self.set_footer(bars[self.mode])


    def set_bars(self):
        """
        Sets both the footer and header to their default values
        for the current mode.
        """
        self.set_default_header()
        self.set_default_footer()


    def close_editor(self):
        """
        Close whatever editing widget is open and restore proper
        state back the walker.
        """
        if self.window_split:
            self.window_split = False
            self.loop.widget.focus_position = "body"
            self.set_footer(bars["thread"])
        else:
            self.loop.widget = self.loop.widget[0]
        self.set_default_header()


    def remove_overlays(self, *_):
        """
        Remove ALL urwid.Overlay objects which are currently covering the base
        widget.
        """
        while True:
            try:
                self.loop.widget = self.loop.widget[0]
            except:
                break


    def switch_editor(self):
        """
        Switch focus between the thread viewer and the open editor
        """
        if not self.window_split:
            return

        elif self.loop.widget.focus_position == "body":
            self.loop.widget.focus_position = "footer"
            focus = "[focused on editor]"
            attr = ("bar", "dim")

        else:
            self.loop.widget.focus_position = "body"
            focus = "[focused on thread]"
            attr = ("dim", "bar")

        self.loop.widget.footer[0].set_text(
            "[F1]Abort [F2]Swap [F3]Formatting Help [save/quit to send] " + focus)

        # HACK WHY WHY WHY WHYW HWY
        # this sets the focus color for the editor frame
        self.loop.widget.footer.contents[1][0].original_widget.attr_map = \
            self.loop.widget.footer.contents[0][0].attr_map = {None: attr[0]}
        self.loop.widget.header.attr_map = {None: attr[1]}


    def readable_delta(self, modified):
        """
        Return a human-readable string representing the difference
        between a given epoch time and the current time.
        """
        delta = time() - modified
        hours, remainder = divmod(delta, 3600)
        if hours > 48:
            return self.timestring(modified)
        elif hours > 1:
            return "%d hours ago" % hours
        elif hours == 1:
            return "about an hour ago"
        minutes, remainder = divmod(remainder, 60)
        if minutes > 1:
            return "%d minutes ago" % minutes
        return "less than a minute ago"


    def quote_view_action(self, button, message):
        """
        Callback function to view a quote from the message object menu.
        """
        widget = OptionsMenu(
            urwid.ListBox(
                urwid.SimpleFocusListWalker([
                    *self.make_message_body(message)
                ])),
            title=">>%d" % message["post_id"],
            **frame_theme()
        )

        self.loop.widget = urwid.Overlay(
            widget, self.loop.widget,
            align=("relative", 50),
            valign=("relative", 50),
            width=("relative", 98),
            height=("relative", 60)
        )


    def quote_view_menu(self, button, post_ids):
        """
        Receives a list of quote ids and makes a frilly menu to pick one to view.
        It retrieves messages objects from the thread and attaches them to a
        callback to `quote_view_action`
        """
        buttons = []
        for pid in post_ids:
            try:
                message = self.thread["messages"][pid]
                if len(post_ids) == 1:
                    return self.quote_view_action(button, message)
                author = self.usermap[message["author"]]
                label = [
                    ("button", ">>%d " % pid),
                    "(",
                    (str(author["color"]),
                     author["user_name"]),
                    ")"
                ]
                buttons.append(cute_button(label, self.quote_view_action, message))
            except IndexError:
                continue # users can submit >>29384234 garbage references

        widget = OptionsMenu(
            urwid.ListBox(urwid.SimpleFocusListWalker(buttons)),
            title="View a Quote", **frame_theme()
        )

        self.loop.widget = urwid.Overlay(
            widget, self.loop.widget,
            align=("relative", 50),
            valign=("relative", 50),
            height=len(buttons) + 3,
            width=30
        )





    def edit_post(self, button, message):
        post_id = message["post_id"]
        thread_id = message["thread_id"]
        # first we need to get the server's version of the message
        # instead of our formatted one
        try:
            message = network.edit_query(thread_id, post_id)
        except UserWarning as e:
            self.remove_overlays()
            return self.temp_footer_message(e.description)

        self.loop.widget = urwid.Overlay(
            urwid.LineBox(
                ExternalEditor(
                    "edit_post",
                    init_body=message["body"],
                    post_id=post_id,
                    thread_id=thread_id),
                title="[F1]Abort [F3]Formatting Help (save/quit to commit)",
                **frame_theme()),
            self.loop.widget,
            align="center",
            valign="middle",
            width=("relative", 75),
            height=("relative", 75))


    def reply(self, button, message):
        self.remove_overlays()
        self.compose(init_body=">>%d\n\n" % message["post_id"])



    def on_post(self, button, message):
        quotes = self.get_quotes(message)
        author = self.usermap[message["author"]]
        buttons = [
            urwid.Button("Reply", self.reply, message),
        ]

        if quotes and message["post_id"] != 0:
            buttons.insert(1, urwid.Button(
                "View %sQuote" % ("a " if len(quotes) != 1 else ""),
                self.quote_view_menu, quotes))

        if network.can_edit(message["thread_id"], message["post_id"]):
            buttons.insert(0, urwid.Button("Edit Post", self.edit_post, message))

        widget = OptionsMenu(
            urwid.ListBox(urwid.SimpleFocusListWalker(buttons)),
            title=str(">>%d (%s)" % (message["post_id"], author["user_name"])),
            **frame_theme()
        )
        size = self.loop.screen_size

        self.loop.widget = urwid.Overlay(
            urwid.AttrMap(widget, str(author["color"]*10)),
            self.loop.widget,
            align=("relative", 50),
            valign=("relative", 50),
            width=30,
            height=len(buttons) + 2
        )


    def get_quotes(self, msg_object, value_type=int):
        """
        Returns the post_ids that msg_object is quoting.
        Is a list, may be empty. ids are ints by default
        but can be passed `str` for strings.
        """
        quotes = []
        for paragraph in msg_object["body"]:
            # yes python is lisp fuck you
            [quotes.append(cdr) for car, cdr in paragraph if car == "quote"]
        return [value_type(q) for q in quotes]


    def make_thread_body(self, thread):
        """
        Returns the pile widget that comprises a thread in the index.
        """
        button = cute_button(">>", self.thread_load, thread["thread_id"])
        title = urwid.Text(thread["title"])
        user = self.usermap[thread["author"]]
        dateline = [
            ("default", "by "),
            (str(user["color"]), "~%s " % user["user_name"]),
            ("dim", "@ %s" % self.timestring(thread["created"]))
        ]

        infoline = "%d replies; active %s" % (
            thread["reply_count"], self.timestring(thread["last_mod"], "delta"))

        pile = urwid.Pile([
            urwid.Columns([(3, urwid.AttrMap(button, "button", "hover")), title]),
            urwid.Text(dateline),
            urwid.AttrMap(urwid.Text(infoline), "dim"),
            urwid.AttrMap(urwid.Divider("-"), "dim")
        ])

        pile.thread = thread
        return pile


    def make_message_body(self, message, no_action=False):
        """
        Returns the widgets that comprise a message in a thread, including the
        text body, author info and the action button
        """
        info = "@ " + self.timestring(message["created"])
        if message["edited"]:
            info += " [edited]"

        if no_action:
            callback = ignore
            name = urwid_rainbows("~SYSTEM", True)
            color = "0"
        else:
            callback = self.on_post
            name = urwid.Text("~{}".format(self.usermap[message["author"]]["user_name"]))
            color = str(self.usermap[message["author"]]["color"])

        post = str(message["post_id"])
        head = urwid.Columns([
                (2 + len(post), urwid.AttrMap(
                    cute_button(">" + post, callback, message), "button", "hover")),
                (len(name._text) + 1, urwid.AttrMap(name, color)),
                urwid.AttrMap(urwid.Text(info), "dim")
            ])

        head.message = message
        return [
            head,
            urwid.Divider(),
            urwid.Padding(
                MessageBody(message),
                width=self.prefs["max_text_width"]),
            urwid.Divider(),
            urwid.AttrMap(urwid.Divider("-"), "dim")
        ]


    def timestring(self, epoch, mode="both"):
        """
        Returns a string of time representing a given epoch and mode.
        """
        if mode == "delta":
            return self.readable_delta(epoch)

        date = datetime.fromtimestamp(epoch)
        if mode == "time":
            directive = self.prefs["time"]
        elif mode == "date":
            directive = self.prefs["date"]
        else:
            directive = "%s %s" % ( self.prefs["time"], self.prefs["date"])
        return date.strftime(directive)





    def index(self, *_):
        """
        Browse the index.
        """
        self.mode = "index"
        self.thread = None
        self.window_split = False
        threads, usermap = network.thread_index()
        self.usermap.update(usermap)
        self.walker.clear()
        for thread in threads:
            self.walker.append(self.make_thread_body(thread))
        self.set_bars()
        try: self.box.set_focus(self.last_pos)
        except IndexError:
            self.box.change_focus(size, 0)


    def thread_load(self, button, thread_id):
        """
        Open a thread.
        """
        if self.mode == "index":
            self.last_pos = self.box.get_focus()[1]
        self.mode = "thread"
        thread, usermap = network.thread_load(thread_id, format="sequential")
        self.usermap.update(usermap)
        self.thread = thread
        self.walker.clear()
        for message in thread["messages"]:
            self.walker += self.make_message_body(message)
        self.set_bars()


    def refresh(self, bottom=True):
        self.remove_overlays()
        if self.mode == "index":
            return self.index()
        self.thread_load(None, self.thread["thread_id"])
        if bottom:
            self.box.set_focus(len(self.walker) - 5)


    def back(self, terminate=False):
        if app.mode == "index" and terminate:
            frilly_exit()

        elif self.window_split:
            # display a confirmation dialog before killing off an in-progress post
            buttons = [
                urwid.Text(("bold", "Discard current post?")),
                urwid.Divider(),
                cute_button(("10" ,">> Yes"), lambda _: [
                    self.remove_overlays(),
                    self.index()
                ]),
                cute_button(("30", "<< No"), self.remove_overlays)
            ]

            # TODO: create a central routine for creating popups. this is getting really ridiculous
            popup = OptionsMenu(
                urwid.ListBox(urwid.SimpleFocusListWalker(buttons)),
                **frame_theme())

            self.loop.widget = urwid.Overlay(
                popup, self.loop.widget,
                align=("relative", 50),
                valign=("relative", 25),
                width=30, height=6)

        else:
            self.index()


    def set_new_editor(self, button, value, arg):
        """
        Callback for the option radio buttons to set the the text editor.
        """
        if value == False:
            return
        elif isinstance(value, str):
            [button.set_state(False) for button in arg]
            self.prefs["editor"] = value
            bbjrc("update", **self.prefs)
            return

        key, widget = arg
        widget.set_edit_text(key)
        self.prefs.update({"editor": key})
        bbjrc("update", **self.prefs)


    def set_editor_mode(self, button, value):
        """
        Callback for the editor mode radio buttons in the options.
        """
        self.prefs["integrate_external_editor"] = value
        bbjrc("update", **self.prefs)


    def relog(self, *_, **__):
        """
        Options menu callback to log the user in again.
        Drops back to text mode because im too lazy to
        write a responsive urwid thing for this.
        """
        self.loop.widget = self.loop.widget[0]
        self.loop.stop()
        run("clear", shell=True)
        print(welcome)
        try: log_in()
        except (KeyboardInterrupt, InterruptedError): pass
        self.loop.start()
        self.set_default_header()
        self.options_menu()


    def unlog(self, *_, **__):
        """
        Options menu callback to anonymize the user and
        then redisplay the options menu.
        """
        network.user_name = network.user_auth = None
        self.loop.widget = self.loop.widget[0]
        self.set_default_header()
        self.options_menu()


    def general_help(self):
        """
        Show a general help dialog. In all honestly, its not
        very useful and will only help people who have never
        really used terminal software before =)
        """
        widget = OptionsMenu(
            urwid.ListBox(
                urwid.SimpleFocusListWalker([
                    urwid_rainbows(
                        "This is BBJ, a client/server textboard made for tilde.town!",
                        True),
                    urwid.Text(("dim", "...by ~desvox")),
                    urwid.Divider("-"),
                    urwid.Button("Post Formatting Help", self.formatting_help),
                    urwid.Divider("-"),
                    urwid.Text(general_help)
                ])),
            title="?????",
            **frame_theme()
        )

        app.loop.widget = urwid.Overlay(
            widget, app.loop.widget,
            align=("relative", 50),
            valign=("relative", 50),
            width=30,
            height=("relative", 60)
        )


    def formatting_help(self, *_):
        """
        Pops a help window with formatting directives.
        """
        message = network.fake_message("\n\n".join(format_help))
        widget = OptionsMenu(
            urwid.ListBox(
                urwid.SimpleFocusListWalker([
                    *app.make_message_body(message, True)
                ])),
            title="Formatting Help",
            **frame_theme()
        )

        app.loop.widget = urwid.Overlay(
            widget, app.loop.widget,
            align=("relative", 50),
            valign=("relative", 50),
            width=("relative", 98),
            height=("relative", 60)
        )


    def set_color(self, button, value, color):
        if value == False:
            return
        network.user_update(color=color)


    def toggle_exit(self, button, value):
        self.prefs["dramatic_exit"] = value
        bbjrc("update", **self.prefs)


    def change_username(self, *_):
        self.loop.stop()
        run("clear", shell=True)
        def __loop(prompt, positive):
            new_name = sane_value("user_name", prompt, positive)
            if network.user_is_registered(new_name):
                return __loop("%s is already registered" % new_name, False)
            return new_name
        try:
            name = __loop("Choose a new username", True)
            network.user_update(user_name=name)
            motherfucking_rainbows("~~hello there %s~~" % name)
            sleep(0.8)
            self.loop.start()
            self.loop.widget = self.loop.widget[0]
            self.index()
            self.options_menu()
        except (KeyboardInterrupt, InterruptedError):
            self.loop.start()


    def change_password(self, *_):
        self.loop.stop()
        run("clear", shell=True)
        def __loop(prompt, positive):
            first = paren_prompt(prompt, positive)
            if first == "":
                confprompt = "Confirm empty password"
            else:
                confprompt = "Confirm it"
            second = paren_prompt(confprompt)
            if second != first:
                return __loop("Those didnt match. Try again", False)
            return first
        try:
            password = __loop("Choose a new password. Can be empty", True)
            network.user_update(auth_hash=network._hash(password))
            motherfucking_rainbows("SET NEW PASSWORD")
            sleep(0.8)
            self.loop.start()
            self.loop.widget = self.loop.widget[0]
            self.index()
            self.options_menu()
        except (KeyboardInterrupt, InterruptedError):
            self.loop.start()


    def live_time_render(self, editor, text, args):
        widget, key = args
        try:
            rendered = datetime.fromtimestamp(time()).strftime(text)
            self.prefs[key] = text
            bbjrc("update", **self.prefs)
        except:
            rendered = ("1", "Invalid Input")
        widget.set_text(rendered)


    def edit_width(self, editor, content):
        self.prefs["max_text_width"] = \
            int(content) if content else 0
        bbjrc("update", **self.prefs)


    def options_menu(self):
        """
        Create a popup for the user to configure their account and
        display settings.
        """
        editor_buttons = []
        edit_mode = []

        if network.user_auth:
            account_message = "Logged in as %s." % network.user_name
            user_colors = []
            for index, color in enumerate(colornames):
                urwid.RadioButton(
                    user_colors, color.title(),
                    network.user["color"] == index,
                    self.set_color, index)

            account_stuff = [
                urwid.Button("Relog", on_press=self.relog),
                urwid.Button("Go anonymous", on_press=self.unlog),
                urwid.Button("Change username", on_press=self.change_username),
                urwid.Button("Change password", on_press=self.change_password),
                urwid.Divider(),
                urwid.Text(("button", "Your color:")),
                urwid.Text(("default", "This color will show on your "
                            "post headers and when people quote you.")),
                urwid.Divider(),
                *user_colors
            ]
        else:
            account_message = "You're browsing anonymously, and cannot set account preferences."
            account_stuff = [urwid.Button("Login/Register", on_press=self.relog)]

        time_box = urwid.Text(self.timestring(time(), "time"))
        time_edit = Prompt(edit_text=self.prefs["time"])
        urwid.connect_signal(time_edit, "change", self.live_time_render, (time_box, "time"))

        date_box = urwid.Text(self.timestring(time(), "date"))
        date_edit = Prompt(edit_text=self.prefs["date"])
        urwid.connect_signal(date_edit, "change", self.live_time_render, (date_box, "date"))

        time_stuff = [
            urwid.Text(("button", "Time Format")),
            time_box, urwid.AttrMap(time_edit, "opt_prompt"),
            urwid.Divider(),
            urwid.Text(("button", "Date Format")),
            date_box, urwid.AttrMap(date_edit, "opt_prompt"),
        ]

        width_edit = urwid.IntEdit(default=self.prefs["max_text_width"])
        urwid.connect_signal(width_edit, "change", self.edit_width)

        editor_display = Prompt(edit_text=self.prefs["editor"])
        urwid.connect_signal(editor_display, "change", self.set_new_editor, editor_buttons)
        for editor in editors:
            urwid.RadioButton(
                editor_buttons, editor,
                state=self.prefs["editor"] == editor,
                on_state_change=self.set_new_editor,
                user_data=(editor, editor_display))

        urwid.RadioButton(
            edit_mode, "Integrate",
            state=self.prefs["integrate_external_editor"],
            on_state_change=self.set_editor_mode)

        urwid.RadioButton(
            edit_mode, "Overthrow",
            state=not self.prefs["integrate_external_editor"])

        widget = OptionsMenu(
            urwid.ListBox(
                urwid.SimpleFocusListWalker([
                    urwid.Text(("opt_header", "Account"), 'center'),
                    urwid.Text(account_message),
                    urwid.Divider(),
                    *account_stuff,
                    urwid.Divider("-"),
                    urwid.Text(("opt_header", "App"), 'center'),
                    urwid.Divider(),
                    urwid.CheckBox(
                        "Dump rainbows on exit",
                        state=self.prefs["dramatic_exit"],
                        on_state_change=self.toggle_exit
                    ),
                    urwid.Divider(),
                    *time_stuff,
                    urwid.Divider(),
                    urwid.Text(("button", "Max message width:")),
                    urwid.AttrMap(width_edit, "opt_prompt"),
                    urwid.Divider(),
                    urwid.Text(("button", "Text editor:")),
                    urwid.Text("You can type in your own command or use one of these presets."),
                    urwid.Divider(),
                    urwid.AttrMap(editor_display, "opt_prompt"),
                    *editor_buttons,
                    urwid.Divider(),
                    urwid.Text(("button", "External text editor mode:")),
                    urwid.Text("If you have problems using an external text editor, "
                               "set this to Overthrow."),
                    urwid.Divider(),
                    *edit_mode,
                    urwid.Divider("-"),
                ])
            ),
            title="Options",
            **frame_theme()
        )

        self.loop.widget = urwid.Overlay(
            widget, self.loop.widget,
            align="center",
            valign="middle",
            width=30,
            height=("relative", 75)
        )


    def footer_prompt(self, text, callback, *callback_args, extra_text=None):
        text = "(%s)> " % text
        widget = urwid.Columns([
            (len(text), urwid.AttrMap(urwid.Text(text), "bar")),
            FootPrompt(callback, *callback_args)
        ])

        if extra_text:
            widget = urwid.Pile([
                urwid.AttrMap(urwid.Text(extra_text), "2"),
                widget
            ])

        self.loop.widget.footer = widget
        self.loop.widget.focus_position = "footer"


    def reset_footer(self, _, from_temp):
        if from_temp and self.window_split:
            return
        try:
            self.set_default_footer()
            self.loop.widget.focus_position = "body"
        except:
            # just keep trying until the focus widget can handle it
            self.loop.set_alarm_in(0.5, self.reset_footer)


    def temp_footer_message(self, string, duration=3):
        self.loop.set_alarm_in(duration, self.reset_footer, True)
        self.set_footer(string)


    def overthrow_ext_edit(self, init_body=""):
        """
        Opens the external editor, but instead of integreating it into the app,
        stops the mainloop and blocks until the editor is killed. Returns the
        body of text the user composed.
        """
        self.loop.stop()
        descriptor, path = tempfile.mkstemp()
        with open(path, "w") as _:
            _.write(init_body)
        run("%s %s" % (self.prefs["editor"], path), shell=True)
        with open(path) as _:
            body = _.read()
        os.remove(path)
        self.loop.start()
        return body.strip()


    def compose(self, title=None, init_body=""):
        """
        Dispatches the appropriate composure mode and widget based on application
        context and user preferences.
        """
        if self.mode == "index" and not title:
            return self.footer_prompt("Title", self.compose)

        elif title:
            try: network.validate("title", title)
            except AssertionError as e:
                return self.footer_prompt(
                    "Title", self.compose, extra_text=e.description)

        if self.prefs["editor"] and not self.prefs["integrate_external_editor"]:
            body = self.overthrow_ext_edit(init_body)
            if not body:
                return self.temp_footer_message("EMPTY POST DISCARDED")
            params = {"body": body}

            if self.mode == "thread":
                endpoint = "reply"
                params.update({"thread_id": self.thread["thread_id"]})
            else:
                endpoint = "create"
                params.update({"title": title})

            network.request("thread_" + endpoint, **params)
            return self.refresh(True)

        if self.mode == "index":
            self.set_header('Composing "{}"', title)
            self.set_footer("[F1]Abort [F3]Formatting Help [Save and quit to submit your thread]")
            self.loop.widget = urwid.Overlay(
                urwid.LineBox(
                    ExternalEditor("thread_create", title=title),
                    title=self.prefs["editor"] or "",
                    **frame_theme()),
                self.loop.widget,
                align="center",
                valign="middle",
                width=("relative", 90),
                height=("relative", 80))

        elif self.mode == "thread":
            self.window_split=True
            self.set_header('Replying to "{}"', self.thread["title"])
            self.loop.widget.footer = urwid.Pile([
                urwid.AttrMap(urwid.Text(""), "bar"),
                urwid.BoxAdapter(
                    urwid.AttrMap(
                        urwid.LineBox(
                            ExternalEditor(
                                "thread_reply",
                                init_body=init_body,
                                thread_id=self.thread["thread_id"]),
                            **frame_theme()
                        ),
                        "bar"),
                    self.loop.screen_size[1] // 2),])
            self.switch_editor()


class MessageBody(urwid.Text):
    """
    An urwid.Text object that works with the BBJ formatting directives.
    """
    def __init__(self, message):
        text_objects = message["body"]
        result = []
        last_directive = None
        for paragraph in text_objects:
            for directive, body in paragraph:

                if directive in colornames:
                    color = str(colornames.index(directive))
                    result.append((color, body))

                elif directive in ["underline", "bold"]:
                    result.append((directive, body))

                elif directive == "linequote":
                    if directive != last_directive and result[-1][-1][-1] != "\n":
                        result.append(("default", "\n"))
                    result.append(("3", "%s\n" % body.strip()))

                elif directive == "quote":
                    if message["post_id"] == 0:
                        # Quotes in OP have no meaning, just insert them plainly
                        result.append(("default", ">>%s" % body))
                        continue
                    elif body == "0":
                        # quoting the OP, lets make it stand out a little
                        result.append(("50", ">>OP"))
                        continue

                    color = "2"
                    try:
                        # we can get this quote by its index in the thread
                        message = app.thread["messages"][int(body)]
                        user = app.usermap[message["author"]]
                        # try to get the user's color, if its default use the normal one
                        _c = user["color"]
                        if _c != 0:
                            color = str(_c)

                        if user != "anonymous" and user["user_name"] == network.user_name:
                            display = "[You]"
                            # bold it
                            color += "0"
                        else:
                            display = "[%s]" % user["user_name"]
                    except: # the quote may be garbage and refer to a nonexistant post
                        display = ""
                    result.append((color, ">>%s%s" % (body, display)))

                elif directive == "rainbow":
                    color = 1
                    for char in body:
                        if color == 7:
                            color = 1
                        result.append((str(color), char))
                        color += 1

                else:
                    result.append(("default", body))
                last_directive = directive
            result.append("\n\n")
        result.pop() # lazily ensure \n\n between paragraphs but not at the end
        super(MessageBody, self).__init__(result)


class Prompt(urwid.Edit):
    """
    Supports basic bashmacs keybinds. Key casing is
    ignored and ctrl/alt are treated the same. Only
    character-wise (not word-wise) movements are
    implemented.
    """
    def keypress(self, size, key):
        if not super(Prompt, self).keypress(size, key):
            return
        elif key[0:4] not in ["meta", "ctrl"]:
            return key

        column = self.get_cursor_coords((app.loop.screen_size[0],))[0]
        text = self.get_edit_text()
        key = key[-1].lower()

        if key == "u":
            self.set_edit_pos(0)
            self.set_edit_text(text[column:])

        elif key == "k":
            self.set_edit_text(text[:column])

        elif key == "f":
            self.keypress(size, "right")

        elif key == "b":
            self.keypress(size, "left")

        elif key == "a":
            self.set_edit_pos(0)

        elif key == "e":
            self.set_edit_pos(len(text))

        elif key == "d":
            self.set_edit_text(text[0:column] + text[column+1:])

        return key


class FootPrompt(Prompt):
    def __init__(self, callback, *callback_args):
        super(FootPrompt, self).__init__()
        self.callback = callback
        self.args = callback_args


    def keypress(self, size, key):
        super(FootPrompt, self).keypress(size, key)
        if key == "enter":
            app.loop.widget.focus_position = "body"
            app.set_default_footer()
            self.callback(self.get_edit_text(), *self.args)
        elif key.lower() in ["esc", "ctrl g", "ctrl c"]:
            app.loop.widget.focus_position = "body"
            app.set_default_footer()


class ExternalEditor(urwid.Terminal):
    def __init__(self, endpoint, **params):
        self.file_descriptor, self.path = tempfile.mkstemp()
        with open(self.path, "w") as _:
            if params.get("init_body"):
                init_body = params.pop("init_body")
            else:
                init_body = ""
            _.write(init_body)

        self.endpoint = endpoint
        self.params = params
        env = os.environ
        # barring this, programs will happily spit out unicode chars which
        # urwid+python3 seem to choke on. This seems to be a bug on urwid's
        # behalf. Users who take issue to programs trying to supress unicode
        # should use the options menu to switch to Overthrow mode.
        env.update({"LANG": "POSIX"})
        command = ["bash", "-c", "{} {}; echo Press any key to kill this window...".format(
            app.prefs["editor"], self.path)]
        super(ExternalEditor, self).__init__(command, env, app.loop, "f1")


    def keypress(self, size, key):
        if self.terminated:
            app.close_editor()
            with open(self.path) as _:
                body = _.read().strip()
            os.remove(self.path)

            if body and not re.search("^>>[0-9]+$", body):
                self.params.update({"body": body})
                network.request(self.endpoint, **self.params)
                return app.refresh(True)
            else:
                return app.temp_footer_message("EMPTY POST DISCARDED")

        elif key not in ["f1", "f2", "f3"]:
            return super(ExternalEditor, self).keypress(size, key)

        elif key == "f1":
            self.terminate()
            app.close_editor()
            app.refresh()
        elif key == "f2":
            app.switch_editor()
        elif key == "f3":
            app.formatting_help()


    def __del__(self):
        """
        Make damn sure we scoop up after ourselves here...
        """
        try:
            os.remove(self.path)
        except FileNotFoundError:
            pass


class OptionsMenu(urwid.LineBox):
    def keypress(self, size, key):
        if key == "esc":
            app.loop.widget = app.loop.widget[0]
        # try to let the base class handle the key, if not, we'll take over
        elif not super(OptionsMenu, self).keypress(size, key):
            return
        elif key in ["shift down", "J", "N"]:
            for x in range(5):
                self.keypress(size, "down")
        elif key in ["shift up", "K", "P"]:
            for x in range(5):
                self.keypress(size, "up")
        elif key.lower() in ["left", "h", "q"]:
            app.loop.widget = app.loop.widget[0]
        elif key.lower() in ["right", "l"]:
            return self.keypress(size, "enter")
        elif key in ["ctrl n", "j", "n"]:
            return self.keypress(size, "down")
        elif key in ["ctrl p", "k", "p"]:
            return self.keypress(size, "up")


class ActionBox(urwid.ListBox):
    """
    The listwalker used by all the browsing pages. Most of the application
    takes place in an instance of this box. Handles many keybinds.
    """
    def keypress(self, size, key):
        super(ActionBox, self).keypress(size, key)

        if key == "f2":
            app.switch_editor()

        elif key in ["j", "n", "ctrl n"]:
            self._keypress_down(size)

        elif key in ["k", "p", "ctrl p"]:
            self._keypress_up(size)

        elif key in ["shift down", "J", "N"]:
            for x in range(5):
                self._keypress_down(size)

        elif key in ["shift up", "K", "P"]:
            for x in range(5):
                self._keypress_up(size)

        elif key in ["h", "left"]:
            app.back()

        elif key in ["l", "right"]:
            self.keypress(size, "enter")

        elif key == "b":
            self.change_focus(size, len(app.walker) - 1)

        elif key == "t":
            self.change_focus(size, 0)

        elif key in ["c", "R", "+"]:
            app.compose()

        elif key == "r":
            app.refresh()

        elif key == "o":
            app.options_menu()

        elif key == "?":
            app.general_help()

        elif key.lower() == "q":
            app.back(True)


def frilly_exit():
    """
    Exit with some flair. Will fill the screen with rainbows
    and shit, or just say bye, depending on the user's bbjrc
    setting, `dramatic_exit`
    """
    app.loop.stop()
    if app.prefs["dramatic_exit"]:
        width, height = app.loop.screen_size
        for x in range(height - 1):
            motherfucking_rainbows(
                "".join([choice([" ", choice(punctuation)])
                        for x in range(width)]
                ))
        out = "  ~~CoMeE BaCkK SooOn~~  0000000"
        motherfucking_rainbows(out.zfill(width))
    else:
        run("clear", shell=True)
        motherfucking_rainbows("Come back soon! <3")
    exit()


def cute_button(label, callback=None, data=None):
    """
    Urwid's default buttons are shit, and they have ugly borders.
    This function returns buttons that are a bit easier to love.
    """
    button = urwid.Button("", callback, data)
    super(urwid.Button, button).__init__(
        urwid.SelectableIcon(label))
    return button


def urwid_rainbows(string, bold=False):
    """
    Same as below, but instead of printing rainbow text, returns
    a markup list suitable for urwid's Text contructor.
    """
    colors = [str(x) for x in range(1, 7)]
    if bold: colors = [(c + "0") for c in colors]
    return urwid.Text([(choice(colors), char) for char in string])


def motherfucking_rainbows(string, inputmode=False, end="\n"):
    """
    I cANtT FeELLE MyYE FACECsEE ANYrrMOROeeee
    """
    for character in string:
        print(choice(colors) + character, end="")
    print('\033[0m', end="")
    if inputmode:
        return input("")
    return print(end, end="")


def paren_prompt(text, positive=True, choices=[]):
    """
    input(), but riced the fuck out. Changes color depending on
    the value of positive (blue/green for good stuff, red/yellow
    for bad stuff like invalid input), and has a multiple choice
    system capable of rejecting unavailable choices and highlighting
    their first characters.
    """
    end = text[-1]
    if end != "?" and end in punctuation:
        text = text[0:-1]

    mood = ("\033[1;36m", "\033[1;32m") if positive \
           else ("\033[1;31m", "\033[1;33m")

    if choices:
        prompt = "%s{" % mood[0]
        for choice in choices:
            prompt += "{0}[{1}{0}]{2}{3} ".format(
                "\033[1;35m", choice[0], mood[1], choice[1:])
        formatted_choices = prompt[:-1] + ("%s}" % mood[0])
    else:
        formatted_choices = ""

    try:
        response = input("{0}({1}{2}{0}){3}> \033[0m".format(
            *mood, text, formatted_choices))
        if not choices:
            return response
        elif response == "":
            response = " "
        char = response.lower()[0]
        if char in [c[0] for c in choices]:
            return char
        return paren_prompt("Invalid choice", False, choices)

    except EOFError:
        print("")
        return ""


def sane_value(key, prompt, positive=True, return_empty=False):
    response = paren_prompt(prompt, positive)
    if return_empty and response == "":
        return response
    try: network.validate(key, response)
    except AssertionError as e:
        return sane_value(key, e.description, False)
    return response


def log_in():
    """
    Handles login or registration using an oldschool input()
    chain. The user is run through this before starting the
    curses app.
    """
    name = sane_value("user_name", "Username", return_empty=True)
    if name == "":
        motherfucking_rainbows("~~W3 4R3 4n0nYm0u5~~")
    else:
        # ConnectionRefusedError means registered but needs a
        # password, ValueError means we need to register the user.
        try:
            network.set_credentials(name, "")
            # make it easy for people who use an empty password =)
            motherfucking_rainbows("~~welcome back {}~~".format(network.user_name))

        except ConnectionRefusedError:
            def login_loop(prompt, positive):
                try:
                    password = paren_prompt(prompt, positive)
                    network.set_credentials(name, password)
                except ConnectionRefusedError:
                    login_loop("// R E J E C T E D //.", False)

            login_loop("Enter your password", True)
            motherfucking_rainbows("~~welcome back {}~~".format(network.user_name))

        except ValueError:
            motherfucking_rainbows("Nice to meet'cha, %s!" % name)
            response = paren_prompt(
                "Register as %s?" % name,
                choices=["yes!", "change name", "nevermind!"]
            )

            if response == "c":
                def nameloop(prompt, positive):
                    name = sane_value("user_name", prompt, positive)
                    if network.user_is_registered(name):
                        return nameloop("%s is already registered" % name, False)
                    return name
                name = nameloop("Pick a new name", True)

            elif response == "n":
                raise InterruptedError

            def password_loop(prompt, positive=True):
                response1 = paren_prompt(prompt, positive)
                if response1 == "":
                    confprompt = "Confirm empty password"
                else:
                    confprompt = "Confirm it"
                response2 = paren_prompt(confprompt)
                if response1 != response2:
                    return password_loop("Those didnt match. Try again", False)
                return response1

            password = password_loop("Enter a password. It can be empty if you want")
            network.user_register(name, password)
            motherfucking_rainbows("~~welcome to the party, %s!~~" % network.user_name)
    sleep(0.8) # let that confirmation message shine


def frame_theme(mode="default"):
    """
    Return the kwargs for a frame theme.
    """
    if mode == "default":
        return dict(
            tlcorner="@", trcorner="@", blcorner="@", brcorner="@",
            tline="=", bline="=", lline="|", rline="|"
        )



def bbjrc(mode, **params):
    """
    Maintains a user a preferences file, setting or returning
    values depending on `mode`.
    """
    path = os.path.join(os.getenv("HOME"), ".bbjrc")
    try:
        # load it up
        with open(path, "r") as _in:
            values = json.load(_in)
        # update it with new keys if necessary
        for key, default_value in default_prefs.items():
            if key not in values:
                values[key] = default_value
    # else make one
    except FileNotFoundError:
        values = default_prefs

    values.update(params)
    # we always write
    with open(path, "w") as _out:
        json.dump(values, _out)

    return values


def ignore(*_, **__):
    """
    The blackness of my soul.
    """
    pass


def main():
    global app
    app = App()
    app.usermap.update(network.user)
    run("clear", shell=True)
    motherfucking_rainbows(obnoxious_logo)
    print(welcome)
    try:
        log_in()
        app.loop.run()
    except (InterruptedError, KeyboardInterrupt):
        frilly_exit()


if __name__ == "__main__":
    main()
