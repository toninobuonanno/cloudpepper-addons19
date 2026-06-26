# -*- coding: utf-8 -*-
import io
import base64
from odoo import api, fields, models


class VolontariatoTurnoReportWizard(models.TransientModel):
    _name = 'volontariato.turno.report.wizard'
    _description = 'Wizard Report Turni per Periodo'

    data_da = fields.Date(string='Data Da', required=True)
    data_a = fields.Date(string='Data A', required=True)

    file_xlsx = fields.Binary(string='File Excel', readonly=True)
    file_xlsx_name = fields.Char(string='Nome File', readonly=True)
    stato = fields.Selection(
        [('input', 'Input'), ('done', 'Fatto')],
        default='input',
    )

    def _get_turni(self):
        domain = [
            ('data', '>=', self.data_da),
            ('data', '<=', self.data_a),
        ]
        return self.env['volontariato.turno'].search(domain, order='data, ora_inizio')

    def action_print_pdf(self):
        turni = self._get_turni()
        return self.env.ref(
            'gestione_ass_volontariato.action_report_turni_periodo'
        ).report_action(turni.ids)

    def action_generate_xlsx(self):
        import xlsxwriter

        turni = self._get_turni()
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Turni')

        header_fmt = workbook.add_format({
            'bold': True, 'bg_color': '#2C3E50', 'font_color': 'white',
            'border': 1, 'align': 'center',
        })
        cell_fmt = workbook.add_format({'border': 1})
        date_fmt = workbook.add_format({'border': 1, 'num_format': 'dd/mm/yyyy'})

        headers = ['Codice', 'Data', 'Evento', 'Luogo', 'Ora Inizio', 'Ora Fine',
                   'Ruolo', 'Volontario', 'Qualifica']
        for col, h in enumerate(headers):
            sheet.write(0, col, h, header_fmt)

        row = 1
        for turno in turni:
            righe = turno.squadra_ids or [None]
            for riga in righe:
                sheet.write(row, 0, turno.codice, cell_fmt)
                if turno.data:
                    sheet.write_datetime(row, 1, fields.Datetime.from_string(str(turno.data)), date_fmt)
                else:
                    sheet.write(row, 1, '', cell_fmt)
                sheet.write(row, 2, turno.evento or '', cell_fmt)
                sheet.write(row, 3, turno.luogo or '', cell_fmt)
                sheet.write(row, 4, '%02d:%02d' % (int(turno.ora_inizio), int((turno.ora_inizio % 1) * 60)), cell_fmt)
                sheet.write(row, 5, '%02d:%02d' % (int(turno.ora_fine), int((turno.ora_fine % 1) * 60)) if turno.ora_fine else '', cell_fmt)
                if riga:
                    sheet.write(row, 6, riga.ruolo_id.name or '', cell_fmt)
                    sheet.write(row, 7, riga.employee_id.name or '', cell_fmt)
                    sheet.write(row, 8, riga.qualifica_id.name or '', cell_fmt)
                else:
                    sheet.write(row, 6, '', cell_fmt)
                    sheet.write(row, 7, 'Nessun volontario assegnato', cell_fmt)
                    sheet.write(row, 8, '', cell_fmt)
                row += 1

        sheet.set_column(0, 0, 12)
        sheet.set_column(1, 1, 12)
        sheet.set_column(2, 3, 22)
        sheet.set_column(4, 5, 10)
        sheet.set_column(6, 8, 18)

        workbook.close()
        output.seek(0)

        self.write({
            'file_xlsx': base64.b64encode(output.read()),
            'file_xlsx_name': 'turni_%s_%s.xlsx' % (self.data_da, self.data_a),
            'stato': 'done',
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'volontariato.turno.report.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
