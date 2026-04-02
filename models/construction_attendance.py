from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ConstructionAttendance(models.Model):
    _name = 'construction.attendance'
    _description = "Workforce Attendance"
    _rec_name = "workforce_id"

    workforce_id = fields.Many2one(
        'construction.workforce',
        string="Worker",
        required=True)

    site_ids = fields.Many2many(
        'construction.site',
        string='Sites',
        compute='_compute_sites'
    )

    project_id = fields.Many2one(
        'construction.project',
        string="Project",
        related='site_ids.project_id',
        store=True,
    )

    date = fields.Date(
        string="Date",
        required=True,
        default=fields.Date.context_today
    )

    status = fields.Selection([
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('half_day', 'Half Day')
    ], string='Status', default='present')

    check_in = fields.Datetime(string="Check In", required=True)
    check_out = fields.Datetime(string="Check Out")
    duration = fields.Float(string="Duration (Hours)", compute="_compute_duration")
    notes = fields.Text(string="Notes")
    active = fields.Boolean(default=True)

    check_in_ampm = fields.Char(
        string="Check In (AM/PM)",
        compute="_compute_ampm",
        readonly=True,
        store=False
    )
    check_out_ampm = fields.Char(
        string="Check Out (AM/PM)",
        compute="_compute_ampm",
        readonly=True,
        store=False
    )

    is_paid = fields.Boolean(string="Paid", default=False, readonly=True)

    @api.depends('check_in', 'check_out')
    def _compute_duration(self):
        for rec in self:
            if rec.check_in and rec.check_out:
                delta = rec.check_out - rec.check_in
                rec.duration = delta.total_seconds() / 3600.0
            else:
                rec.duration = 0

    @api.constrains('check_in', 'check_out')
    def _check_times(self):
        for rec in self:
            if rec.check_out and rec.check_in > rec.check_out:
                raise ValidationError('Check Out must be after Check In!')

    @api.depends('workforce_id')
    def _compute_sites(self):
        for rec in self:
            if rec.workforce_id:
                rec.site_ids = rec.workforce_id.site_ids
            else:
                rec.site_ids = self.env['construction.site'].browse([])

    @api.constrains('workforce_id', 'date', 'site_ids')
    def _check_duplicate_attendance(self):
        for rec in self:
            if not rec.workforce_id or not rec.date or not rec.site_ids:
                continue
            existing = self.search([
                ('id', '!=', rec.id),
                ('workforce_id', '=', rec.workforce_id.id),
                ('date', '=', rec.date),
                ('site_ids', 'in', rec.site_ids.ids),
            ])
            if existing:
                raise ValidationError(
                    'Attendance already exists for this worker at one of these sites on this date!'
                )

    @api.depends('check_in', 'check_out')
    def _compute_ampm(self):
        for rec in self:
            rec.check_in_ampm = rec.check_in.strftime("%I:%M %p") if rec.check_in else ''
            rec.check_out_ampm = rec.check_out.strftime("%I:%M %p") if rec.check_out else ''
