from odoo import http
from odoo.http import request


class PastWorkController(http.Controller):
    @http.route("/past-work-catalog", type="http", auth="public", website=True)
    def past_work_catalog(self, **kwargs):
        Event = request.env["event.event"].sudo()

        selected_sectors = request.httprequest.args.getlist("sector")
        selected_types = request.httprequest.args.getlist("work_type")

        domain = [
            ("show_in_past_work", "=", True),
            ("website_published", "=", True),
        ]

        if selected_sectors:
            domain.append(("past_work_sector", "in", selected_sectors))

        if selected_types:
            domain.append(("past_work_type", "in", selected_types))

        records = Event.search(domain, order="name asc")

        sectors = Event._fields["past_work_sector"].selection
        work_types = Event._fields["past_work_type"].selection

        values = {
            "records": records,
            "sectors": sectors,
            "work_types": work_types,
            "selected_sectors": selected_sectors,
            "selected_types": selected_types,
        }
        return request.render("inom_past_work_catalog.past_work_catalog_page", values)
