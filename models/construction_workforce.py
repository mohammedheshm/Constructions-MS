from odoo import fields, models, api
from odoo.exceptions import ValidationError


class ConstructionWorkforce(models.Model):
    _name = 'construction.workforce'
    _description = 'Workforce'
    _rec_name = 'workforce_name'

    workforce_name = fields.Char(string='Name', required=True)
    workforce_code = fields.Char(string='Code', readonly=True, default='New')
    worker_type = fields.Selection([
        ('worker', 'Worker'),
        ('engineer', 'Engineer'),
        ('contractor', 'Contractor'),
        ('supervisor', 'Supervisor'),
    ], string='Worker Type', required=True)

    job_title = fields.Selection([
        ('carpenter', 'Carpenter'),
        ('electrician', 'Electrician'),
        ('plumber', 'Plumber'),
        ('painter', 'Painter'),
        ('blacksmith', 'Blacksmith'),
        ('civil_engiworkforce_seqneer', 'Civil Engineer'),
        ('architect', 'Architect'),
    ], string='Job Title')

    salary_type = fields.Selection([
        ('daily', 'Daily'),
        ('monthly', 'Monthly'),
    ], string='Salary Type')

    salary = fields.Float(string='Salary')
    phone = fields.Char(string='Phone')
    email = fields.Char(string='Email')
    hire_date = fields.Date(string='Hire Date')
    active = fields.Boolean(string='Active', default=True)
    notes = fields.Text(string='Notes')
    site_ids = fields.Many2many('construction.site', string='Sites')

    @api.model
    def create(self, vals):
        if vals.get('workforce_code', 'New') == 'New':
            vals['workforce_code'] = self.env['ir.sequence'].next_by_code('workforce_seq') or 'New'
        return super(ConstructionWorkforce, self).create(vals)

    @api.constrains('salary')
    def _check_salary(self):
        for rec in self:
            if rec.salary < 0:
                raise ValidationError('Salary must be positive!')

    @api.constrains('hire_date')
    def _check_hire_date(self):
        for rec in self:
            if rec.hire_date > fields.Date.today():
                raise ValidationError('Hire Date cannot be in the future!')
