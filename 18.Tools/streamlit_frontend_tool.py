import streamlit as st
from langgraph_tool_backend import chatbot, retrieve_all_threads
from langchain_core.messages import HumanMessage, AIMessage,ToolMessage
import uuid

# **************************************** Utility Functions *************************

def generate_thread_id():
    thread_id = str(uuid.uuid4())
    return thread_id

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_thread(st.session_state['thread_id'])
    st.session_state['message_history'] = []

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def load_conversation(thread_id):
    return chatbot.get_state(config={'configurable': {'thread_id': thread_id}}).values.get('messages', [])

# **************************************** Session Setup ******************************

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = retrieve_all_threads()

add_thread(st.session_state['thread_id'])

# **************************************** Sidebar UI *********************************

st.sidebar.title("LangGraph Chatbot")

if st.sidebar.button('New Chat'):
    reset_chat()

st.sidebar.header('My Conversations')

for thread_id in st.session_state['chat_threads'][::-1]:
    messages = load_conversation(thread_id)
    first_msg = messages[0].content if messages else str(thread_id)
    label = first_msg[:40] + ('...' if len(first_msg) > 40 else '')
    
    if st.sidebar.button(label, key=thread_id):
        st.session_state['thread_id'] = thread_id
        temp_messages = []
        for msg in messages:
            role = 'user' if isinstance(msg, HumanMessage) else 'assistant'
            temp_messages.append({'role': role, 'content': msg.content})
        st.session_state['message_history'] = temp_messages

# **************************************** Main UI ************************************

# loading the conversation history
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

user_input = st.chat_input('Type here')

if user_input:

    # first add the message to message_history
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)

    CONFIG = {
        "configurable": {"thread_id": st.session_state['thread_id']},
        "metadata": {
            "thread_id": st.session_state['thread_id']
        },
        "run_name": "chat_turn"
    }

    # first add the message to message_history    
    with st.chat_message('assistant'):
        # Use a mutable holder so the generator can set/modify it
        status_holder = {"box": None}

        def ai_only_stream():
            for message_chunk, metadata in chatbot.stream(
                {'messages':[HumanMessage(content=user_input)]},
                config = CONFIG,
                stream_mode = 'messages'
            ):
                # Lazily create & pdate the SAME status container when any tool runs
                if isinstance(message_chunk, ToolMessage):
                    tool_name = getattr(message_chunk, "name", "tool")
                    if status_holder["box"] is None:
                        status_holder["box"] = st.status(
                            f"🔧 Using '{tool_name} ...", expanded=True
                        )
                    status_holder["box"].update(
                    label=f"✅ Used '{tool_name}'",
                    state="complete",
                    expanded=False
                    )
                    # else:
                    #     status_holder["box"].update(
                    #         label=f"🔧 Using '{tool_name} ...",
                    #         state="running",
                    #         expanded=True
                    #     )

                # Stream ONLY assistant tokens
                if isinstance(message_chunk, AIMessage):
                    # Yield only assistent tokens
                    # yield message_chunk.content
                    content = message_chunk.content
                    if isinstance(content, str):
                        yield content
                    else:
                        for block in content:
                            if isinstance(block, dict) and block.get('type') == 'text':
                                yield block.get('text', '')

        ai_message = st.write_stream(ai_only_stream())

    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})