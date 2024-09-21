from fasthtml.common import (
    Article,
    Body,
    Script,
    Link,
    Header,
    Form,
    Div,
    Section,
    Hidden,
    Button,
    Group,
    FastHTML,
    picolink,
    Input,
    serve,
    P,
    H1,
    H2,
    fast_app,
)
import avdrag

hdrs = (
    # picolink,
    # probably switch to using local tailwind
    # Link(href="css/output.css", rel="stylesheet"),
    # Script(src="https://cdn.tailwindcss.com"),
    # Script(
    #     src="https://cdn.jsdelivr.net/npm/@tailwindcss/typography@0.5.15/src/index.min.js"
    # ),
    # Link(
    #     rel="stylesheet",
    #     href="https://cdn.jsdelivr.net/npm/daisyui@4.11.1/dist/full.min.css",
    # ),
)

app, rt = fast_app(pico=True, hdrs=hdrs)


def ChatMessage(msg, user):
    hdr = "User: " if user else "Bot: "

    return Article(Header(hdr), msg)
    # bubble_class = "chat-bubble-primary" if user else "chat-bubble-secondary"
    # chat_class = "chat-end" if user else "chat-start"
    # return Div(cls=f"chat {chat_class}")(
    #     Div("user" if user else "assistant", cls="chat-header"),
    #     Div(msg, cls=f"chat-bubble {bubble_class}"),
    #     Hidden(msg, name="messages"),
    # )


def ChatInput():
    return Input(
        name="msg",
        id="msg-input",
        placeholder="Send a query",
        # cls="input input-bordered flex-grow",
        cls="input input-bordered flex-grow mr-2 min-w-0",
        hx_swap_oob="true",
    )


@app.get("/")  # pyright: ignore
def home():
    # insert some sample queries here
    chat_header = Article(H2("Sample chat prompts to try:"), cls="prose")
    sample_chats = Section(
        # Article(H2("Sample chat prompts to try:"), cls="prose"),
        # Div(P("How many bgp neighbors does dc1-leaf1a have?"), cls="card-body"),
        Article(P("How many bgp neighbors does dc1-leaf1a have?")),
        # cls="card bg-primary text-primary-content",
        # Div(P("What VRFs are configured on dc1-leaf2b?"), cls="card-body"),
        Article(P("What VRFs are configured on dc1-leaf2b?")),
        # cls="card bg-primary text-primary-content",
        cls="grid",
    )
    form = Form(hx_post=send, hx_target="#chatlist", hx_swap="beforeend")(
        Div(id="chatlist", cls="chat-box h-[73vh] overflow-y-auto"),
        Group(
            ChatInput(),
            Button("Send"),
            # cls="flex, space-x-2, mt-2",
        ),
    )
    page = Div(chat_header, sample_chats, form, cls="max-w-6xl mx-auto")
    # add the json output here as a box that can be replaced and hidden
    return Body(Div(page, cls="container mx-auto p-4", role="main"))


@app.post  # pyright: ignore
def send(msg: str, messages: list[str] | None = None):
    if not messages:
        messages = []
    messages.append(msg.rstrip())
    # get response from chat model
    response = avdrag.get_response(msg)
    response_text = response["answer"]
    return (
        ChatMessage(msg, True),  # The user's message
        ChatMessage(response_text.rstrip(), False),  # The chatbot's response
        ChatInput(),
    )  # And clear the input field via an OOB swap


serve(host="0.0.0.0", port=8080)
