from odoo import fields, api, models
from odoo.exceptions import ValidationError


class ConstructionTask(models.Model):
    _name = 'construction.task'
    _description = 'Project Tasks'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Task Name', required=True, tracking=True)
    description = fields.Text(string='Description')
    start_date = fields.Date(string='Start Date', tracking=True)
    end_date = fields.Date(string='End Date', tracking=True)
    progress = fields.Float(string='Progress %', compute='_compute_progress', store=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'), ], tracking=True)

    project_id = fields.Many2one(
        'construction.project',
        string='Project',
        required=True,
    )
    site_ids = fields.Many2many(
        'construction.site',
        string='Site',
        domain="[('project_id','=',project_id)]",

    )

    site_material_line_display = fields.One2many(
        'construction.task.site.material',
        'task_id',
        string='Materials per Site',
        readonly=True,
    )

    total_material_cost = fields.Float(
        string='Total Material Cost',
        compute='_compute_total_material_cost',
        store=False,
    )

    assigned_workforce_ids = fields.Many2many(
        'construction.workforce',
        string='Assigned Workforce',
    )

    @api.depends('project_id', 'project_id.site_ids.material_ids.total_price')
    def _compute_total_material_cost(self):
        for rec in self:
            total = sum(
                mat.total_price
                for site in rec.project_id.site_ids
                for mat in site.material_ids
            )
            rec.total_material_cost = total

    @api.depends('state')
    def _compute_progress(self):
        for rec in self:
            if rec.state == 'draft':
                rec.progress = 0
            elif rec.state == 'in_progress':
                rec.progress = 50
            elif rec.state == 'done':
                rec.progress = 100
            else:
                rec.progress = 0

    @api.onchange('site_ids')
    def _onchange_site_ids(self):
        if self.site_ids:
            domain_workers = self.env['construction.workforce'].search([('site_ids', 'in', self.site_ids.ids)])
            self.assigned_workforce_ids = [(6, 0, [])]
            return {
                'domain': {
                    'assigned_workforce_ids': [('id', 'in', domain_workers.ids)]
                }
            }
        else:
            self.assigned_workforce_ids = [(6, 0, [])]
            return {
                'domain': {
                    'assigned_workforce_ids': [('id', 'in', [])]
                }
            }

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for rec in self:
            if rec.start_date and rec.end_date and rec.end_date < rec.start_date:
                raise ValidationError("End Date cannot be before Start Date.")

    def _populate_site_materials(self):
        task_material = self.env['construction.task.site.material']
        for rec in self:
            old_materials = task_material.search([('task_id', '=', rec.id)])
            if old_materials:
                old_materials.unlink()
            for site in rec.site_ids:
                for mat in site.material_ids or []:
                    task_material.create({
                        'task_id': rec.id,
                        'site_id': site.id,
                        'material_id': mat.id,
                    })

    def create(self, vals):
        task = super().create(vals)
        task._populate_site_materials()
        return task

    def write(self, vals):
        res = super().write(vals)
        if 'project_id' in vals or 'site_ids' in vals:
            self._populate_site_materials()
        return res

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_in_progress(self):
        self.write({'state': 'in_progress'})

    def action_done(self):
        self.write({'state': 'done'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})
