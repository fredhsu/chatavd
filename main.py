import json
from fasthtml.common import (
    Article,
    Body,
    Pre,
    Footer,
    Header,
    Form,
    Div,
    Section,
    Dialog,
    Button,
    Group,
    Input,
    serve,
    P,
    Code,
    H1,
    H2,
    H3,
    Ul,
    Li,
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

sample_chat_prompts = [
    "How many bgp neighbors does dc1-leaf1a have?",
    "What VRFs are configured on dc1-leaf2b?",
]


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

    # print(msg)

    context_button = Button(
        "Switch Config",
        hx_get=f"/modal/{msg_idx}",
        hx_target="#modals-here",
        hx_trigger="click",
        data_bs_toggle="modal",
        data_bs_target="#modals-here",
        role="button",
        cls="secondary",
    )

    footer = None
    if msg["context"] != "":
        context = json.loads(msg["context"])
        print(f"Context has {len(context)} results:\n")
        footer = (
            Footer("Click here to see the relevant switch config ")(context_button)
            if msg["role"] != "user"
            else None
        )
    # context = Button("Context")
    return Article(
        Header(hdr),
        text,
        footer,
        id=f"chat-message-{msg_idx}",
        cls="prose",
        **stream_args if generating else {},
    )


def ChatInput():
    return Input(
        name="msg",
        id="msg-input",
        value="How many BGP neighbors does dc1-spine1 have?",
        # cls="input input-bordered flex-grow",
        cls="input input-bordered flex-grow mr-2 min-w-0",
        hx_swap_oob="true",
    )


@app.get("/close_modal")
def CloseModal():
    return  # Dialog(open=False)


def parse_json(json_string):
    try:
        return json.loads(json_string)[0]["hostname"]
    except json.JSONDecodeError:
        return {}


@app.get("/modal/{msg_idx}")
def modal(msg_idx: int):
    context = json.loads(messages[msg_idx]["context"])
    print(f"Context has {len(context)} results:\n")
    hostname = json.loads(messages[msg_idx]["context"])[0]["hostname"]
    config = get_config(hostname)
    return Dialog(
        Article(
            P(config)(
                Footer(
                    Button("Close"),
                    hx_get="/close_modal",
                    hx_target="#modal",
                    hx_trigger="click",
                    hx_swap="outerHTML",
                    data_bs_dismiss="modal",
                )
            )
        ),
        open=True,
        id="modal",
    )


@app.get("/chat_message/{msg_idx}")
def get_chat_message(msg_idx: int):
    if msg_idx >= len(messages):
        return ""
    return ChatMessage(msg_idx)


@app.get("/config/{hostname}")
def get_config(hostname: str):
    import libsql_experimental as libsql
    import os

    url = os.environ.get("TURSO_DATABASE_URL")
    auth_token = os.environ.get("TURSO_AUTH_TOKEN")
    conn = libsql.connect(database=url, auth_token=auth_token)
    config = conn.execute(
        f"SELECT config FROM configs WHERE hostname = '{hostname}'"
    ).fetchone()
    print(config)

    return Pre(Code(config))


@app.get("/")  # pyright: ignore
def home():
    # insert some sample queries here
    heading = (
        H1("ChatAVD"),
        (
            P(
                "Welcome to the ChatAVD demo. This demo uses a RAG system that has been \
            loaded with the output from generating docs and configs from the AVD \
            L3LS example. The example consists of:"
            )(H3("Spines")),
            (Ul(Li("dc1-spine1f"), Li("dc1-spine2"))),
            (H3("L3 leaf switches")),
            (
                Ul(
                    Li("dc1-leaf1a"),
                    Li("dc1-leaf1b"),
                    Li("dc1-leaf2a"),
                    Li("dc1-leaf2b"),
                )
            ),
            (H3("L2 leaf switches")),
            (Ul(Li("dc1-leaf1c"), (Li("dc1-leaf2c")))),
            (
                P(
                    "Asking how many bgp neighbors for the L3 \
            leaf switches should answer 5, whereas for the L2 should respond with \
            'I don't know'. There can be hallucinations so you may not get the expected answer. \
            Once the answer is found, the related switch config can be viewed to confirm the answer. \
            Due to some bugs the switch configs are not always the most relevant 😊."
                )
            ),
        ),
    )
    chat_header = Article(H2("Sample chat prompts (click to try):"), cls="prose")
    dialog = Dialog(Article(Header(), P("hello")))
    modals = Div(id="modals-here", cls="modal modal-blur")
    sample_chats = Section(
        Article(
            P(sample_chat_prompts[0]),
            hx_get="/sample_chat/0",
            hx_target="#msg-input",
        ),
        Article(
            P(sample_chat_prompts[1]),
            hx_get="/sample_chat/1",
            hx_target="#msg-input",
        ),
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
    page = Div(
        heading,
        modals,
        chat_header,
        sample_chats,
        dialog,
        chat_messages,
        form,
        cls="max-w-6xl mx-auto",
    )
    # add the json output here as a box that can be replaced and hidden
    return Body(Div(page, cls="container mx-auto p-4", role="main"))


@app.get("/sample_chat/{idx}")
def sample_chat(idx: int):
    return update_chat_input(sample_chat_prompts[idx])


def update_chat_input(value):
    return Input(
        name="msg",
        id="msg-input",
        value=value,
        cls="input input-bordered flex-grow mr-2 min-w-0",
        hx_swap_oob="true",
    )


# run chat model in a different thread
@threaded  # pyright: ignore
def get_response(r, idx):
    context = ""
    for chunk in r:
        if "answer" in chunk:
            messages[idx]["content"] += chunk["answer"]
        if "context" in chunk:
            context += chunk["context"]
    messages[idx]["context"] = context
    messages[idx]["generating"] = False
    print("finished getting response")


@app.post("/")
def post(msg: str):
    idx = len(messages)
    messages.append({"role": "user", "content": msg.rstrip(), "context": ""})
    # get response from chat model
    messages.append(
        {"role": "assistant", "generating": True, "content": "", "context": ""}
    )
    response = avdrag.get_response(msg)
    context = get_response(response, idx + 1)
    print(context)

    return (
        ChatMessage(idx),  # The user's message
        ChatMessage(idx + 1),  # The chatbot's response
        ChatInput(),
    )  # And clear the input field via an OOB swap


serve(host="0.0.0.0", port=8080)
