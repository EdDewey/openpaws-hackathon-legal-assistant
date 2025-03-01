This is a project from the 2025 Code for Compassion Hackathon.

- What: 
  - A simple RAG app to help formulate legal complaints relevant to animal welfare
  - The intended use case is to help prepare the bones of an argument, for example in order to get a lawyer interested in getting the rest of the way pro bono
  - It outputs
    - an overall strategy
    - a draft complaint
    - a list of TODOs for the user, mostly further research and confirmations they should do.
- Why:
  - There are a lot of people doing fairly small-bore legal work out there and we would like to support that
- How:
  - It's a LangGraph app, calling an OpenAI model on Azure, with a UI through Streamlit
  - Context can be provided automatically by scraping `animallaw.info`, or explicitly by the user providing text files
- Does it work:
  - Open question!  Someone who has nonzero domain knowledge should probably QA it.
  - The scraper is very unreliable (and fails silently).  That's too bad, since context seems to help when it works.

### Running it

This is only tested with python 3.12/

```commandline
$ cp env-template .env
... fill in .env file with secrets ...
$ source venv/bin/activate
$ pip install -r requirements.txt
$ python -m streamlit run app.py
```

### Demo

Since the UI is almost static, we have provided a demo in pdf form in this repository.

### Where to from here?

Examples of complaints seem to be valuable for this sort of application.  And there turn out to be a lot of repositories of legal information relevant to animals available online, but they are not easy to query and apparently lack public APIs.

If we were doing it all again, we would probably focus on the data-ingestion problem - grabbing data from existing animal-focus data repositories (or maybe even from PACER) and putting them into a knowledge base for effective RAGing.
