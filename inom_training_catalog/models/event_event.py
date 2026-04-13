from odoo import api, fields, models


class EventEvent(models.Model):
    _inherit = "event.event"

    provider_type = fields.Selection(
        selection=[
            ("aha", "Aha Academy"),
            ("iap2", "IAP2"),
        ],
        string="Provider Type",
        help="Controls website visibility rules for event details.",
    )
    content_type = fields.Selection(
        selection=[
            ("engagement", "Engagement"),
            ("conflict", "Conflict"),
            ("facilitation", "Facilitation"),
            ("evaluation", "Evaluation"),
        ],
        string="Content Type",
    )
    booking_url = fields.Char(string="Booking Link")
    more_info_url = fields.Char(string="More Information Link")
    training_pdf_attachment_id = fields.Many2one(
        "ir.attachment",
        string="Training PDF",
        domain="[(\"res_model\",\"=\",\"event.event\"), (\"mimetype\",\"=like\",\"application/pdf%\") ]",
        help="Downloadable PDF for this course/event.",
    )
    show_in_portfolio = fields.Boolean(
        string="Show in Portfolio",
        default=True,
        help="Display this course in the always-on portfolio section.",
    )
    is_unscheduled_course = fields.Boolean(
        string="Unscheduled Course",
        help="Use this when the course should appear as a portfolio item without active schedule.",
    )
    visibility_state = fields.Selection(
        selection=[("published", "Published"), ("unpublished", "Unpublished")],
        string="Publish/Unpublish",
        compute="_compute_visibility_state",
        search="_search_visibility_state",
    )
    schedule_state = fields.Selection(
        selection=[("scheduled", "Scheduled"), ("unscheduled", "Unscheduled")],
        string="Scheduled/Unscheduled",
        compute="_compute_schedule_state",
        search="_search_schedule_state",
    )

    @api.depends("website_published")
    def _compute_visibility_state(self):
        for event in self:
            event.visibility_state = "published" if event.website_published else "unpublished"

    @api.depends("is_unscheduled_course", "date_begin")
    def _compute_schedule_state(self):
        for event in self:
            event.schedule_state = "unscheduled" if event.is_unscheduled_course or not event.date_begin else "scheduled"

    def _search_visibility_state(self, operator, value):
        if operator not in ("=", "!="):
            return []
        want_published = value == "published"
        if operator == "!=":
            want_published = not want_published
        return [("website_published", "=", want_published)]

    def _search_schedule_state(self, operator, value):
        if operator not in ("=", "!="):
            return []
        want_unscheduled = value == "unscheduled"
        if operator == "!=":
            want_unscheduled = not want_unscheduled
        return [("is_unscheduled_course", "=", want_unscheduled)]

    def website_can_see_restricted_fields(self):
        self.ensure_one()
        user = self.env.user
        return not self.provider_type == "iap2" or not user._is_public()

    def website_pdf_url(self):
        self.ensure_one()
        if not self.training_pdf_attachment_id:
            return False
        return f"/web/content/{self.training_pdf_attachment_id.id}?download=true"
