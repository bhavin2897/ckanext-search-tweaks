from __future__ import annotations
import json
from typing import Any
import ckan.plugins as p
import ckan.plugins.toolkit as tk
from ckan.exceptions import CkanConfigurationException

CONFIG_FORM_DEFINITION = "ckanext.search_tweaks.advanced_search.fields"
CONFIG_FIELD_ORDER = "ckanext.search_tweaks.advanced_search.order"

DEFAULT_FORM_DEFINITION = json.dumps(
    {
        "title": {
            "type": "text",
            "label": "Title",
            "placeholder": "Enter a search term",
        },

        "notes": {
            "type": "text",
            "label": "Description",
            "placeholder": "Enter a search term",
        },

        "inchi":{
            "type": "text",
            "label": "InChI",
            "placeholder": "Enter a search term",
            "default" : True,
        },

        "inchi_key":{
            "type": "text",
            "label": "InChIKey",
            "placeholder": "Enter a search term",
        },

        "measurement_technique": {
            "type": "text",
            "label": "Measurement Technique",
            "placeholder": "ex:  ",
        }

    }
)
DEFAULT_FIELD_ORDER = None

DEFAULT_FIELD_ORDER_IMAGE = None


DEFAULT_FORM_DEFINITION_IMAGE = json.dumps(
    {
            "inchi_key":{
            "type": "text",
            "label": "InChIKey",
            "placeholder": "Enter a search term"
    }
    }
)

def form_config():
    definition = json.loads(
        tk.config.get(CONFIG_FORM_DEFINITION, DEFAULT_FORM_DEFINITION)
    )
    order = tk.aslist(tk.config.get(CONFIG_FIELD_ORDER, DEFAULT_FIELD_ORDER))
    if not order:
        order = list(definition)
    return {
        "definitions": definition,
        "order": order,
    }


def form_config_image():

    definition = json.loads(
        tk.config.get(CONFIG_FORM_DEFINITION, DEFAULT_FORM_DEFINITION_IMAGE)
    )
    order = tk.aslist(tk.config.get(CONFIG_FIELD_ORDER, DEFAULT_FIELD_ORDER_IMAGE))
    if not order:
        order = list(definition)
    return {
        "definitions": definition,
        "order": order,
    }


class AdvancedSearchPlugin(p.SingletonPlugin):
    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.IConfigurable)
    p.implements(p.ITemplateHelpers)
    p.implements(p.IPackageController, inherit=True)

    # IConfigurer

    def update_config(self, config):
        tk.add_template_directory(config, "templates")
        tk.add_resource("assets", "search_tweaks_advanced_search")

    # IConfigurable

    def configure(self, config):
        try:
            from ckanext.composite_search.interfaces import ICompositeSearch
        except ImportError:
            raise CkanConfigurationException(
                "ckanext-composite-search is not installed"
            )
        if not p.plugin_loaded("composite_search"):
            raise CkanConfigurationException(
                "`composite_search` plugin must be enabled in order to use advanced search"
            )
        if not list(p.PluginImplementations(ICompositeSearch)):
            raise CkanConfigurationException(
                "Advanced search requires plugin that implements ICompositeSearch."
                + " Consider enabling `default_composite_search` plugins."
            )

    # ITemplateHelpers

    def get_helpers(self):
        return {
            "advanced_search_form_config": form_config,
            "advanced_search_form_config_image" : form_config_image,
        }

    # IPackageController

    def before_search(self, search_params: dict[str, Any]):
        solr_q = search_params.get("extras", {}).get("ext_solr_q", None)
        if solr_q:
            search_params.setdefault("q", "")
            search_params["q"] += " " + solr_q
        return search_params
