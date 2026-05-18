from odoo import api, fields, models


class OEHealthPatient(models.Model):
    _name = "oehealth.patient"
    _description = "Patient"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "display_name"

    name = fields.Char(required=True, tracking=True)
    patient_code = fields.Char(default="New", readonly=True, copy=False, index=True)
    display_name = fields.Char(compute="_compute_display_name", store=True)
    active = fields.Boolean(default=True)
    photo = fields.Image()
    birth_date = fields.Date(tracking=True)
    gender = fields.Selection([("male", "Male"), ("female", "Female"), ("other", "Other")], tracking=True)
    blood_group = fields.Selection([("a+", "A+"), ("a-", "A-"), ("b+", "B+"), ("b-", "B-"), ("ab+", "AB+"), ("ab-", "AB-"), ("o+", "O+"), ("o-", "O-")])
    partner_id = fields.Many2one("res.partner", string="Related Contact")
    family_group_id = fields.Many2one("oehealth.family.group", string="Family Group")
    allergy_notes = fields.Text()
    alert_flag = fields.Boolean()
    medical_history = fields.Html()
    vaccination_ids = fields.One2many("oehealth.vaccination", "patient_id")
    appointment_ids = fields.One2many("oehealth.appointment", "patient_id")
    visit_timeline_note = fields.Html()

    @api.depends("name", "patient_code")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"[{rec.patient_code}] {rec.name}" if rec.patient_code and rec.patient_code != "New" else rec.name

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("patient_code", "New") == "New":
                vals["patient_code"] = seq.next_by_code("oehealth.patient") or "New"
        return super().create(vals_list)


class OEHealthFamilyGroup(models.Model):
    _name = "oehealth.family.group"
    _description = "Family Health Group"

    name = fields.Char(required=True)
    member_ids = fields.One2many("oehealth.patient", "family_group_id")


class OEHealthVaccination(models.Model):
    _name = "oehealth.vaccination"
    _description = "Vaccination Tracking"

    patient_id = fields.Many2one("oehealth.patient", required=True, ondelete="cascade")
    vaccine_name = fields.Char(required=True)
    dose = fields.Char()
    administered_on = fields.Date()
    next_due_on = fields.Date()


class OEHealthAppointment(models.Model):
    _name = "oehealth.appointment"
    _description = "Appointment & Rapid Consultation"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(default="New", readonly=True, copy=False)
    patient_id = fields.Many2one("oehealth.patient", required=True, tracking=True)
    doctor_id = fields.Many2one("res.users", required=True, tracking=True)
    appointment_datetime = fields.Datetime(required=True, tracking=True)
    state = fields.Selection([("draft", "Draft"), ("confirmed", "Confirmed"), ("in_consult", "In Consultation"), ("done", "Done"), ("cancel", "Cancelled")], default="draft", tracking=True)
    chief_complaint = fields.Text()
    follow_up_date = fields.Date()
    queue_number = fields.Integer()


class OEHealthClinicalRecord(models.Model):
    _name = "oehealth.clinical.record"
    _description = "Clinical Evaluation"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(default="New", readonly=True, copy=False)
    patient_id = fields.Many2one("oehealth.patient", required=True)
    appointment_id = fields.Many2one("oehealth.appointment")
    diagnosis_icd10 = fields.Char()
    diagnosis_icd11 = fields.Char()
    treatment_plan = fields.Html()
    prescription_note = fields.Html()
    procedure_note = fields.Html()
    consent_form_ref = fields.Char(help="External digital consent reference")


class OEHealthOperation(models.Model):
    _name = "oehealth.operation"
    _description = "Surgery / OT"

    name = fields.Char(required=True)
    patient_id = fields.Many2one("oehealth.patient", required=True)
    surgeon_id = fields.Many2one("res.users")
    schedule_start = fields.Datetime()
    schedule_end = fields.Datetime()
    asa_score = fields.Selection([(str(i), str(i)) for i in range(1, 7)], string="ASA")
    mallampati = fields.Selection([("i", "I"), ("ii", "II"), ("iii", "III"), ("iv", "IV")])
    rcri = fields.Integer(string="RCRI")
    anesthesia_record = fields.Html()
    team_note = fields.Text()
    supplies_note = fields.Text()


class OEHealthBed(models.Model):
    _name = "oehealth.bed"
    _description = "Hospital Bed"

    name = fields.Char(required=True)
    ward = fields.Char()
    building = fields.Char()
    campus = fields.Char()
    occupied = fields.Boolean()


class OEHealthAdmission(models.Model):
    _name = "oehealth.admission"
    _description = "IPD Admission / Discharge"

    name = fields.Char(default="New", readonly=True, copy=False)
    patient_id = fields.Many2one("oehealth.patient", required=True)
    bed_id = fields.Many2one("oehealth.bed")
    admitted_on = fields.Datetime(default=fields.Datetime.now)
    discharged_on = fields.Datetime()
    triage_note = fields.Text()
    apache_ii = fields.Float()
    sofa = fields.Float()
    nursing_plan = fields.Html()


class OEHealthBilling(models.Model):
    _name = "oehealth.billing"
    _description = "Billing & Insurance"

    name = fields.Char(default="New", readonly=True, copy=False)
    patient_id = fields.Many2one("oehealth.patient", required=True)
    amount_total = fields.Monetary(currency_field="currency_id")
    currency_id = fields.Many2one("res.currency", default=lambda s: s.env.company.currency_id.id)
    insurance_provider = fields.Char()
    pre_auth_code = fields.Char()
    claim_reference = fields.Char()
    edi_837p_reference = fields.Char()
    hcfa_1500_reference = fields.Char()
    state = fields.Selection([("draft", "Draft"), ("submitted", "Submitted"), ("paid", "Paid"), ("rejected", "Rejected")], default="draft")


class OEHealthKPI(models.Model):
    _name = "oehealth.kpi"
    _description = "Healthcare KPI"

    name = fields.Char(required=True)
    value = fields.Float()
    as_of = fields.Date(default=fields.Date.today)
    note = fields.Text()
