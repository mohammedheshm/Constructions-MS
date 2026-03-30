from odoo import fields, models, api
from odoo.exceptions import ValidationError


class ConstructionWorkforce(models.Model):
    _name = 'construction.workforce'
    _description = 'Workforce'
    _rec_name = 'workforce_name'
    _order = "worker_type, workforce_name"

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
        ('civil_engineer', 'Civil Engineer'),
        ('architect', 'Architect'),
    ], string='Job Title')
    salary_type = fields.Selection([
        ('daily', 'Daily'),
        ('monthly', 'Monthly'),
    ], string='Salary Type')
    salary = fields.Float(string='Salary', required=True)
    salary_display = fields.Char(string='Salary Display', compute='_compute_salary_display', readonly=True)
    daily_cost = fields.Float(string='Daily Cost', compute='_compute_daily_cost', readonly=True)
    phone = fields.Char(string='Phone')
    email = fields.Char(string='Email')
    hire_date = fields.Date(string='Hire Date', required=True)
    active = fields.Boolean(string='Active', default=True)
    notes = fields.Text(string='Notes')
    site_ids = fields.Many2many('construction.site', string='Sites')
    project_ids = fields.Many2many(
        'construction.project',
        string='Projects',
        compute='_compute_projects',
        readonly=True,
    )
    site_count = fields.Integer(string='Site Count', compute='_compute_site_count', readonly=True)
    availability = fields.Selection([
        ('available', 'Available'),
        ('assigned', 'Assigned'),
    ], string='Availability', compute='_compute_availability', store=True, readonly=True)

    _sql_constraints = [
        ('unique_workforce_code',
         'unique (workforce_code)',
         'Workforce Code must be unique!'
         )
    ]

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
            if rec.hire_date and rec.hire_date > fields.Date.today():
                raise ValidationError('Hire Date cannot be in the future!')

    @api.depends('site_ids')
    def _compute_site_count(self):
        for rec in self:
            rec.site_count = len(rec.site_ids)

    @api.depends('site_ids')
    def _compute_availability(self):
        for rec in self:
            if rec.site_ids:
                rec.availability = 'assigned'
            else:
                rec.availability = 'available'

    @api.depends('salary', 'salary_type')
    def _compute_salary_display(self):
        for rec in self:
            if rec.salary_type == 'daily':
                rec.salary_display = f"{rec.salary} / Day"
            elif rec.salary_type == 'monthly':
                rec.salary_display = f"{rec.salary} / Month"
            else:
                rec.salary_display = ""

    @api.depends('salary', 'salary_type')
    def _compute_daily_cost(self):
        for rec in self:
            if rec.salary_type == 'daily':
                rec.daily_cost = rec.salary
            elif rec.salary_type == 'monthly':
                rec.daily_cost = rec.salary / 30
            else:
                rec.daily_cost = 0

    @api.depends('site_ids.project_id')
    def _compute_projects(self):
        for rec in self:
            projects = rec.site_ids.mapped('project_id')
            rec.project_ids = projects
