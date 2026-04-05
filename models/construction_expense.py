from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ConstructionExpense(models.Model):
    _name = 'construction.expense'
    _description = 'Expenses'
    _rec_name = 'description'
    _order = 'expense_date desc'

    project_id = fields.Many2one(
        'construction.project',
        string='Project',
        required=True,
    )
    site_id = fields.Many2one(
        'construction.site',
        string='Site',
        domain="[('project_id','=',project_id)]"
    )

    task_id = fields.Many2one(
        'construction.task',
        string='Task',
        domain="[('project_id','=',project_id)]"

    )

    description = fields.Char(string='Description', required=True)
    expense_date = fields.Date(string='Expense Date', default=fields.Date.context_today, required=True)
    amount = fields.Float(string='Amount', required=True)
    expense_type = fields.Selection([
        ('material', 'Material'),
        ('labor', 'Labor'),
        ('transport', 'Transport'),
        ('equipment', 'Equipment'),
        ('misc', 'Miscellaneous')
    ],
        string='Expense Type',
        default='misc'
    )
    note = fields.Text(string="Notes")
