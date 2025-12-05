# Copyright 2013-2025, MTNET SERVICES
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL.html).

import ast
import calendar
import logging
from datetime import date, timedelta

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _

FIELD_STATE = [("pv", "To Validate"), ("denied", "Denied"), ("approve", "Valid")]


class DocumentRepse(models.Model):
    _name = "document.repse"
    _inherit = ["portal.mixin", "mail.thread", "mail.activity.mixin"]
    _description = "REPSE"
    _translate = True

    # Necesary documents for repse registry #
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=False,
        default=lambda self: self.env.company)
    # Documents from day 1 to 8 of every month #
    fiscal_constancy = fields.Binary(attachment=True)  #
    fiscal_constancy_name = fields.Char(tracking=True)
    cfiscal_state = fields.Selection(FIELD_STATE, string="C.Fiscal State", tracking=True)

    opinion = fields.Binary(attachment=True, string="SAT compliance opinion")  #
    opinion_name = fields.Char(tracking=True)
    opinion_state = fields.Selection(FIELD_STATE, tracking=True)

    imss_compliance = fields.Binary(attachment=True, string="IMSS Compliance")  #
    imss_name = fields.Char(tracking=True)
    imss_state = fields.Selection(FIELD_STATE, string="IMSS State", tracking=True)

    infonavit_compliance = fields.Binary(attachment=True, string="INFONAVIT Compliance")  #
    infonavit_name = fields.Char(tracking=True)
    infonavit_state = fields.Selection(FIELD_STATE, tracking=True)

    fiscal_constancy1 = fields.Binary(attachment=True, string="Fiscal Constancy 1")
    fiscalc1_name = fields.Char(tracking=True)
    cfiscal1_state = fields.Selection(FIELD_STATE, string="Fiscal C. 1 State", tracking=True)

    workers_relationship = fields.Binary(attachment=True, string="Workers relationship")  #
    workers_name = fields.Char(tracking=True)
    worker_state = fields.Selection(FIELD_STATE, string="Workers State", tracking=True)

    repse_doc = fields.Binary(attachment=True, string="Doc B.P. REPSE")
    repdoc_name = fields.Char(tracking=True)
    repse_state = fields.Selection(FIELD_STATE, string="Repse Doc State", tracking=True)

    no_activity = fields.Boolean(string="No activity?")
    no_activity_file = fields.Binary(attachment=True, string="No activity documentation")
    na_name = fields.Char(tracking=True)
    na_state = fields.Selection(FIELD_STATE, string="No activity State", tracking=True)

    # Documents from 2 bussiness days after 16 of next month #

    act_cons = fields.Binary(attachment=True, string="Const. Act")
    acta_name = fields.Char(tracking=True)
    act_state = fields.Selection(FIELD_STATE, tracking=True)

    bim_card = fields.Binary(attachment=True, string="BIM-MON Card")
    bim_name = fields.Char(tracking=True)
    bim_state = fields.Selection(FIELD_STATE, string="BMC State", tracking=True)

    sipare_line = fields.Binary(attachment=True, string="SIPARE Line")
    sipare_name = fields.Char(tracking=True)
    sipare_state = fields.Selection(FIELD_STATE, tracking=True)

    settlement_resume = fields.Binary(
        attachment=True,
    )
    settlement_name = fields.Char(tracking=True)
    settlement_state = fields.Selection(FIELD_STATE, tracking=True)

    sua_payment = fields.Binary(attachment=True, string="SUA Payment")
    sua_name = fields.Char(tracking=True)
    sua_state = fields.Selection(FIELD_STATE, string="SUA State", tracking=True)

    iva_statement = fields.Binary(attachment=True, string="IVA Statement")
    ivas_name = fields.Char(tracking=True)
    diva_state = fields.Selection(FIELD_STATE, string="IVA S. State", tracking=True)

    iva_complement = fields.Binary(attachment=True, string="IVA Comp.")
    ivac_name = fields.Char(tracking=True)
    civa_state = fields.Selection(FIELD_STATE, string="IVA C. State", tracking=True)

    cfdi_paysheet = fields.Binary(attachment=True, string="CFDI Paysheet")  #
    cfdip_name = fields.Char()
    cfdi_state = fields.Selection(
        FIELD_STATE,
        string="CFDI State",
    )

    isr_statement = fields.Binary(attachment=True, string="ISR Statement")
    isrs_name = fields.Char(tracking=True)
    disr_state = fields.Selection(FIELD_STATE, string="ISR S. State", tracking=True)

    isr_complement = fields.Binary(attachment=True, string="ISR Comp.")
    isrc_name = fields.Char(tracking=True)
    cisr_state = fields.Selection(FIELD_STATE, string="ISR C. State", tracking=True)

    # Documents for every four month period #

    icsoe = fields.Binary(attachment=True, string="ICSOE")  #
    icsoe_name = fields.Char(tracking=True)
    icsoe_state = fields.Selection(FIELD_STATE, tracking=True)

    sisub = fields.Binary(attachment=True, string="SISUB")  #
    sisub_name = fields.Char(tracking=True)
    sisub_state = fields.Selection(FIELD_STATE, tracking=True)

    contract = fields.Binary(
        attachment=True,
    )
    contract_v2 = fields.Binary(
        attachment=True,
    )

    # fields for repse control #

    name = fields.Char()
    partner_id = fields.Many2one("res.partner", string="Supplier")
    repse_date = fields.Date()

    state = fields.Selection(
        [("process", "In Process"), ("positive", "Positive"), ("cancel", "Cancelled")],
        string="Status",
        default="process",
    )
    compute_state = fields.Boolean(compute="_compute_state")
    missing_documents = fields.Text(string="Missing docs", compute="_compute_get_missing_docs")
    repse_line_ids = fields.One2many("document.repse.line", "repse_document_id", string="Repse Lines")

    repse_user_id = fields.Many2one(
        "res.users", copy=False, tracking=True, string="User", default=lambda self: self.env.user
    )

    repse_type = fields.Selection(
        [("activity", "Activity"), ("no", "No activity"), ("quatri", "Four month period")],
        string="REPSE Type",
    )
    invoice_count = fields.Integer(compute="_compute_invoice")
    invoice_ids = fields.One2many("account.move", "repse_id", string="Invoices")
    after_month = fields.Boolean(string="After base month", compute="_compute_get_create_date")

    # # to review
    move_id = fields.Many2one("account.move", string="Facturas")

    # Fields to simplified repse process #
    quatri = fields.Boolean(compute="_compute_state", store=True)
    no_activity = fields.Boolean(compute="_compute_invoice", store=True)

    @api.depends("state")
    def _compute_state(self):
        all_valid = self.action_all_valid()
        for rec in self:
            rec.sudo().update(
                {
                    "state": "positive" if all_valid else rec.state,
                    "compute_state": all_valid,
                    "quatri": int(rec.repse_date.month) in [1, 5, 9],
                }
            )

    @api.depends("repse_line_ids")
    def _compute_invoice(self):
        for order in self:
            inv_date = order.repse_date - relativedelta(months=1)
            if inv_date.month < 10:
                month = "0" + str(inv_date.month)
            else:
                month = str(inv_date.month)

            last_day = calendar.monthrange(inv_date.year, inv_date.month)
            repse_date_start = str(inv_date.year) + "-" + month + "-01"
            repse_date_end = str(inv_date.year) + "-" + month + "-" + str(last_day[1])
            in_invoice_ids = (
                self.env["account.move"]
                .sudo()
                .search(
                    [
                        ("partner_id", "=", order.partner_id.id),
                        ("state", "=", "posted"),
                        ("move_type", "=", "in_invoice"),
                        ("invoice_date", ">=", repse_date_start),
                        ("invoice_date", "<=", repse_date_end),
                    ]
                )
            )
            sp_cont_product_ids = self.env["product.product"].search(
                [("purchase_ok", "=", True), ("default_code", "ilike", "SP Cont")]
            )
            invoice_ids = in_invoice_ids.filtered(
                lambda x: any(line.product_id.id in sp_cont_product_ids.ids for line in x.invoice_line_ids)
            )
            order.sudo().update(
                {
                    "invoice_ids": invoice_ids.ids,
                    "invoice_count": len(invoice_ids),
                    "no_activity": not invoice_ids,
                }
            )

    @api.depends("repse_date")
    def _compute_get_create_date(self):
        for rec in self:
            current_year = date.today().year
            after_month = False
            repse_date = date.today()
            if rec.repse_date:
                repse_date = rec.repse_date
            if current_year == repse_date.year:
                current_month = date.today().month
                if current_month > repse_date.month:
                    after_month = True
            elif current_year > rec.repse_date.year:
                after_month = True

            rec.sudo().update({"after_month": after_month})

    def _get_missing_first(self, rec, missing_documents):
        if not rec.opinion:
            missing_documents += "- SAT Compliance Opinion\n"
        if not rec.imss_compliance:
            missing_documents += "- IMSS Compliance Opinion\n"
        if not rec.infonavit_compliance:
            missing_documents += "- INFONAVIT Compliance Constancy  \n"
        if not rec.fiscal_constancy1:
            missing_documents += "- Month Fiscal Situation Constancy\n"
        if rec.no_activity and not rec.no_activity_file:
            missing_documents += "- No Activity Written\n"
        if not rec.no_activity and not rec.repse_doc:
            missing_documents += "- Repse Activity Doc\n"

        return missing_documents

    def _get_missing_after(self, rec, missing_documents):
        if not rec.bim_card:
            missing_documents += "- Month - Bimonth Card Worker-Employer fee\n"
        if not rec.sipare_line:
            missing_documents += "- SIPARE\n"
        if not rec.settlement_resume:
            missing_documents += "- Settlement Resume\n"
        if not rec.sua_payment:
            missing_documents += "- SUA Payment\n"
        if not rec.iva_statement:
            missing_documents += "- IVA Statement\n"
        if not rec.iva_complement:
            missing_documents += "- IVA Payment\n"
        if not rec.cfdi_paysheet:
            missing_documents += "- Contract Workers Paysheet CFDI'S\n"
        if not rec.isr_statement:
            missing_documents += "- ISR Statement\n"
        if not rec.isr_complement:
            missing_documents += "- ISR Payment\n"

        return missing_documents

    def _get_missing_quatri(self, rec, missing_documents):
        if not rec.icsoe:
            missing_documents += "- Informative Acknowledgment (ICSOE)\n"
        if not rec.sisub:
            missing_documents += "- Informative Acknowledgment (SISUB)\n"
        return missing_documents

    def _compute_get_missing_docs(self):
        for rec in self:
            missing_documents = ""
            missing_documents = self._get_missing_first(rec, missing_documents)
            if not rec.no_activity:
                missing_documents = self._get_missing_after(rec, missing_documents)
            if rec.quatri:
                missing_documents = self._get_missing_quatri(rec, missing_documents)

            uncomplete_parent_docs = bool(missing_documents)
            if rec.repse_line_ids.filtered(lambda x: not x.workers_relationship):
                missing_documents += "- Contract Workers List: \n"

                for line in rec.repse_line_ids:
                    if not line.workers_relationship:
                        missing_documents += "    - %s / %s \n" % (
                            line.purchase_order_id.name,
                            line.purchase_order_id.date_approve.date()
                            if line.purchase_order_id.date_approve
                            else date.today(),
                        )

            all_valid = rec.action_all_valid()

            if not uncomplete_parent_docs and rec.state == "process" and all_valid:
                rec.sudo().update({"state": "positive"})
            if not uncomplete_parent_docs and rec.state == "positive" and not all_valid:
                rec.sudo().update({"state": "process"})
            if uncomplete_parent_docs and rec.state == "positive":
                rec.sudo().update({"state": "process"})
            rec.missing_documents = missing_documents

    def action_cancel(self):
        for rec in self:
            rec.write({"state": "cancel"})

    def action_open(self):
        for rec in self:
            rec.write({"state": "process"})

    def check_is_cancel(self):
        for rec in self.filtered(lambda x: x.state != "cancel"):
            raise ValidationError(
                _("Warning to delete the {} document, has to be on a cancelled state").format(rec.name)
            )
        return True

    def unlink(self):
        self.check_is_cancel()
        return super().unlink()

    def action_all_valid(self):
        for rec in self:
            all_valid = True
            if (
                rec.opinion_state in ["pv", "denied"]
                or not rec.opinion_state
                or rec.imss_state in ["pv", "denied"]
                or not rec.imss_state
                or rec.infonavit_state in ["pv", "denied"]
                or not rec.infonavit_state
                or rec.cfiscal1_state in ["pv", "denied"]
                or not rec.cfiscal1_state
            ):
                all_valid = False

            if rec.no_activity:
                if rec.na_state in ["pv", "denied"] or not rec.na_state:
                    all_valid = False

            for line in rec.repse_line_ids:
                if line.worker_state in ["pv", "denied"] or not line.worker_state:
                    all_valid = False

            if not rec.no_activity:
                if (
                    rec.repse_state in ["pv", "denied"]
                    or not rec.repse_state
                    or rec.bim_state in ["pv", "denied"]
                    or not rec.bim_state
                    or rec.sipare_state in ["pv", "denied"]
                    or not rec.sipare_state
                    or rec.settlement_state in ["pv", "denied"]
                    or not rec.settlement_state
                    or rec.sua_state in ["pv", "denied"]
                    or not rec.sua_state
                    or rec.diva_state in ["pv", "denied"]
                    or not rec.diva_state
                    or rec.civa_state in ["pv", "denied"]
                    or not rec.civa_state
                    or rec.disr_state in ["pv", "denied"]
                    or not rec.disr_state
                    or rec.cisr_state in ["pv", "denied"]
                    or not rec.cisr_state
                    or rec.cfdi_state in ["pv", "denied"]
                    or not rec.cfdi_state
                ):
                    all_valid = False

            if rec.quatri:
                if (
                    rec.icsoe_state in ["pv", "denied"]
                    or not rec.icsoe_state
                    or rec.sisub_state in ["pv", "denied"]
                    or not rec.sisub_state
                ):
                    all_valid = False

        return all_valid

    # EXTENDS portal portal.mixin
    def _compute_access_url(self):
        res = super()._compute_access_url()
        for repse in self:
            repse.access_url = "/my/repse/%s" % (repse.id)
        return res

    def _get_repse_portal_extra_values(self):
        self.ensure_one()
        return {
            "repse": self,
        }

    @api.onchange(
        "opinion",
        "imss_compliance",
        "infonavit_compliance",
        "fiscal_constancy1",
        "fiscal_constancy",
        "act_cons",
        "repse_doc",
        "no_activity_file",
        "bim_card",
        "sipare_line",
        "settlement_resume",
        "sua_payment",
        "iva_statement",
        "iva_complement",
        "isr_statement",
        "isr_complement",
        "workers_relationship",
        "cfdi_paysheet",
        "icsoe",
        "sisub",
        "contract",
        "contract_v2",
    )
    def onchange_files(self):
        for rec in self:
            record = self.env['document.repse'].browse(rec.id)
            for field_name, field_value in rec._convert_to_write(rec.read(rec._fields.keys())[0]).items():
                if self.env.context.get('field') == field_name:
                    if field_value:
                        rec.sudo().write(self.env.context.get("document"))
                    else:
                        if self.env.context.get("document"):
                            state_str = str(self.env.context.get("document")).replace("approve", "")
                            state_dict = ast.literal_eval(state_str)
                            rec.sudo().write(state_dict)


    @api.onchange(
        "opinion_state",
        "imss_state",
        "infonavit_state",
        "cfiscal_state",
        "cfiscal1_state",
        "act_state",
        "repse_state",
        "na_state",
        "bim_state",
        "sipare_state",
        "settlement_state",
        "sua_state",
        "civa_state",
        "diva_state",
        "cisr_state",
        "disr_state",
        "worker_state",
        "cfdi_state",
        "icsoe_state",
        "sisub_state",
        "repse_line_ids",
    )
    def onchange_files_state(self):
        for rec in self:
            if not self.env.context.get("file") and self.env.context.get("file") is not None:
                raise ValidationError(_("Warning, you cannot set state value if theres no file to support it"))
            if not self.env.context.get("file") and self.env.context.get("state") == "approve":
                raise ValidationError(_("Warning, you cannot set state to valid if theres no file to support it"))
            if rec.state != "cancel":
                all_valid = rec.action_all_valid()
                state = "process"
                if not bool(rec.missing_documents) and all_valid:
                    state = "positive"

                rec.sudo().update({"state": state})

    def action_view_invoice(self, invoices=False):
        """This function returns an action that display existing vendor bills of
        given purchase order ids. When only one found, show the vendor bill
        immediately.
        """
        if not invoices:
            # Invoice_ids may be filtered depending on the user. To ensure we get all
            # invoices related to the purchase order, we read them in sudo to fill the
            # cache.
            # self.sudo()._read(["invoice_ids"])
            invoices = self.invoice_ids

        result = self.env["ir.actions.act_window"]._for_xml_id("account.action_move_in_invoice_type")
        # choose the view_mode accordingly
        if len(invoices) > 1:
            result["domain"] = [("id", "in", invoices.ids)]
        elif len(invoices) == 1:
            res = self.env.ref("account.view_move_form", False)
            form_view = [(res and res.id or False, "form")]
            if "views" in result:
                result["views"] = form_view + [(state, view) for state, view in result["views"] if view != "form"]
            else:
                result["views"] = form_view
            result["res_id"] = invoices.id
        else:
            result = {"type": "ir.actions.act_window_close"}

        return result

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            sequence_id = self.env.ref("repse_mtnmx.ir_sequence_repse")
            new_number = sequence_id.next_by_id()
            vals.update({"name": new_number})
        return super().create(vals_list)

    def action_generate_auto_repse(self):
        today = date.today()
        partner_repse_ids = self.env["res.users"].search([])
        urepse_ids = partner_repse_ids.filtered(lambda x: x.has_group("repse_mtnmx.group_repse_portal"))
        prepse_ids = []
        for user in urepse_ids:
            prepse_ids.append(user.partner_id)

        for partner_id in prepse_ids:
            year = str(today.year)

            if today.month < 10:
                month = "0" + str(today.month)
            else:
                month = str(today.month)

            last_day = calendar.monthrange(today.year, today.month)
            repse_date_start = year + "-" + month + "-01"
            repse_date_end = year + "-" + month + "-" + str(last_day[1])

            bp_repse_id = (
                self.env["document.repse"]
                .sudo()
                .search(
                    [
                        ("repse_date", ">=", repse_date_start),
                        ("repse_date", "<=", repse_date_end),
                        ("partner_id", "=", partner_id.id),
                    ]
                )
            )
            if not bp_repse_id:
                bp_repse_id = (
                    self.env["document.repse"]
                    .sudo()
                    .create(
                        {
                            "partner_id": partner_id.id,
                            "repse_date": today,
                        }
                    )
                )

    def action_process_upload(self, vals=None, msg=None, partner_id=None):
        self.ensure_one()
        vals_to_valid = vals
        vals_to_valid.pop('name',None)
        if not vals_to_valid:
            return False

        if len(msg) > 0:
            self.sudo().write(vals)
            self.sudo().message_post(
                body=_(msg),
                subject=_("""Repse docs uploaded"""),
                message_type="notification",
                author_id=partner_id.id,
            )

            team_id = self.env.ref("repse_mtnmx.mail_activity_team_repse")
            activity_data = {
                "res_id": self.id,  # ID of the record the activity is linked to
                "res_model_id": self.env["ir.model"]._get_id(
                    self._name
                ),  # The ID of the record the activity is linked to
                "activity_type_id": self.env.ref(
                    "repse_mtnmx.mail_act_repse_review"
                ).id,  # Example: To-Do activity type
                "team_id": team_id.id,
                "summary": _("""{} REPSE # {} """).format(
                    "Review the documents upload by the supplier.", self.name
                ),
                "note": _(msg),
                "date_deadline": date.today() + timedelta(days=3),  # Deadline 3 days from now
                "user_id": team_id.user_id.id,  # Assign to the current user
            }

                # Create the activity
            self.env["mail.activity"].sudo().create(activity_data)

    def action_generate_repse_email(self):
        repse_partner_ids = self.env["res.partner"].sudo().search([("repse_group", "=", True)])
        for rec in repse_partner_ids:
            repse_docs_ids = (
                self.env["document.repse"].sudo().search([("partner_id", "=", rec.id), ("state", "in", ["process"])])
            )
            if repse_docs_ids:
                repse_doc_list = ""
                partners = [rec.id]
                for repse in repse_docs_ids:
                    repse_doc_list += repse.name + " " + repse.state + "\n" + " - " + _(repse.missing_documents)

            rec.sudo().message_post(
                body=_("""Greetings, you have repse docs to upload {}""").format(repse_doc_list),
                subject=_("""Repse documents"""),
                partner_ids=partners,
                subtype_xmlid="mail.mt_comment",
            )

            if date.today().day in [1, 10]:
                missing_repse = ""
                no_repse_ids = self.env["repse.document"].sudo().search([("state", "=", "process")])
                for nrepse in no_repse_ids:
                    missing_repse += nrepse.name + "\n"
                if bool(missing_repse):
                    emails = list({rec.email})
                    subject = "Odoo - Missing REPSE Documents"
                    body = _(
                        """  Greetings, we remind you that you have pending REPSE documentation,
                        which must be submitted on the 8th and 20th of each month.
                        We kindly ask that you send it as soon as possible. {} """
                    ).format(missing_repse)
                    email = self.env["ir.mail_server"].build_email(
                        email_from=self.env.user.email,
                        email_to=emails,
                        subject=subject,
                        body=body,
                    )
                    try:
                        self.env["ir.mail_server"].send_email(email)
                    except Exception as e:
                        logging.info(e)

            return True

    @api.constrains ('repse_line_ids')
    def _check_exist_product_in_line(self):
        for repse in self:
            purchase_order_ids = repse.mapped('repse_line_ids.purchase_order_id')
            for purchase in purchase_order_ids:
                lines_count = len(repse.repse_line_ids.filtered(lambda line: line.purchase_order_id == purchase))
                if lines_count > 1:
                    raise ValidationError(_('Purchase {} already added.'.format(purchase.name)))
        return True


class DocumentRepseLine(models.Model):
    _name = "document.repse.line"
    _inherit = ["portal.mixin", "mail.thread", "mail.activity.mixin"]
    _description = "Purchases"

    name = fields.Char()
    repse_document_id = fields.Many2one("document.repse", string="Repse")
    purchase_order_id = fields.Many2one("purchase.order", string="Purchase order", tracking=True)
    purchase_partner_id = fields.Many2one("res.partner", string="Supplier", related="purchase_order_id.partner_id")
    purchase_date = fields.Datetime(string="Pruchase date", related="purchase_order_id.date_approve")
    workers_relationship = fields.Binary(attachment=True, string="Workers relationship")  #
    workers_name = fields.Char(tracking=True)
    worker_state = fields.Selection(FIELD_STATE, string="Workers State")
    repse_attach = fields.Binary(attachment=True, string="Attach")
    repse_attach_name = fields.Char(tracking=True)
    repse_attach_state = fields.Selection(FIELD_STATE, string="Attach State")

    @api.onchange("workers_relationship", "repse_attach")
    def onchange_files(self):
        for rec in self:
            record = self.env['document.repse.line'].browse(rec.id)
            for field_name, field_value in rec._convert_to_write(rec.read(rec._fields.keys())[0]).items():
                if self.env.context.get('field') == field_name:
                    if field_value:
                        rec.sudo().write(self.env.context.get("document"))
                    else:
                        if self.env.context.get("document"):
                            state_str = str(self.env.context.get("document")).replace("approve", "")
                            state_dict = ast.literal_eval(state_str)
                            rec.sudo().write(state_dict)


class DocumentRepseAttach(models.Model):
    _name = "document.repse.attach"
    _description = "Repse attach"

    name = fields.Char()
