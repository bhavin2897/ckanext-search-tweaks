from __future__ import annotations

import logging

from typing import Any, Dict
import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
from ckan.lib.search.query import QUERY_FIELDS

from flask import jsonify
from ckanext.search_tweaks.controller import molecule_name_search as molecule_name_search
from . import cli, boost_preffered, feature_disabled
from .interfaces import ISearchTweaks

log = logging.getLogger(__name__)

SearchParams = Dict[str, Any]

CONFIG_QF = "ckanext.search_tweaks.common.qf"
CONFIG_FUZZY = "ckanext.search_tweaks.common.fuzzy_search.enabled"
CONFIG_FUZZY_DISTANCE = "ckanext.search_tweaks.common.fuzzy_search.distance"
CONFIG_MM = "ckanext.search_tweaks.common.mm"
CONFIG_FUZZY_KEEP_ORIGINAL = (
    "ckanext.search_tweaks.common.fuzzy_search.keep_original"
)

DEFAULT_QF = QUERY_FIELDS
DEFAULT_FUZZY = False
DEFAULT_FUZZY_DISTANCE = 1
DEFAULT_MM = "1"
DEFAULT_FUZZY_KEEP_ORIGINAL = True


class SearchTweaksPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IClick)
    plugins.implements(plugins.IPackageController, inherit=True)

    # IClick
    def get_commands(self):
        return cli.get_commands()

    # IPackageController

    def before_search(self, search_params: SearchParams):
        if feature_disabled("everything", search_params):
            return search_params

        search_params.setdefault("mm", tk.config.get(CONFIG_MM, DEFAULT_MM))

        if "defType" not in search_params:
            search_params["defType"] = "edismax"

        if boost_preffered() and search_params["defType"] == "edismax":
            _set_boost(search_params)

        else:
            _set_bf(search_params)

        # search based on PubChem Search when a string is provided & matches with Search
        if "fq" in search_params and search_params.get('q', '').strip():
            # Check if "+dataset_type:molecule" is in 'fq'
            # TODO: Comments or Logging debug comments should be removed

            if "+dataset_type:molecule" in search_params["fq"]:
                log.debug("Molecule search triggered for PubChem.")

                # Perform molecule search via PubChem
                data_dict = molecule_search_pubchem(search_params=search_params)

                if data_dict and 'q' in data_dict and data_dict['q']:
                    # Append new query to existing query
                    search_params['q'] = f"{search_params['q']} OR {data_dict['q']}"
                    log.debug(f"Updated search_params['q']: {search_params['q']}")
                else:
                    log.warning("No valid data_dict['q'] returned from molecule_search_pubchem.")
        else:
            pass
        #    log.debug("Search is empty and goes to default")

        _set_qf(search_params)
        _set_fuzzy(search_params)
        # log.debug(f"Searching from before search {search_params}")
        return search_params


def _set_boost(search_params: SearchParams) -> None:
    boost: list[str] = search_params.setdefault("boost", [])
    for plugin in plugins.PluginImplementations(ISearchTweaks):
        extra = plugin.get_search_boost_fn(search_params)
        if not extra:
            continue
        boost.append(extra)


def _set_bf(search_params: SearchParams) -> None:
    default_bf: str = search_params.get("bf") or "0"
    search_params.setdefault("bf", default_bf)
    for plugin in plugins.PluginImplementations(ISearchTweaks):
        extra_bf = plugin.get_search_boost_fn(search_params)
        if not extra_bf:
            continue
        search_params["bf"] = f"sum({search_params['bf']},{extra_bf})"


def _set_qf(search_params: SearchParams) -> None:
    if feature_disabled("qf", search_params):
        return

    default_qf: str = search_params.get("qf") or tk.config.get(
        CONFIG_QF, DEFAULT_QF
    )
    search_params.setdefault("qf", default_qf)
    for plugin in plugins.PluginImplementations(ISearchTweaks):
        extra_qf = plugin.get_extra_qf(search_params)
        if not extra_qf:
            continue
        search_params["qf"] += " " + extra_qf


def _set_fuzzy(search_params: SearchParams) -> None:
    if not tk.asbool(tk.config.get(CONFIG_FUZZY, DEFAULT_FUZZY)):
        return

    if feature_disabled("fuzzy", search_params):
        return

    distance = _get_fuzzy_distance()
    if not distance:
        return

    q = search_params.get("q")
    if not q:
        return

    if set(""":"'~""") & set(q):
        return

    fuzzy_q = " ".join(
        map(
            lambda s: f"{s}~{distance}"
            if s.isalpha() and s not in ("AND", "OR", "TO")
            else s,
            q.split(),
        )
    )
    if tk.asbool(
        tk.config.get(CONFIG_FUZZY_KEEP_ORIGINAL, DEFAULT_FUZZY_KEEP_ORIGINAL)
    ):
        search_params["q"] = f"({fuzzy_q}) OR ({q})"
    else:
        search_params["q"] = fuzzy_q


def _get_fuzzy_distance() -> int:
    distance = tk.asint(
        tk.config.get(CONFIG_FUZZY_DISTANCE, DEFAULT_FUZZY_DISTANCE)
    )
    if distance < 0:
        log.warning("Cannot use negative fuzzy distance: %s.", distance)
        distance = 0
    elif distance > 2:
        log.warning(
            "Cannot use fuzzy distance greater than 2: %s. Reduce it to top boundary",
            distance,
        )
        distance = 2
    return distance


def molecule_search_pubchem(search_params):
    """
    PubChem Molecule Search via Molecule Name when it is available.
    This function sends the dict to the logic in controller folder to search for the given Molecule name using PubChem API
    """

    data_dict = {
                'q': search_params['q'],
                'fq': 'type:molecule'
            }

    try:
        # Call custom search function
        data_dict = molecule_name_search.custom_molecule_search({}, data_dict)

        # log.debug(f"Search Results from Custom {data_dict}")

        return data_dict

    except tk.ValidationError as e:
        return jsonify({'error': str(e)}), 400


