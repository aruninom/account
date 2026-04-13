from odoo import fields, http
from odoo.http import request


class TrainingCatalogController(http.Controller):
    @http.route(["/training", "/training/<string:view_mode>"], type="http", auth="public", website=True)
    def training_catalog(self, view_mode="upcoming", **kwargs):
        Event = request.env["event.event"].sudo()
        provider_type = kwargs.get("provider_type")
        content_type = kwargs.get("content_type")
        query = kwargs.get("q")
        show_scheduled = kwargs.get("show_scheduled")
        show_unscheduled = kwargs.get("show_unscheduled")
        show_published = kwargs.get("show_published")
        show_unpublished = kwargs.get("show_unpublished")

        is_public_user = request.env.user._is_public()
        base_domain = [("show_in_portfolio", "=", True)]

        if view_mode == "upcoming":
            base_domain += [
                ("date_begin", ">=", fields.Datetime.now()),
                ("is_unscheduled_course", "=", False),
            ]
        else:
            # Portfolio view should show courses even without active schedule.
            base_domain += []

        if provider_type in ("aha", "iap2"):
            base_domain.append(("provider_type", "=", provider_type))

        if content_type in ("engagement", "conflict", "facilitation", "evaluation"):
            base_domain.append(("content_type", "=", content_type))

        if show_scheduled and not show_unscheduled:
            base_domain.append(("schedule_state", "=", "scheduled"))
        elif show_unscheduled and not show_scheduled:
            base_domain.append(("schedule_state", "=", "unscheduled"))

        if is_public_user:
            base_domain.append(("website_published", "=", True))
        else:
            if show_published and not show_unpublished:
                base_domain.append(("visibility_state", "=", "published"))
            elif show_unpublished and not show_published:
                base_domain.append(("visibility_state", "=", "unpublished"))

        if query:
            search_fields = [field for field in ("name", "subtitle", "description") if field in Event._fields]
            if search_fields:
                if len(search_fields) == 1:
                    base_domain.append((search_fields[0], "ilike", query))
                elif len(search_fields) == 2:
                    base_domain += ["|", (search_fields[0], "ilike", query), (search_fields[1], "ilike", query)]
                else:
                    base_domain += [
                        "|",
                        "|",
                        (search_fields[0], "ilike", query),
                        (search_fields[1], "ilike", query),
                        (search_fields[2], "ilike", query),
                    ]

        events = Event.search(base_domain, order="date_begin asc, name asc")

        values = {
            "events": events,
            "view_mode": view_mode,
            "provider_type": provider_type,
            "content_type": content_type,
            "q": query,
            "show_scheduled": show_scheduled,
            "show_unscheduled": show_unscheduled,
            "show_published": show_published,
            "show_unpublished": show_unpublished,
        }
        return request.render("inom_training_catalog.training_catalog_page", values)
