from odoo import api, fields, models, exceptions
from odoo.exceptions import ValidationError


class ConstructionProject(models.Model):
    _name = 'construction.project'
    _description = 'Projects'
    _rec_name = 'project_name'

    site_ids = fields.One2many('construction.site', 'project_id', string='Sites')
    project_name = fields.Char(string='Project Name', required=True)
    project_code = fields.Char(default='New', string='Project Code', readonly=True)
    customer = fields.Char(string='Customer')
    project_manager = fields.Many2one('res.users', string='Project Manager')
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    budget = fields.Float(string='Budget')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('closed', 'Closed'),
    ], string='State', default='draft', required=True)
    description = fields.Text(string='Description', required=True)

    def action_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_in_progress(self):
        for rec in self:
            rec.state = 'in_progress'

    def action_done(self):
        for rec in self:
            if rec.state != 'done':
                rec.state = 'done'

    def action_close(self):
        for rec in self:
            rec.state = 'closed'

    @api.model
    def create(self, vals):
        if vals.get('project_code', 'New') == 'New':
            vals['project_code'] = self.env['ir.sequence'].next_by_code('Project_seq') or 'New'
        return super(ConstructionProject, self).create(vals)

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for rec in self:
            if rec.end_date < rec.start_date:
                raise ValidationError('End Date must be after Start Date!')
