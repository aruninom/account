from odoo import http
from odoo.http import request


class PastWorkController(http.Controller):
    @http.route("/past-work-catalog", type="http", auth="public", website=True)
    def past_work_catalog(self, **kwargs):
        Project = request.env["project.project"].sudo()

        records = Project.search([("show_in_past_work", "=", True)], order="name asc")

        sectors = sorted({(record.past_work_sector or "").strip() for record in records if record.past_work_sector})
        work_types = sorted({(record.past_work_type or "").strip() for record in records if record.past_work_type})

        values = {
            "records": records,
            "sectors": sectors,
            "work_types": work_types,
        }
        return request.render("inom_past_work_catalog.past_work_catalog_page", values)
