# -*- coding: utf-8 -*-
import io
import base64
from odoo import fields, models


class VolontariatoInterventoReportWizard(models.TransientModel):
    _name = 'volontariato.intervento.report.wizard'
    _description = 'Wizard Report Interventi per Periodo'

    data_da = fields.Date(string='Data Da', required=True)
    data_a = fields.Date(string='Data A', required=True)

    file_xlsx = fields.Binary(string='File Excel', readonly=True)
    file_xlsx_name = fields.Char(string='Nome File', readonly=True)
    stato = fields.Selection(
        [('input', 'Input'), ('done', 'Fatto')],
        default='input',
    )

    def _get_interventi(self):
        domain = [
            ('data', '>=', self.data_da),
            ('data', '<=', self.data_a),
        ]
        return self.env['volontariato.intervento'].search(domain, order='data, ora_inizio')

    def action_print_pdf(self):
        interventi = self._get_interventi()
        return self.env.ref(
            'gestione_ass_volontariato.action_report_elenco_interventi'
        ).report_action(interventi.ids)

    def action_generate_xlsx(self):
        import xlsxwriter

        interventi = self._get_interventi()
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Interventi')

        title_fmt = workbook.add_format({'bold': True, 'font_size': 14})
        header_fmt = workbook.add_format({
            'bold': True, 'bg_color': '#2C3E50', 'font_color': 'white',
            'border': 1, 'align': 'center',
        })
        cell_fmt = workbook.add_format({'border': 1})
        date_fmt = workbook.add_format({'border': 1, 'num_format': 'dd/mm/yyyy'})

        sheet.write(0, 0, self.env.company.name, title_fmt)

        headers = ['Codice', 'Data', 'Automezzo', 'Tipo', 'Richiedente',
                   'Luogo', 'Km Totali', 'Stato']
        header_row = 2
        for col, h in enumerate(headers):
            sheet.write(header_row, col, h, header_fmt)

        row = header_row + 1
        for intervento in interventi:
            sheet.write(row, 0, intervento.codice, cell_fmt)
            if intervento.data:
                sheet.write_datetime(row, 1, fields.Datetime.from_string(str(intervento.data)), date_fmt)
            else:
                sheet.write(row, 1, '', cell_fmt)
            sheet.write(row, 2, intervento.vehicle_id.display_name or '', cell_fmt)
            sheet.write(row, 3, intervento.tipo_intervento_id.name or '', cell_fmt)
            sheet.write(row, 4, intervento.richiedente_id.display_name or '', cell_fmt)
            sheet.write(row, 5, intervento.luogo or '', cell_fmt)
            sheet.write(row, 6, intervento.km_totali or 0, cell_fmt)
            sheet.write(row, 7, dict(intervento._fields['state'].selection)[intervento.state], cell_fmt)
            row += 1

        sheet.set_column(0, 0, 12)
        sheet.set_column(1, 1, 12)
        sheet.set_column(2, 4, 24)
        sheet.set_column(5, 5, 22)
        sheet.set_column(6, 7, 12)

        workbook.close()
        output.seek(0)

        self.write({
            'file_xlsx': base64.b64encode(output.read()),
            'file_xlsx_name': 'interventi_%s_%s.xlsx' % (self.data_da, self.data_a),
            'stato': 'done',
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'volontariato.intervento.report.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
