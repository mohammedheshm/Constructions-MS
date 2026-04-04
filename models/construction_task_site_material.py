from odoo import fields, models, api


class ConstructionTaskSiteMaterial(models.Model):
    _name = 'construction.task.site.material'
    _description = 'Materials per Task per Site'

    task_id = fields.Many2one('construction.task', string='Task')
    site_id = fields.Many2one('construction.site', string='Site')
    material_id = fields.Many2one('construction.site.material', string='Material')
