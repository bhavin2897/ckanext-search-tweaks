import requests
import ckan.plugins.toolkit as tk

from xml.etree import ElementTree as ET

import logging

log = logging.getLogger(__name__)



def resolve_inchi_key(molecule_name):
    """Fetch InChIKey from PubChem for the given molecule name.
    Returns InChiKey as text string"""

    base_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name"
    property_path = "/property/InChIKey/xml"
    url = f"{base_url}/{molecule_name}{property_path}"

    try:
        response = requests.get(url)

        if response.status_code == 200:
            tree = ET.fromstring(response.text)

            # Define the namespace
            namespaces = {
                "pug": "http://pubchem.ncbi.nlm.nih.gov/pug_rest"
            }

            # Find the InChIKey using the namespace
            inchikey = tree.find(".//pug:InChIKey", namespaces)
            if inchikey is not None and inchikey.text:
                log.debug(f"InChIKey found: {inchikey.text}")
            else:
                log.debug("InChIKey not found in the XML response.")
        return inchikey.text

    except Exception as e:
        log.error(f"Error resolving InChIKey for '{molecule_name}': {e}")
    return None


def custom_molecule_search(context, data_dict):
    """Custom search logic for molecule datasets.
    returns data dictionary with inchi_key when available"""
    search_query = data_dict.get('q', '').strip()

    if search_query:
        # Resolve molecule name to InChIKey
        inchikey = resolve_inchi_key(search_query)

        if inchikey:
            # Update search query to search by InChIKey in Solr
            data_dict['q'] = f'{inchikey}'


        else:
            log.debug(f"InChIKey not found for molecule name: {search_query}")
            raise tk.ValidationError(
                {"q": [f"Could not resolve InChIKey for molecule name '{search_query}'"]}
            )

    # Call default search action
    # return tk.get_action('package_search')(context, data_dict)
    return data_dict
