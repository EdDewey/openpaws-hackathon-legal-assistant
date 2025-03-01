import requests
from functools import cache
import html_to_json

SCRAPED = set()


def build_url(material_type="All", combine_op="contains", query_string="", page=0):
    """Get a url for searching with"""
    keyword = query_string.replace(" ", "+")
    assert material_type in {"All", "Case", "Local Ordinance", "Pleading", "Statute"}
    assert combine_op in {"contains", "word"}
    return f"https://www.animallaw.info/filters?topic=All&species=All&type={material_type}&country=All&jurisdiction=All&{combine_op}=contains&keyword={keyword}&page={page}"


def parse_search_html_inner(html):
    entries = html_to_json.convert(html)["html"][0]["body"][0]["div"][2]["main"][0][
        "div"
    ][0]["div"][1]["table"][0]["tbody"][0]["tr"]
    parsed = [parse_search_entry(entry) for entry in entries]
    return [x for x in parsed if x is not None]


def parse_search_entry(entry):
    data = entry["td"]
    summary = None
    try:
        summary = data[4]["p"][0]["_value"]
    except KeyError:
        pass

    try:
        summary = data[4]["_value"]
    except KeyError:
        pass

    if summary is None:
        return
    href = data[0]["a"][0]["_attributes"]["href"]
    return {"summary": summary, "href": href}


def parse_search(html):
    try:
        return parse_search_html_inner(html)
    except Exception as e:
        print(e)
        return []


def get_href_url(href):
    return f"https://www.animallaw.info{href}"


def parse_content(html):
    paragraphs = html_to_json.convert(html)["html"][0]["body"][0]["div"][2]["main"][0][
        "article"
    ][0]["section"][0]["span"][0]["span"][0]["span"][0]["p"]
    output = ""
    for pp in paragraphs:
        try:
            text = pp["_value"]
            if isinstance(text, str):
                output += "\n\n" + text
        except:
            pass
    return output


@cache
def search_animal_law(query_string="", material_type="All"):
    """Seach for legal data from the animal law database.
    :param str query_string: text to search for.  It will just try to match each word.
    :param str material_type: The kind of result to get.  Must be among 'All', 'Case', 'Local Ordinance', 'Pleading', 'Statute'.  Defaults to 'All'.
    return: a list of entries in the database with their summaries"""
    url = build_url(material_type, "word", query_string)
    search_html = requests.get(url).text
    return parse_search(search_html)


@cache
def get_from_animal_law(href):
    """Retrieve detailed information from the animal law database.
    :param str href: a reference to the database article, as returned by the search_animal_law function.
    return: the full text of the data.
    """
    url = get_href_url(href)
    html = requests.get(url).text
    SCRAPED.add(url)
    return parse_content(html)


if __name__ == "__main__":
    # tests
    search_results = search_animal_law()
    assert search_results
    href = search_results[0]["href"]
    text = get_from_animal_law(href)
    assert text
