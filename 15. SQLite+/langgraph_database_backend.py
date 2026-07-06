from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_anthropic import ChatAnthropic
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
import sqlite3

load_dotenv()

llm = ChatAnthropic(model="claude-haiku-4-5-20251001")

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat_node(state: ChatState):
    messages = state['messages']
    response = llm.invoke(messages)
    return {"messages": [response]}

conn = sqlite3.connect(database='chatbot_db', check_same_thread=False)
# Checkpointer
checkpointer = SqliteSaver(conn=conn)

graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

chatbot = graph.compile(checkpointer=checkpointer)

# print(checkpointer.list(None))
def retrieve_all_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        # print(checkpoint)
        # print(checkpointer.config['configurable']['thread_id'])
        all_threads.add(checkpoint.config['configurable']['thread_id'])

    # print(list(all_threads))
    return list(all_threads)

# test
# CONFIG = {'configurable': {'thread_id': 'thread-1'}}

# response = chatbot.invoke(
#     {'messages':[HumanMessage(content='Hi My Name is Nikhil')]},
#     config = CONFIG
# )

# print(response)

# response = chatbot.invoke(
#     {'messages':[HumanMessage(content='What is my name?')]},
#     config = CONFIG
# )

# print(response)

# CONFIG = {'configurable': {'thread_id': 'thread-2'}}

# response = chatbot.invoke(
#     {'messages':[HumanMessage(content='Hi My Name is Sakshi')]},
#     config = CONFIG
# )

# print(response)

# response = chatbot.invoke(
#     {'messages':[HumanMessage(content='What is my name?')]},
#     config = CONFIG
# )

# print(response)