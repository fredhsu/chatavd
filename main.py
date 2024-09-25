import json
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
    threaded,
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

messages = []


def ChatMessage(msg_idx):
    msg = messages[msg_idx]
    text = "..." if msg["content"] == "" else msg["content"]
    hdr = "User: " if msg["role"] == "user" else "Bot: "
    generating = "generating" in messages[msg_idx] and messages[msg_idx]["generating"]
    stream_args = {
        "hx_trigger": "every 0.1s",
        "hx_swap": "outerHTML",
        "hx_get": f"/chat_message/{msg_idx}",
    }

    return Article(
        Header(hdr),
        text,
        id=f"chat-message-{msg_idx}",
        cls="prose",
        **stream_args if generating else {},
    )
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


@app.get("/chat_message/{msg_idx}")
def get_chat_message(msg_idx: int):
    if msg_idx >= len(messages):
        return ""
    return ChatMessage(msg_idx)


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
    chat_messages = Div(
        *[ChatMessage(i) for i in range(len(messages))],
        id="chatlist",
        cls="chat-box h-[73vh] overflow-y-auto",
    )
    form = Form(hx_post="/", hx_target="#chatlist", hx_swap="beforeend")(
        Group(
            ChatInput(),
            Button("Send"),
            # cls="flex, space-x-2, mt-2",
        ),
    )
    page = Div(chat_header, sample_chats, chat_messages, form, cls="max-w-6xl mx-auto")
    # add the json output here as a box that can be replaced and hidden
    return Body(Div(page, cls="container mx-auto p-4", role="main"))


# run chat model in a different thread
@threaded
def get_response(r, idx):
    for chunk in r:
        print(chunk["answer"])
        messages[idx]["content"] += chunk["answer"]
    messages[idx]["generating"] = False


@app.post("/")
def post(msg: str):
    idx = len(messages)
    messages.append({"role": "user", "content": msg.rstrip()})
    # get response from chat model
    messages.append({"role": "assistant", "generating": True, "content": ""})
    response = avdrag.get_response(msg)
    get_response(response, idx + 1)
    # response_text = response["answer"]
    # context_json = json.loads(response["context"])
    # could grab the hostname of the context and use that to lookup the config file

    # hostname = context_json["hostname"]
    # print(hostname)
    #
    # print("\n\nSending response")
    # print(response)

    return (
        ChatMessage(idx),  # The user's message
        ChatMessage(idx + 1),  # The chatbot's response
        ChatInput(),
    )  # And clear the input field via an OOB swap


serve(host="0.0.0.0", port=8080)
