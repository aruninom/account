from odoo import fields, models


class EventEvent(models.Model):
    _inherit = "event.event"

    show_in_past_work = fields.Boolean(
        string="Show in Past Work",
        default=False,
        help="Enable this record for the public past work catalogue.",
    )
    past_work_sector = fields.Selection(
        selection=[
            ("government", "Government"),
            ("education", "Education"),
            ("health", "Health"),
            ("infrastructure", "Infrastructure"),
            ("community", "Community"),
            ("private", "Private Sector"),
            ("other", "Other"),
        ],
        string="Past Work Sector",
    )
    past_work_type = fields.Selection(
        selection=[
            ("facilitation", "Facilitation"),
            ("engagement", "Engagement"),
            ("research", "Research"),
            ("strategy", "Strategy"),
            ("training", "Training"),
            ("evaluation", "Evaluation"),
            ("other", "Other"),
        ],
        string="Past Work Type",
    )
    past_work_short_description = fields.Char(string="Past Work Short Description")
    past_work_detailed_description = fields.Html(string="Past Work Detailed Description")
    past_work_pdf_attachment_id = fields.Many2one(
        "ir.attachment",
        string="Past Work Case Study PDF",
        domain="[(\"res_model\",\"=\",\"event.event\"), (\"mimetype\",\"=like\",\"application/pdf%\") ]",
    )

    def past_work_pdf_url(self):
        self.ensure_one()
        if not self.past_work_pdf_attachment_id:
            return False
        return f"/web/content/{self.past_work_pdf_attachment_id.id}?download=true"
