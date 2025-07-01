//ckan.module("search-tweaks-advanced-search", function ($) {
//  "use strict";
//  var EVENT_TOGGLE_SEARCH = "composite-search:toggle";
//  return {
//    options: {
//      enableAdvanced: false,
//      enableSolr: false,
//    },
//    initialize: function () {
//      $.proxyAll(this, /_on/);
//      this.toggles = this.$(".advanced-toggles");
//      this.fieldQ = this.$('input[name="q"]');
//      this.fieldSolr = this.$('input[name="ext_solr_q"]');
//
//      this.toggles
//        .find(".enable-advanced")
//        .on("change", this._onEnableAdvanced);
//      this.toggles.find(".enable-image").on("change", this._onEnableSolr);
//      this.el.on("keyup", this._onKeyUp);
//
//      if (this.options.enableAdvanced) {
//        this.enableAdvanced();
//      }
//      if (this.options.enableSolr) {
//        this.enableAdvanced();
//        this.enableSolr();
//      }
//    },
//    teadown: function () {},
//    _onKeyUp: function (e) {
//      if (e.key !== "Enter") {
//        return;
//      }
//      if (e.target.name != "ext_composite_value") {
//        return;
//      }
//      this.$('[type="submit"]').first().click();
//    },
//    _onEnableAdvanced: function (e) {
//      if (e.target.checked) {
//        this.enableAdvanced();
//      } else {
//        this.disableAdvanced();
//      }
//    },
//    _onEnableSolr: function (e) {
//      if (e.target.checked) {
//        this.enableSolr();
//      } else {
//        this.disableSolr();
//      }
//    },
//
//    enableAdvanced: function () {
//      this.el.addClass("enabled");
//      this.toggles.addClass("advanced-active");
//      this.sandbox.publish(EVENT_TOGGLE_SEARCH, true);
//      this.fieldQ.prop("disabled", true);
//    },
//
//    disableAdvanced: function () {
//      this.el.removeClass("enabled");
//      this.toggles
//        .removeClass("advanced-active")
//        .find(".enable-image input")
//        .prop("checked", false);
//      this.disableSolr();
//      this.sandbox.publish(EVENT_TOGGLE_SEARCH, false);
//      this.fieldQ.prop("disabled", false);
//    },
//
//    enableSolr: function () {
//      this.el.addClass("use-solr-query");
//      this.sandbox.publish(EVENT_TOGGLE_SEARCH, false);
//      this.fieldSolr.prop("disabled", false);
//    },
//    disableSolr: function () {
//      this.el.removeClass("use-solr-query");
//      this.sandbox.publish(EVENT_TOGGLE_SEARCH, true);
//      this.fieldSolr.prop("disabled", true);
//    },
//  };
//});


ckan.module("search-tweaks-advanced-search", function ($) {
  "use strict";

  var EVENT_TOGGLE_SEARCH = "composite-search:toggle";

  return {
    options: {
      enableAdvanced: false,
      enableSolr: false,
    },

    initialize: function () {
      $.proxyAll(this, /_on/);
      this.toggles = this.$(".advanced-toggles");
      this.fieldQ = this.$('input[name="q"]');
      this.fieldSolr = this.$('input[name="ext_solr_q"]');

      // New field for dataset_type
      this.fieldDatasetType = this.$('select[name="dataset_type"]');

      this.toggles
        .find(".enable-advanced")
        .on("change", this._onEnableAdvanced);
      this.toggles.find(".enable-image").on("change", this._onEnableSolr);
      this.el.on("keyup", this._onKeyUp);

      // New event listener for PubChem
      this.fieldQ.on("input", this._onPubChemSearch);

      if (this.options.enableAdvanced) {
        this.enableAdvanced();
      }
      if (this.options.enableSolr) {
        this.enableAdvanced();
        this.enableSolr();
      }
    },

    teadown: function () {},

    _onKeyUp: function (e) {
      if (e.key !== "Enter") {
        return;
      }
      if (e.target.name != "ext_composite_value") {
        return;
      }
      this.$('[type="submit"]').first().click();
    },

    _onEnableAdvanced: function (e) {
      if (e.target.checked) {
        this.enableAdvanced();
      } else {
        this.disableAdvanced();
      }
    },

    _onEnableSolr: function (e) {
      if (e.target.checked) {
        this.enableSolr();
      } else {
        this.disableSolr();
      }
    },

    enableAdvanced: function () {
      this.el.addClass("enabled");
      this.toggles.addClass("advanced-active");
      this.sandbox.publish(EVENT_TOGGLE_SEARCH, true);
      this.fieldQ.prop("disabled", true);
    },

    disableAdvanced: function () {
      this.el.removeClass("enabled");
      this.toggles
        .removeClass("advanced-active")
        .find(".enable-image input")
        .prop("checked", false);
      this.disableSolr();
      this.sandbox.publish(EVENT_TOGGLE_SEARCH, false);
      this.fieldQ.prop("disabled", false);
    },

    enableSolr: function () {
      this.el.addClass("use-solr-query");
      this.sandbox.publish(EVENT_TOGGLE_SEARCH, false);
      this.fieldSolr.prop("disabled", false);
    },

    disableSolr: function () {
      this.el.removeClass("use-solr-query");
      this.sandbox.publish(EVENT_TOGGLE_SEARCH, true);
      this.fieldSolr.prop("disabled", true);
    },

    /**
     * New Method for PubChem Integration
     */
    _onPubChemSearch: function () {
      const query = this.fieldQ.val().trim();
      const datasetType = this.fieldDatasetType.val();

      if (!query || datasetType !== "molecule") {
        return; // Do nothing if no query or dataset type is not "molecule"
      }

      $.ajax({
        url: "/api/3/action/search_pubchem_for_molecules",
        method: "POST",
        contentType: "application/json",
        dataType: "json",
        data: JSON.stringify({ compound_name: query }),
        success: (data) => {
          if (data && data.result && data.result.results.length > 0) {
            this._updateSearchResults(data.result.results);
          } else {
            console.log("No PubChem results found.");
          }
        },
        error: (xhr, status, error) => {
          console.error("PubChem search failed:", status, error);
        },
      });
    },

    /**
     * Helper Method to Update Search Results to search
     */
    _updateSearchResults: function (results) {
      const resultsContainer = this.$("#search-autocomplete--suggestion-box");

      if (!resultsContainer.length) {
        console.error("Suggestion box element is missing.");
        return;
      }

      const html = results
        .map(
          (item) => `
          <li>
            <a href="/dataset/${item.name}" target="_blank">
              ${item.title} (InChIKey: ${item.inchi_key})
            </a>
          </li>
        `
        )
        .join("");

      resultsContainer.html(html);
    },
  };
});
