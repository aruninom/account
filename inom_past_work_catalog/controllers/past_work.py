from odoo import http
from odoo.http import request


class PastWorkController(http.Controller):
    @http.route("/past-work-catalog", type="http", auth="public", website=True)
    def past_work_catalog(self, **kwargs):
        Project = request.env["project.project"].sudo()

        selected_sectors = request.httprequest.args.getlist("sector")
        selected_types = request.httprequest.args.getlist("work_type")

        domain = [
            ("show_in_past_work", "=", True),
            ("past_work_is_published", "=", True),
        ]

        if selected_sectors:
            domain.append(("past_work_sector", "in", selected_sectors))

        if selected_types:
            domain.append(("past_work_type", "in", selected_types))

        records = Project.search(domain, order="name asc")

        sectors = Project._fields["past_work_sector"].selection
        work_types = Project._fields["past_work_type"].selection

        values = {
            "records": records,
            "sectors": sectors,
            "work_types": work_types,
            "selected_sectors": selected_sectors,
            "selected_types": selected_types,
        }
        return request.render("inom_past_work_catalog.past_work_catalog_page", values)
