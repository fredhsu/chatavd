from fasthtml.common import (
    Script,
    Link,
    Form,
    Div,
    Titled,
    Hidden,
    Button,
    Group,
    FastHTML,
    picolink,
    Input,
    serve,
)
import avdrag

hdrs = (
    picolink,
    Script(src="https://cdn.tailwindcss.com"),
    Link(
        rel="stylesheet",
        href="https://cdn.jsdelivr.net/npm/daisyui@4.11.1/dist/full.min.css",
    ),
)

app = FastHTML(hdrs=hdrs)


def ChatMessage(msg, user):
    bubble_class = "chat-bubble-primary" if user else "chat-bubble-secondary"
    chat_class = "chat-end" if user else "chat-start"
    return Div(cls=f"chat {chat_class}")(
        Div("user" if user else "assistant", cls="chat-header"),
        Div(msg, cls=f"chat-bubble {bubble_class}"),
        Hidden(msg, name="messages"),
    )


def ChatInput():
    return Input(
        name="msg",
        id="msg-input",
        placeholder="Type a message",
        cls="input input-bordered w-full",
        hx_swap_oob="true",
    )


@app.get("/")  # pyright: ignore
def home():
    # insert some sample queries here
    page = Form(hx_post=send, hx_target="#chatlist", hx_swap="beforeend")(
        Div(id="chatlist", cls="chat-box h-[73vh] overflow-y-auto"),
        Div(cls="flex space-x-2 mt-2")(
            Group(ChatInput(), Button("Send", cls="btn btn-primary"))
        ),
    )
    # add the json output here as a box that can be replaced and hidden
    return Titled("ChatAVD Demo", page)


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
