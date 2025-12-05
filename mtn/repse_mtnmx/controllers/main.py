# Copyright 2013-2025, MTNET SERVICES
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL.html).

import ast
import base64
from collections import OrderedDict

from odoo import _, http
from odoo.exceptions import AccessError, MissingError
from odoo.http import content_disposition, request, route
from odoo.osv import expression

from odoo.addons.portal.controllers import portal
from odoo.addons.portal.controllers.portal import pager as portal_pager

portal.CustomerPortal.OPTIONAL_BILLING_FIELDS.append("fiscal_constancy")


class CustomerPortal(portal.CustomerPortal):
    def _get_repse_searchbar_sortings(self):
        return {
            "date": {"label": _("Date"), "order": "repse_date desc"},
            "name": {"label": _("Reference"), "order": "name desc"},
            "state": {"label": _("Status"), "order": "state"},
        }  # repse

    def _get_repse_searchbar_filters(self):
        return {
            "all": {"label": _("All"), "domain": []},
            "state": {
                "label": _("Missing"),
                "domain": [("state", "=", ("process"))],
            },
        }

    def _render_portal(
        self,
        template,
        page,
        date_begin,
        date_end,
        sortby,
        filterby,
        domain,
        searchbar_filters,
        default_filter,
        url,
        history,
        page_name,
        key,
    ):
        values = self._prepare_portal_layout_values()

        return request.render(template, values)

    def _prepare_my_repse_values(self, page, date_begin, date_end, sortby, filterby, domain=None, url="/my/repse"):
        values = self._prepare_portal_layout_values()
        repse_obj = request.env["document.repse"]

        domain = expression.AND(
            [
                domain or [],
            ]
        )

        repse_user = False
        user = request.env["res.users"].sudo().search([("id", "=", request.env.uid)])
        if user.has_group("repse_mtnmx.group_repse_portal") or user.has_group("repse_mtnmx.group_repse_manager"):
            repse_user = True

        partner_id = request.env.user.partner_id
        if not user.has_group("repse_mtnmx.group_repse_manager"):
            domain += [("partner_id", "=", partner_id.id)]
        domain += [("state", "=", "process")]
        searchbar_sortings = self._get_repse_searchbar_sortings()
        # default sort by order
        if not sortby:
            sortby = "date"
        order = searchbar_sortings[sortby]["order"]

        searchbar_filters = self._get_repse_searchbar_filters()
        # default filter by value
        if not filterby:
            filterby = "all"
        domain += searchbar_filters[filterby]["domain"]

        if date_begin and date_end:
            domain += [
                ("create_date", ">", date_begin),
                ("create_date", "<=", date_end),
            ]

        values.update(
            {
                "date": date_begin,
                # content according to pager and archive selected
                # lambda function to get the invoices recordset when the pager will be defined in the main method of a route
                "repses": lambda pager_offset: (
                    repse_obj.search(
                        domain,
                        order=order,
                        limit=self._items_per_page,
                        offset=pager_offset,
                    )
                    if repse_user
                    else repse_obj
                ),
                "page_name": "Repse",
                "pager": {  # vals to define the pager.
                    "url": url,
                    "url_args": {
                        "date_begin": date_begin,
                        "date_end": date_end,
                        "sortby": sortby,
                        "filterby": filterby,
                    },
                    "total": repse_obj.search_count(domain) if repse_user else 0,
                    "page": page,
                    "step": self._items_per_page,
                },
                "default_url": url,
                "searchbar_sortings": searchbar_sortings,
                "sortby": sortby,
                "searchbar_filters": OrderedDict(sorted(searchbar_filters.items())),
                "filterby": filterby,
            }
        )
        return values

    @route(["/my", "/my/home"], type="http", auth="user", website=True)
    def home(self, **kw):
        user = request.env["res.users"].sudo().search([("id", "=", request.env.uid)])
        tag_id = request.env.ref("repse_mtnmx.partner_portal_repse")
        if user.partner_id.category_id and tag_id:
            if tag_id.id in user.partner_id.category_id.ids:
                return request.redirect("/my/repse")
        values = self._prepare_portal_layout_values()
        return request.render("portal.portal_my_home", values)

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        user = request.env["res.users"].sudo().search([("id", "=", request.env.uid)])
        if "repse_count" in counters:
            domain = []
            if not user.has_group("repse_mtnmx.group_repse_manager"):
                domain += [("partner_id", "=", user.partner_id.id)]
            repse_count = (
                request.env["document.repse"].search_count(domain)
                if request.env["document.repse"].check_access_rights("read", raise_exception=False)
                else 0
            )
            values["repse_count"] = repse_count

        return values

    @route(
        ["/my/repse", "/my/repse/page/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def repse(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        user = request.env["res.users"].sudo().search([("id", "=", request.env.uid)])
        if not user.has_group("repse_mtnmx.group_repse_portal"):
            if not user.has_group("repse_mtnmx.group_repse_manager"):
                return request.redirect("/my/home")

        values = self._prepare_my_repse_values(page, date_begin, date_end, sortby, filterby)
        pager = portal_pager(**values["pager"])

        # content according to pager and archive selected
        repses = values["repses"](pager["offset"])
        request.session["my_repses_history"] = repses.ids[:100]

        values.update(
            {
                "repses": repses,
                "pager": pager,
            }
        )
        # return request.render("account.portal_my_invoices", values)

        partner = request.env.user.partner_id
        values.update(
            {
                "partner": partner,
            }
        )
        domain = []
        if not user.has_group("repse_mtnmx.group_repse_manager"):
            domain += [("partner_id", "=", user.partner_id.id)]
        repse_ids = request.env["document.repse"].sudo().search(domain)
        repse_doc_ids = []
        missing_docs = []
        for repse in repse_ids:
            mdocs = repse.missing_documents.split("\n")
            for mdoc in mdocs:
                if bool(mdoc):
                    missing_docs.append(mdoc)

            repse_doc_ids.append(
                {
                    "repse": repse,
                    "name": repse.name,
                    "state": repse.state,
                    "mdocs": missing_docs,
                }
            )
        values.update({"repse_ids": repse_doc_ids})
        response = request.render("repse_mtnmx.repse", values)
        response.headers["X-Frame-Options"] = "DENY"

        return response

    def _repse_get_page_view_values(self, repse, access_token, **kwargs):
        values = {
            "page_name": "Repse",
            **repse._get_repse_portal_extra_values(),
        }
        return self._get_page_view_values(repse, access_token, values, "my_repses_history", False, **kwargs)

    def _process_kw(self, keys, vals, msg, repse_id):
        repse_id = request.env["document.repse"].sudo().search([("id", "=", repse_id)])
        vals.update({"name": keys.get("name")})
        if keys.get("cfiscal"):
            vals.update(
                {
                    "fiscal_constancy": base64.b64encode(keys.get("cfiscal").read()),
                    "fiscal_constancy_name": keys.get("name").filename,
                }
            )
            msg += _("Fiscal constancy, ")

        if keys.get("actac"):
            vals.update(
                {
                    "acta_cons": base64.b64encode(keys.get("actac").read()),
                    "acta_name": keys.get("actac").filename,
                }
            )
            msg += _("Constitutive act, ")

        if keys.get("opinion"):
            vals.update(
                {
                    "opinion": base64.b64encode(keys.get("opinion").read()),
                    "opinion_state": "pv",
                    "opinion_name": keys.get("opinion").filename,
                }
            )
            msg += _("SAT compliance opinion, ")

        if keys.get("cimss"):
            vals.update(
                {
                    "imss_compliance": base64.b64encode(keys.get("cimss").read()),
                    "imss_state": "pv",
                    "imss_name": keys.get("cimss").filename,
                }
            )
            msg += _("IMSS compliance, ")

        if keys.get("cinfonavit"):
            vals.update(
                {
                    "infonavit_compliance": base64.b64encode(keys.get("cinfonavit").read()),
                    "infonavit_state": "pv",
                    "infonavit_name": keys.get("cinfonavit").filename,
                }
            )
            msg += _("Infonavit compliance, ")

        if keys.get("cfiscal1"):
            vals.update(
                {
                    "fiscal_constancy1": base64.b64encode(keys.get("cfiscal1").read()),
                    "cfiscal1_state": "pv",
                    "fiscalc1_name": keys.get("cfiscal1").filename,
                }
            )
            msg += _("Monthly fiscal contancy, ")

        if keys.get("no_activity"):
            vals.update(
                {
                    "no_activity_file": base64.b64encode(keys.get("no_activity").read()),
                    "na_state": "pv",
                    "na_name": keys.get("no_activity").filename,
                }
            )
            msg += _("no activity written, ")

        if keys.get("repse_doc"):
            vals.update(
                {
                    "repse_doc": base64.b64encode(keys.get("repse_doc").read()),
                    "repse_state": "pv",
                    "repdoc_name": keys.get("repse_doc").filename,
                }
            )
            msg += _("Repse activity doc, ")

        if keys.get("workers"):
            vals.update(
                {
                    "workers_relationship": base64.b64encode(keys.get("workers").read()),
                    "workers_name": keys.get("workers").filename,
                }
            )
            msg += _("Workers relationship, ")

        return vals, msg

    def _process_kw1(self, keys, vals, msg, repse_id):
        repse_id = request.env["document.repse"].sudo().search([("id", "=", repse_id)])

        if keys.get("bim"):
            vals.update(
                {
                    "bim_card": base64.b64encode(keys.get("bim").read()),
                    "bim_state": "pv",
                    "bim_name": keys.get("bim").filename,
                }
            )
            msg += _("BIM CARD, ")

        if keys.get("sipare"):
            vals.update(
                {
                    "sipare_line": base64.b64encode(keys.get("sipare").read()),
                    "sipare_state": "pv",
                    "sipare_name": keys.get("sipare").filename,
                }
            )
            msg += _("SIPARE, ")

        if keys.get("settlement"):
            vals.update(
                {
                    "settlement_resume": base64.b64encode(keys.get("settlement").read()),
                    "settlement_state": "pv",
                    "settlement_name": keys.get("settlement").filename,
                }
            )
            msg += _("Settlement resume, ")

        if keys.get("sua"):
            vals.update(
                {
                    "sua_payment": base64.b64encode(keys.get("sua").read()),
                    "sua_state": "pv",
                    "sua_name": keys.get("sua").filename,
                }
            )
            msg += _("SUA payment, ")

        if keys.get("diva"):
            vals.update(
                {
                    "iva_statement": base64.b64encode(keys.get("diva").read()),
                    "diva_state": "pv",
                    "ivas_name": keys.get("diva").filename,
                }
            )
            msg += _("IVA Statement, ")

        if keys.get("civa"):
            vals.update(
                {
                    "iva_complement": base64.b64encode(keys.get("civa").read()),
                    "civa_state": "pv",
                    "ivac_name": keys.get("civa").filename,
                }
            )
            msg += _("IVA Complement, ")

        if keys.get("cfdi"):
            vals.update(
                {
                    "cfdi_paysheet": base64.b64encode(keys.get("cfdi").read()),
                    "cfdi_state": "pv",
                    "cfdip_name": keys.get("cfdi").filename,
                }
            )
            msg += _("CFDI Paysheet, ")

        if keys.get("disr"):
            vals.update(
                {
                    "isr_statement": base64.b64encode(keys.get("disr").read()),
                    "disr_state": "pv",
                    "isrs_name": keys.get("disr").filename,
                }
            )
            msg += _("ISR Statement, ")

        if keys.get("cisr"):
            vals.update(
                {
                    "isr_complement": base64.b64encode(keys.get("cisr").read()),
                    "cisr_state": "pv",
                    "isrc_name": keys.get("cisr").filename,
                }
            )
            msg += _("ISR Complement, ")

        for line in repse_id.repse_line_ids:
            if keys.get(str(line.id)):
                line.update(
                    {
                        "workers_relationship": base64.b64encode(keys.get(str(line.id)).read()),
                        "worker_state": "pv",
                        "workers_name": keys.get(str(line.id)).filename,
                    }
                )
                msg += _("Worker relationship from PO {}, ").format(line.purchase_order_id.name)

        return vals, msg

    def _process_kw2(self, keys, vals, msg, repse_id):
        repse_id = request.env["document.repse"].sudo().search([("id", "=", repse_id)])
        if keys.get("icsoe"):
            vals.update(
                {
                    "icsoe": base64.b64encode(keys.get("icsoe").read()),
                    "icsoe_state": "pv",
                    "icsoe_name": keys.get("icsoe").filename,
                }
            )
            msg += _("ICSOE, ")

        if keys.get("sisub"):
            vals.update(
                {
                    "sisub": base64.b64encode(keys.get("sisub").read()),
                    "sisub_state": "pv",
                    "sisub_name": keys.get("sisub").filename,
                }
            )
            msg += _("SISUB, ")

        return vals, msg

    @http.route(["/my/repse/<int:repse_id>"], type="http", auth="public", website=True)
    def portal_my_detail(self, repse_id, access_token=None, **kw):
        try:
            repse_sudo = self._document_check_access("document.repse", repse_id, access_token)
        except (AccessError, MissingError):
            return request.redirect("/my")

        partner_id = request.env.user.partner_id

        if kw and request.httprequest.method == "POST":
            if "doc_name" in str(kw):
                for keywords in kw:
                    if "doc_name" in kw.get(keywords):
                        data = ast.literal_eval(kw.get(keywords))

                        filecontent = base64.b64decode(data.get("doc") or "")
                        if not filecontent:
                            return request.not_found()

                        filename = data.get("doc_name")
                        return request.make_response(
                            filecontent,
                            [
                                ("Content-Type", "application/octet-stream"),
                                ("Content-Disposition", content_disposition(filename)),
                            ],
                        )

            valsa = {}
            msga = _("The following document(s) has been uploaded, please follow up:")

            valsb, msgb = self._process_kw(kw, valsa, msga, repse_id)
            valsc, msgc = self._process_kw1(kw, valsb, msgb, repse_id)
            vals, msg = self._process_kw2(kw, valsc, msgc, repse_id)

            rep_id = request.env["document.repse"].sudo().search([("id", "=", repse_id)])
            rep_id.action_process_upload(vals, msg, partner_id)

        values = self._repse_get_page_view_values(repse_sudo, access_token, **kw)
        return request.render("repse_mtnmx.portal_repse_page", values)
