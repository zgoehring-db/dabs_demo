"""DABs demo app: minimal chat against a Databricks Foundation Model endpoint.

What this demonstrates:
- A Databricks App deployed via DABs (no manual app config in the UI)
- Streamlit chat UI with streaming responses
- The app's own identity (a service principal) calls the serving endpoint —
  authenticated automatically because the bundle binds a serving-endpoint
  resource to the app (see databricks.yml -> resources.apps.hello_app.resources)
- The *viewing* user's identity is read from the X-Forwarded-* headers
  Databricks injects on every request
"""

import os

import streamlit as st
from databricks.sdk import WorkspaceClient
from openai import OpenAI

# ----------------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------------
ENDPOINT = os.environ.get(
    "MODEL_ENDPOINT",
    "databricks-meta-llama-3-3-70b-instruct",
)

st.set_page_config(page_title="DABs demo — chat", page_icon="💬")
st.title("Chat with a Databricks model 💬")
st.caption(
    "Deployed via a Databricks Asset Bundle. The bundle config wires this "
    "app's identity to the serving endpoint — no API keys in code."
)


# ----------------------------------------------------------------------------
# OpenAI client pointed at Databricks Model Serving
# ----------------------------------------------------------------------------
@st.cache_resource
def get_client() -> OpenAI:
    """Build an OpenAI-compatible client authenticated as the app itself."""
    w = WorkspaceClient()
    return OpenAI(
        api_key=w.config.oauth_token().access_token,
        base_url=f"{w.config.host}/serving-endpoints",
    )


client = get_client()


# ----------------------------------------------------------------------------
# Identity helpers
# ----------------------------------------------------------------------------
def viewing_user() -> str:
    """The end-user looking at the app. Databricks proxies inject these
    headers on every request; if we're running locally without the proxy
    they won't be present.
    """
    try:
        h = st.context.headers
    except Exception:
        return "—"
    return (
        h.get("X-Forwarded-Email")
        or h.get("X-Forwarded-Preferred-Username")
        or h.get("X-Forwarded-User")
        or "—"
    )


@st.cache_data(ttl=300)
def app_identity() -> str:
    """The service principal the app is running as. Useful to show that
    it's distinct from the viewing user — the SP is what's calling the
    model endpoint, not the human."""
    try:
        return WorkspaceClient().current_user.me().display_name or "—"
    except Exception:
        return "—"


# ----------------------------------------------------------------------------
# Sidebar
# ----------------------------------------------------------------------------
with st.sidebar:
    st.subheader("App info")
    st.write(f"**Viewing as:** {viewing_user()}")
    st.write(f"**App identity:** {app_identity()}")
    st.write(f"**Endpoint:** `{ENDPOINT}`")
    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.rerun()


# ----------------------------------------------------------------------------
# Chat
# ----------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# Replay history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])


def stream_reply(messages):
    """Yield content chunks from the model's streamed response."""
    stream = client.chat.completions.create(
        model=ENDPOINT,
        messages=messages,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


if prompt := st.chat_input("Ask me anything"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        reply = st.write_stream(stream_reply(st.session_state.messages))
        st.session_state.messages.append({"role": "assistant", "content": reply})
