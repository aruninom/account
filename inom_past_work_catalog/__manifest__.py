{
    "name": "INOM Past Work Catalog",
    "summary": "Public past work catalogue with sector and work type filters",
    "version": "19.0.1.0.0",
    "category": "Website/Event",
    "author": "INOM",
    "license": "LGPL-3",
    "depends": ["website", "project"],
    "data": [
        "views/project_project_views.xml",
        "views/past_work_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "inom_past_work_catalog/static/src/css/past_work.css",
            "inom_past_work_catalog/static/src/js/past_work_filters.js",
        ],
    },
    "installable": True,
    "application": False,
}
