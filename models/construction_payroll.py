from odoo import fields, models, api
from odoo.exceptions import ValidationError


class ConstructionPayroll(models.Model):
    _name = 'construction.payroll'
    _description = 'Payroll'

    workforce_id = fields.Many2one(
        'construction.workforce',
        string='Worker',
        required=True,
    )

    hire_date = fields.Date(
        string='Hire Date',
        related='workforce_id.hire_date',
        readonly=True
    )

    last_attendance_date = fields.Date(
        string='Last Attendance',
        compute='_compute_last_attendance',
        store=True,
    )

    attendance_ids = fields.Many2many(
        'construction.attendance',
        string='Attendance Records',
        compute='_compute_attendance',
    )

    total_hours = fields.Float(
        string='Total Hours',
        compute='_compute_total_hours',
        store=True
    )

    total_salary = fields.Float(
        string='Total Salary',
        compute='_compute_total_salary',
        store=True
    )

    is_paid = fields.Boolean(string="Paid", default=False)

    @api.depends('workforce_id')
    def _compute_attendance(self):
        for rec in self:
            if rec.workforce_id:
                rec.attendance_ids = self.env['construction.attendance'].search([
                    ('workforce_id', '=', rec.workforce_id.id),
                    ('date', '>=', rec.workforce_id.hire_date),
                    ('date', '<=', rec.last_attendance_date),
                    ('is_paid', '=', False),
                ])
            else:
                rec.attendance_ids = self.env['construction.attendance']

    @api.depends('workforce_id')
    def _compute_last_attendance(self):
        for rec in self:
            if rec.workforce_id:
                last_attendance = self.env['construction.attendance'].search([
                    ('workforce_id', '=', rec.workforce_id.id),
                ], order='date desc', limit=1)
                rec.last_attendance_date = last_attendance.date if last_attendance else rec.workforce_id.hire_date

    @api.depends('workforce_id', 'attendance_ids')
    def _compute_total_salary(self):
        for rec in self:
            if not rec.workforce_id:
                rec.total_salary = 0
                rec.total_hours = 0
                continue

            if rec.workforce_id.salary_type == 'daily':
                hourly_rate = rec.workforce_id.salary / 8
                hours_per_day = {}
                for att in rec.attendance_ids:
                    day = att.date
                    hours_per_day[day] = hours_per_day.get(day, 0) + att.duration
                total_hours = sum(hours_per_day.values())
                rec.total_hours = total_hours
                rec.total_salary = total_hours * hourly_rate

            elif rec.workforce_id.salary_type == 'monthly':
                monthly_hours = 30 * 8
                rec.total_hours = sum(att.duration for att in rec.attendance_ids)
                rec.total_salary = (rec.total_hours / monthly_hours) * rec.workforce_id.salary
            else:
                rec.total_salary = 0
                rec.total_hours = 0

    @api.depends('attendance_ids')
    def _compute_total_hours(self):
        for rec in self:
            rec.total_hours = sum(rec.attendance_ids.mapped('duration'))

    def create(self, vals):
        rec = super().create(vals)
        if vals.get('is_paid'):
            if rec.attendance_ids:
                rec.attendance_ids.write({
                    'is_paid': True
                })
        return rec

    def write(self, vals):
        res = super().write(vals)
        if vals.get('is_paid'):
            for rec in self:
                if rec.attendance_ids:
                    rec.attendance_ids.write({
                        'is_paid': True
                    })
        return res
