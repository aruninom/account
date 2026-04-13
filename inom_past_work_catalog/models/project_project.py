from odoo import fields, models


class ProjectProject(models.Model):
    _inherit = "project.project"

    show_in_past_work = fields.Boolean(
        string="Show in Past Work",
        default=False,
        help="Enable this project for the public past work catalogue.",
    )
    past_work_sector = fields.Char(string="Sector")
    past_work_type = fields.Char(string="Type of Work")
    past_work_short_description = fields.Char(string="Short Description")
    past_work_detailed_description = fields.Html(string="Detailed Description")
    past_work_pdf_attachment_id = fields.Many2one(
        "ir.attachment",
        string="PDF Case Study",
        domain="[(\"res_model\",\"=\",\"project.project\"), (\"mimetype\",\"=like\",\"application/pdf%\") ]",
    )

    def past_work_pdf_url(self):
        self.ensure_one()
        if not self.past_work_pdf_attachment_id:
            return False
        return f"/web/content/{self.past_work_pdf_attachment_id.id}?download=true"
