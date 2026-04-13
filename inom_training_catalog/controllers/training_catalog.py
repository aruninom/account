from odoo import fields, http
from odoo.http import request


class TrainingCatalogController(http.Controller):
    @http.route(["/course-training", "/course-training/<string:view_mode>"], type="http", auth="public", website=True)
    def training_catalog(self, view_mode="upcoming", **kwargs):

        print("\n🔥 ===== COURSE TRAINING ROUTE HIT =====")

        Event = request.env["event.event"].sudo()

        provider_type = kwargs.get("provider_type")
        content_type = kwargs.get("content_type")
        query = kwargs.get("q")
        scheduled = kwargs.get("scheduled")
        published = kwargs.get("published")

        print("👉 View Mode:", view_mode)
        print("👉 Provider Type:", provider_type)
        print("👉 Content Type:", content_type)
        print("👉 Search Query:", query)
        print("👉 Scheduled:", scheduled)
        print("👉 Published:", published)

        is_public_user = request.env.user._is_public()
        print("👉 Is Public User:", is_public_user)

        base_domain = [("show_in_portfolio", "=", True)]

        if view_mode == "upcoming":
            base_domain += [
                ("date_begin", ">=", fields.Datetime.now()),
                ("is_unscheduled_course", "=", False),
            ]
        elif view_mode == "portfolio":
            base_domain += [
                "|",
                ("is_unscheduled_course", "=", True),
                ("date_begin", "!=", False),
            ]

        if provider_type in ("aha", "iap2"):
            base_domain.append(("provider_type", "=", provider_type))

        if content_type in ("engagement", "conflict", "facilitation", "evaluation"):
            base_domain.append(("content_type", "=", content_type))

        if scheduled in ("scheduled", "unscheduled"):
            base_domain.append(("schedule_state", "=", scheduled))

        if is_public_user:
            base_domain.append(("website_published", "=", True))
        elif published in ("published", "unpublished"):
            base_domain.append(("visibility_state", "=", published))

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

        print("👉 FINAL DOMAIN:", base_domain)

        events = Event.search(base_domain, order="date_begin asc, name asc")

        print("👉 TOTAL EVENTS FOUND:", len(events))
        print("👉 EVENT IDS:", events.ids)

        values = {
            "events": events,
            "view_mode": view_mode,
            "provider_type": provider_type,
            "content_type": content_type,
            "q": query,
            "scheduled": scheduled,
            "published": published,
        }

        print("🔥 ===== RENDERING TEMPLATE =====\n")

        return request.render("inom_training_catalog.training_catalog_page", values)