import os
import time

from azure.core.exceptions import HttpResponseError
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.tools import tool
from langchain_azure_ai.chat_models import AzureAIChatCompletionsModel
import weaviate
from weaviate.classes.init import Auth

import scraper

load_dotenv()
rest_endpoint = os.getenv("OPENPAWS_KNOWLEDGE_BASE_REST_ENDPOINT")
ReadOnly_API_Key = os.getenv("OPENPAWS_KNOWLEDGE_BASE_READONLY_API_KEY")
paws_openai_api_key = os.getenv("OPENPAWS_OPEN_AI_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
GPT4o_API_Key = os.getenv("AZURE_OPENAI_KEY")


# Connect with read-only API key
client = weaviate.connect_to_weaviate_cloud(
    cluster_url=rest_endpoint,
    auth_credentials=Auth.api_key(ReadOnly_API_Key),
    headers={"X-OpenAI-Api-Key": paws_openai_api_key},
)


def search_animal_knowledge(collection: str, query: str) -> list:
    return (
        client.collections.get(collection)
        .query.near_text(query=query, limit=3)
        .objects
    )


@tool
def search_animal_content(query: str):
    """Look up content related to animal welfare, such as laws and articles."""
    qr = search_animal_knowledge("Content", query)
    texts = [x.properties["main_text"] for x in qr]
    return "\n".join(texts)


@tool
def search_animal_events(query: str):
    """Look up events related to animal welfare, such as protests"""
    qr = search_animal_knowledge("Event", query)
    texts = [x.properties["description"] for x in qr]
    return "\n".join(texts)


@tool
def search_animal_entities(query: str):
    """Look up entities related to animal welfare, such as animal welfare organizations or agribusinesses."""
    qr = search_animal_knowledge("Entities", query)
    texts = [x.properties["description"] for x in qr]
    return "\n".join(texts)


@tool
def search_legal_database(query_string="", material_type="All"):
    """Seach for legal data from the animal law database.
    :param str query_string: text to search for.  It will just try to match each word.
    :param str material_type: The kind of result to get.  Must be among 'All', 'Case', 'Local Ordinance', 'Pleading', 'Statute'.  Defaults to 'All'.
    return: a list of entries in the database with their summaries"""
    return scraper.search_animal_law(query_string, material_type)


@tool
def get_from_legal_database(href):
    """Retrieve detailed information from the animal law database.
    :param str href: a reference to the database article, as returned by the search_animal_law function.
    return: the full text of the data.

    example:
    ```
    search_result = search_legal_database("bear captivity")
    # results is `[{"href": "/case/bear_rescue", "summary": "... some interesting information"}, ...]`
    get_from_legal_database("/case/bear_rescue")
    """
    return scraper.get_from_animal_law(href)


tools = [
    search_legal_database,
    get_from_legal_database,
    search_animal_content,
    search_animal_events,
    search_animal_entities,
]

azure_model = AzureAIChatCompletionsModel(
    endpoint="https://foundryhub25610398881.openai.azure.com/openai/deployments/gpt-4o",
    credential=GPT4o_API_Key,
    model="gpt-4o",
    api_version="2024-08-01-preview",
)


def get_agent():
    checkpointer = MemorySaver()
    return create_react_agent(
        model=azure_model,
        tools=tools,
        checkpointer=checkpointer,
        prompt="You are a legal assistant helping an animal welfare activist by doing research and formulating legal arguments.  You have access to a database of legal actions and cases related to animals",
    )


def use_the_agent(azure_app, text: str, debug=True):
    time.sleep(5)
    try:
        final_state = azure_app.invoke(
            {"messages": [{"role": "user", "content": text}]},
            config={"configurable": {"thread_id": 5}},
            debug=debug,
        )
    except HttpResponseError:
        time.sleep(40)  # there is throttling to avoid
        final_state = azure_app.invoke(
            {"messages": [{"role": "user", "content": text}]},
            config={"configurable": {"thread_id": 5}},
            debug=debug,
        )
    return final_state


def extract_from_final_state(final_state) -> str:
    return final_state["messages"][-1].content


def run_script(azure_agent, situation: str, additional_data: list[str] = None):
    use_the_agent(azure_agent, intro_message)

    final_state = use_the_agent(
        azure_agent, scenario_message.format(situation=situation)
    )
    strategy = extract_from_final_state(final_state)

    use_the_agent(azure_agent, scraper_message)
    if not scraper.SCRAPED:
        use_the_agent(
            azure_agent,
            "Try again with a different (shorter, less strict) query.  Maybe try the empty string.",
        )
    use_the_agent(azure_agent, summarizer_message)
    for datum in additional_data or []:
        use_the_agent(azure_agent, additional_data_message.format(example=datum))

    complaint_chunks = []
    final_state = use_the_agent(azure_agent, complaint_message)
    complaint_chunks.append(extract_from_final_state(final_state))
    while (
        not "done" in complaint_chunks[-1][-20:].lower()
    ):  # obvious possible bug, but whatever
        final_state = use_the_agent(azure_agent, continue_message)
        complaint_chunks.append(extract_from_final_state(final_state))
    complaint = "\n".join(complaint_chunks)

    final_state = use_the_agent(azure_agent, todo_message)
    todo = extract_from_final_state(final_state)

    return {
        "strategy": strategy,
        "complaint": complaint,
        "todo": todo,
        "urls": scraper.SCRAPED,
    }


# Messages

intro_message = """
I want to take legal action against someone mistreating animals.  I will describe my problem.  Then I want you to
1. Outline a general course of legal action
2. Use your search_legal_database and get_from_legal_database tools to find relevant similar cases
3. Summarize the complaints in those cases, from the point of view of imitating them.  Take into account whether the complaint was successful, if that information is available.
4. Based on the results from 1. and 3., write a first draft of my complaint.
5. Write me a list of TODOs for further research of confirmations I should do before submitting my complaint. 

I will talk you through each of these steps.
"""

scenario_message = """
Here is my situation: 

{situation}

First, 1. outline a general course of legal action.  I'll use this to try to get a pro-bono lawyer interested and save them some time.
"""

scraper_message = """
Now
2. Use your search_legal_database and get_from_legal_database tools to find relevant similar cases
Try to get at least two cases.  The search function is very strict, so keep queries simple.  E.G. instead of "endangered animal mistreatment" try "mistreatment".
"""

summarizer_message = """
Now
3. Summarize the complaints in those cases, from the point of view of imitating them.  Take into account whether the complaint was successful, if that information is available.
"""

additional_data_message = """
Here is another relevant example.  As before, summarize from the point of view of imitating it.

{example}
"""

complaint_message = """
Now
4. Based on the results from 1. and 3., write a first draft of my complaint.
If you are done, end you response with 'done'.
"""

continue_message = """
If you did not finish, please continue.  Otherwise, respond with the word 'done'.
"""

todo_message = """Now
5. Write me a list of TODOs for further research of confirmations I should do before submitting my complaint. 
"""
