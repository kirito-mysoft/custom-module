from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)

class LeadController(http.Controller):
    @http.route('/create/lead', type='json', auth='public', methods=['POST'], csrf=False)
    def create_lead(self, **kwargs):
        _logger.info("Request received")

        # Manually parsing the json data because jsonplayload is not working in odoo - jihad
        try:
            data = json.loads(request.httprequest.data)
            _logger.info(f"Parsed data: {data}")

            # Extract data from the parsed JSON
            name = data.get('name')
            email = data.get('email')
            phone = data.get('phone')
            description = data.get('description')
            stage_name = data.get('stage')
            customer_data = data.get('customer')

            # Ensure all required fields are provided
            if not all([name, email, phone, description, stage_name, customer_data]):
                _logger.warning("Missing required fields")
                return json.dumps({'error': 'Missing required fields'})

            # Find the stage ID based on the stage name
            stage = request.env['crm.stage'].sudo().search([('name', '=', stage_name)], limit=1)
            if not stage:
                _logger.warning(f"Stage '{stage_name}' not found")
                return json.dumps({'error': f"Stage '{stage_name}' not found"})

            # Check if customer exists
            customer = request.env['res.partner'].sudo().search([('name', '=', customer_data['name'])], limit=1)
            if not customer:
                # Create a new customer if it doesn't exist
                customer = request.env['res.partner'].sudo().create({
                    'name': customer_data['name'],
                    'email': email,
                    'phone': phone,
                })

            # Create the lead
            lead = request.env['crm.lead'].sudo().create({
                'name': name,
                'contact_name': name,
                'email_from': email,
                'phone': phone,
                'description': description,
                'stage_id': stage.id,  # Assign the stage ID
                'partner_id': customer.id,  # Link the customer
            })

            return json.dumps({'id': lead.id, 'name': lead.name})
        except Exception as e:
            _logger.error(f"Error creating lead: {str(e)}")
            return json.dumps({'error': 'Failed to create lead'})
